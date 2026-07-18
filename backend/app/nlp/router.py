import re
from typing import Set

class IntentRouter:
    def __init__(self):
        # Seed phrases for Chitchat
        self.chitchat_seeds = {
            "hello", "hi", "hey", "hola", "greetings", "howdy",
            "how are you", "how's it going", "what's up", "how do you do",
            "who are you", "what is your name", "tell me a joke", "are you human",
            "good morning", "good afternoon", "good evening", "bye", "goodbye", "thanks", "thank you"
        }
        
        # Seed phrases for Knowledge Queries
        self.knowledge_seeds = {
            "explain", "what is", "how does", "why does", "tell me about",
            "documentation", "rag", "retrieval", "vector database", "embeddings",
            "search", "find information", "get details", "research papers",
            "data analysis", "sales figures", "code examples", "technical specifications"
        }

    def _tokenize(self, text: str) -> Set[str]:
        # Lowercase, strip non-alphanumeric, and tokenize
        cleaned = re.sub(r"[^\w\s]", "", text.lower())
        return set(cleaned.split())

    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        if not set1 or not set2:
            return 0.0
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union)

    def classify_intent(self, text: str) -> str:
        query_tokens = self._tokenize(text)
        if not query_tokens:
            return "chitchat"

        max_chitchat_sim = 0.0
        for seed in self.chitchat_seeds:
            seed_tokens = self._tokenize(seed)
            sim = self._jaccard_similarity(query_tokens, seed_tokens)
            if sim > max_chitchat_sim:
                max_chitchat_sim = sim

        max_knowledge_sim = 0.0
        for seed in self.knowledge_seeds:
            seed_tokens = self._tokenize(seed)
            sim = self._jaccard_similarity(query_tokens, seed_tokens)
            if sim > max_knowledge_sim:
                max_knowledge_sim = sim

        # Add rule-based indicators for knowledge query
        knowledge_indicators = ["what", "how", "why", "who", "define", "explain", "get", "show", "list", "search"]
        indicator_count = sum(1 for word in knowledge_indicators if word in query_tokens)
        
        # Boost knowledge similarity if indicator words are present
        if indicator_count > 0:
            max_knowledge_sim += 0.15 * indicator_count

        # Default fallback logic
        if max_knowledge_sim > max_chitchat_sim:
            return "knowledge_query"
        elif max_chitchat_sim > 0.1:
            return "chitchat"
        else:
            # Fallback to knowledge_query for longer, more complex queries
            return "knowledge_query" if len(query_tokens) > 4 else "chitchat"
