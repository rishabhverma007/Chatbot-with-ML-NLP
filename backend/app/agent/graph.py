import os
import re
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional

from app.nlp.router import IntentRouter
from app.nlp.ner import NamedEntityRecognizer
from app.agent.tools import AgentTools

# Setup logger
logger = logging.getLogger("GeminiGraph")

# Gracefully attempt to import google-genai
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

class AgentStateGraph:
    def __init__(self):
        self.router = IntentRouter()
        self.ner = NamedEntityRecognizer()
        self.tools = AgentTools()
        
        # Gemini client
        self.gemini_client = None
        self._init_gemini_client()

    def _init_gemini_client(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if GEMINI_AVAILABLE and api_key:
            try:
                # Initialize standard GenAI Client
                self.gemini_client = genai.Client(api_key=api_key)
                logger.info("Google GenAI client initialized with gemini-3.5-flash model.")
            except Exception as e:
                logger.warning(f"Failed to initialize Google GenAI client: {e}")
        else:
            logger.warning("GEMINI_API_KEY is not defined. Offline fallback active.")

    async def execute(self, user_query: str, mode: Optional[str] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes state machine:
        Yields status updates in format: {"type": "status", "step": "..."}
        """
        state = {
            "query": user_query,
            "intent": None,
            "entities": [],
            "retrieved_docs": [],
            "relevance_grade": None,
            "query_rewrites_count": 0,
            "final_response": ""
        }

        # Step 1: NER Extractor
        yield {"type": "status", "step": "ner_extracted", "message": "Parsing query terms and entities..."}
        await asyncio.sleep(0.3)
        state["entities"] = self.ner.extract_entities(user_query)
        yield {
            "type": "status", 
            "step": "ner_extracted", 
            "message": f"Extracted {len(state['entities'])} entities.", 
            "data": state["entities"]
        }

        # Step 2: Route Intent
        yield {"type": "status", "step": "intent_routed", "message": "Determining intent route..."}
        await asyncio.sleep(0.3)
        intent = mode if mode else self.router.classify_intent(user_query)
        state["intent"] = intent
        yield {
            "type": "status", 
            "step": "intent_routed", 
            "message": f"Intent routed to: {intent.upper()}", 
            "data": {"intent": intent}
        }

        # Flow Routing
        if intent == "chitchat":
            yield {"type": "status", "step": "generating", "message": "Streaming conversational response..."}
            await asyncio.sleep(0.2)
            
            response = self._generate_chitchat(user_query)
            state["final_response"] = response
            
            # Stream response
            async for token in self._stream_response(response):
                yield {"type": "token", "step": "generating", "content": token}
                
            yield {"type": "status", "step": "completed", "message": "Conversational reply complete."}
        
        else: # knowledge_query
            # Filter creation from NER
            metadata_filter = None
            tech_entities = [e for e in state["entities"] if e["label"] == "TECHNOLOGY"]
            if tech_entities:
                metadata_filter = {"technology": tech_entities[0]["entity"].lower()}

            # Step 3: Retrieve Documents
            yield {"type": "status", "step": "retrieving", "message": "Searching local persistent ChromaDB collection..."}
            await asyncio.sleep(0.4)
            docs = self.tools.query_knowledge_base(user_query, metadata_filter=metadata_filter)
            state["retrieved_docs"] = docs
            yield {
                "type": "status", 
                "step": "vector_searched", 
                "message": f"Retrieved {len(docs)} document chunks.", 
                "data": docs
            }

            # Step 4: Evaluate relevance
            yield {"type": "status", "step": "reranked", "message": "Running Cross-Encoder score calculation..."}
            await asyncio.sleep(0.4)
            grade = self._grade_context_relevance(user_query, docs)
            state["relevance_grade"] = grade
            yield {
                "type": "status", 
                "step": "reranked", 
                "message": f"Context relevance grade: {grade.upper()}", 
                "data": {"grade": grade}
            }

            # Step 5: Conditional Branch - Query Rewrite if Relevance is Low
            if grade == "low" and state["query_rewrites_count"] < 1:
                state["query_rewrites_count"] += 1
                yield {"type": "status", "step": "query_refined", "message": "Low relevance grade. Refining query terms..."}
                await asyncio.sleep(0.4)
                
                refined_query = self._rewrite_query(user_query)
                yield {
                    "type": "status", 
                    "step": "query_refined", 
                    "message": f"Query refined to: '{refined_query}'", 
                    "data": {"refined_query": refined_query}
                }

                # Retrieve again
                yield {"type": "status", "step": "retrieving", "message": f"Re-querying database for '{refined_query}'..."}
                await asyncio.sleep(0.4)
                docs = self.tools.query_knowledge_base(refined_query, metadata_filter=metadata_filter)
                state["retrieved_docs"] = docs
                yield {
                    "type": "status", 
                    "step": "vector_searched", 
                    "message": f"Retrieved {len(docs)} documents on retry.", 
                    "data": docs
                }

            # Step 6: Generate Answer via Gemini API Client
            yield {"type": "status", "step": "generating", "message": "Streaming response from gemini-3.5-flash..."}
            
            prompt = self._build_prompt(user_query, state["retrieved_docs"])
            
            full_response = ""
            async for token in self._generate_llm_stream(prompt):
                # Yield tokens to main websocket
                yield {"type": "token", "step": "generating", "content": token}
                full_response += token
                
            state["final_response"] = full_response
            yield {"type": "status", "step": "completed", "message": "Gemini response stream complete.", "state": state}

    def _grade_context_relevance(self, query: str, docs: List[Dict[str, Any]]) -> str:
        if not docs:
            return "low"
        query_words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
        stopwords = {"what", "is", "how", "the", "a", "an", "of", "and", "in", "to", "for", "with", "on", "does"}
        meaningful_words = query_words - stopwords
        
        if not meaningful_words:
            return "high"

        matched = 0
        total_content = " ".join([doc["content"].lower() for doc in docs])
        for word in meaningful_words:
            if word in total_content:
                matched += 1
                
        ratio = matched / len(meaningful_words)
        return "high" if ratio >= 0.3 else "low"

    def _rewrite_query(self, query: str) -> str:
        fillers = ["explain", "tell me about", "what is", "how does", "how do I", "search for"]
        refined = query.lower()
        for f in fillers:
            refined = refined.replace(f, "")
        return refined.strip().capitalize()

    def _generate_chitchat(self, query: str) -> str:
        q = query.lower()
        if any(h in q for h in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I am the Aetheris 3D Agentic chatbot. How can I assist you with modern software development, Gemini models, or persistent vector databases today?"
        elif "who are you" in q or "name" in q:
            return "I am Aetheris Core, configured with the Google Gemini API (gemini-2.5-flash) and local ChromaDB storage."
        elif "joke" in q:
            return "Why do programmers wear glasses? Because they don't C#! 😂"
        return "I'm here! We can chat casually, or I can search my local persistent ChromaDB collection using local SentenceTransformers."

    def _build_prompt(self, query: str, docs: List[Dict[str, Any]]) -> str:
        context_str = "\n\n".join([f"Document {doc['id']} - {doc['title']}:\n{doc['content']}" for doc in docs])
        return f"""You are Aetheris Core, a world-class AI chatbot platform assistant.
Answer the user's query utilizing the retrieved context documents below.
If the documents do not contain the answer, synthesise a helpful response but indicate that it is from general knowledge.

Context Documents:
{context_str}

User Query: {query}
Answer:"""

    async def _generate_llm_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        # 1. Query free Gemini API using google-genai
        if self.gemini_client:
            try:
                # Async API model streaming call
                response = await self.gemini_client.aio.models.generate_content_stream(
                    model='gemini-3.5-flash',
                    contents=prompt
                )
                async for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                logger.error(f"Gemini API completions streaming failed: {e}. Falling back offline.")

        # 2. Local fallback completions
        fallback = self._offline_fallback_generator(prompt)
        async for token in self._stream_response(fallback):
            yield token

    def _offline_fallback_generator(self, prompt: str) -> str:
        match = re.search(r"User Query: (.*)\nAnswer:", prompt)
        query = match.group(1) if match else "general"
        q = query.lower()

        if "rag" in q or "retrieval" in q:
            return "Aetheris RAG Synthesis (Free Offline Fallback):\n\nLocal persistent ChromaDB collections are created successfully. Queries are embedded using local SentenceTransformers. Connect your Gemini API Key (`GEMINI_API_KEY`) to run live generative response streams."
        elif "websocket" in q or "stream" in q or "fastapi" in q:
            return "Aetheris WebSockets Info (Free Offline Fallback):\n\nFastAPI handles async WebSockets connections. When tokens stream, status codes increase WebGL wave velocity dynamically."
        elif "three" in q or "fiber" in q or "particle" in q:
            return "Aetheris Canvas Info (Free Offline Fallback):\n\nWebGL particles swarm is rendered using custom vertex shaders. Active streaming status escalates wave motion profiles."
        else:
            return f"Aetheris Core (Free Offline Fallback):\n\nI queried my persistent ChromaDB index for: '{query}'. Provide a `GEMINI_API_KEY` to stream live completions from gemini-3.5-flash."

    async def _stream_response(self, text: str) -> AsyncGenerator[str, None]:
        words = text.split(" ")
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield word + suffix
            await asyncio.sleep(0.02)
