import os
import math
import re
import logging
from typing import List, Dict, Any, Optional

# Setup logger
logger = logging.getLogger("PersistentSearch")

# Gracefully attempt to import ChromaDB and SentenceTransformers
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Default mock documents for initialization
MOCK_CORPUS = [
    {
        "id": "doc1",
        "title": "Retrieval-Augmented Generation (RAG) Architecture",
        "content": "Retrieval-Augmented Generation (RAG) combines semantic dense retrieval with large language model generation. RAG fetches relevant context documents from a vector database based on embeddings, formats them into a prompt template, and sends them to the generative LLM. This prevents hallucination and guarantees facts.",
        "metadata": {"technology": "rag", "organization": "ai"}
    },
    {
        "id": "doc2",
        "title": "FastAPI WebSockets Streaming Integration",
        "content": "FastAPI provides native asynchronous support for WebSockets, allowing real-time bi-directional streaming. To stream responses chunk-by-chunk, use an active WebSocket connection and yield structured tokens as JSON frames. This is ideal for chatbot interfaces requiring low latency.",
        "metadata": {"technology": "fastapi", "organization": "python"}
    },
    {
        "id": "doc3",
        "title": "Next.js App Router and Layout Structures",
        "content": "Next.js App Router utilizes React Server Components and nested layouts to deliver optimized layouts. CSS modules or global stylesheet utilities (Tailwind) are imported into layout.tsx. WebGL canvases are wrapped inside Client Components to run on the browser graphics card safely.",
        "metadata": {"technology": "nextjs", "organization": "react"}
    },
    {
        "id": "doc4",
        "title": "React Three Fiber (R3F) and WebGL Rendering",
        "content": "React Three Fiber is a React wrapper for Three.js. It allows developers to construct interactive 3D scenes using custom shaders and moving BufferGeometry. Adding a mouse-move event listener can influence particle orbits dynamically to create premium desktop experiences.",
        "metadata": {"technology": "threejs", "organization": "react"}
    },
    {
        "id": "doc5",
        "title": "Glassmorphism UI/UX Design System",
        "content": "Glassmorphic visual designs rely on hardware-accelerated css styles. The key settings are backdrop-filter: blur(12px) saturate(150%), semi-transparent white borders, and drop-shadows. The layout should have translateZ(0) to force GPU hardware rendering and smooth movement.",
        "metadata": {"technology": "css", "organization": "web"}
    }
]

class HybridSearch:
    def __init__(self, corpus: List[Dict[str, Any]] = MOCK_CORPUS):
        self.corpus = corpus
        self.documents = [doc["content"] for doc in corpus]
        self.doc_ids = [doc["id"] for doc in corpus]
        self.num_docs = len(self.documents)
        
        # Local fallback sparse index structures
        self.vocab = set()
        self.doc_token_counts = []
        self.doc_lengths = []
        self.df = {}
        self._build_sparse_index()

        self.embedder = None
        self.chroma_client = None
        self.chroma_collection = None
        
        # Load local sentence transformers
        self._init_embedder()
        # Initialize persistent ChromaDB
        self._init_vector_db()

    def rebuild_sparse_index(self):
        """Re-computes BM25/sparse indices from the current self.corpus."""
        self.documents = [doc["content"] for doc in self.corpus]
        self.doc_ids = [doc["id"] for doc in self.corpus]
        self.num_docs = len(self.documents)
        self.vocab = set()
        self.doc_token_counts = []
        self.doc_lengths = []
        self.df = {}
        self._build_sparse_index()

    def _init_embedder(self):
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use 100% free local embedding model: all-MiniLM-L6-v2
                logger.info("Initializing SentenceTransformer('all-MiniLM-L6-v2')...")
                self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("SentenceTransformer model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load local SentenceTransformer: {e}. Fallback vector hashing active.")
        else:
            logger.info("sentence-transformers package not loaded. Fallback vector hashing active.")

    def _init_vector_db(self):
        chroma_dir = os.environ.get("CHROMA_DB_DIR", "./chroma_data")
        
        if CHROMA_AVAILABLE:
            try:
                # Initialize Chroma Persistent Client
                logger.info(f"Connecting to persistent ChromaDB at: {chroma_dir}")
                self.chroma_client = chromadb.PersistentClient(path=chroma_dir)
                
                # Check or create collection
                try:
                    self.chroma_collection = self.chroma_client.get_collection("knowledge_corpus")
                    logger.info("Retrieved existing Chroma collection 'knowledge_corpus'.")
                    
                    # Try to load all documents from the collection
                    all_docs = self.chroma_collection.get()
                    if all_docs and all_docs.get("documents"):
                        loaded_corpus = []
                        for idx, doc_text in enumerate(all_docs["documents"]):
                            doc_id = all_docs["ids"][idx]
                            metadata = all_docs["metadatas"][idx] if all_docs["metadatas"] else {}
                            title = metadata.get("title", metadata.get("source", "Vector Doc"))
                            loaded_corpus.append({
                                "id": doc_id,
                                "title": title,
                                "content": doc_text,
                                "metadata": metadata
                            })
                        if loaded_corpus:
                            self.corpus = loaded_corpus
                            self.rebuild_sparse_index()
                            logger.info(f"Successfully loaded {len(self.corpus)} dynamic documents from ChromaDB.")
                    else:
                        logger.info("Chroma collection is empty. Populating with defaults...")
                        for doc in self.corpus:
                            vector = self._get_embedding(doc["content"])
                            self.chroma_collection.add(
                                embeddings=[vector],
                                documents=[doc["content"]],
                                metadatas=[doc["metadata"]],
                                ids=[doc["id"]]
                            )
                        self.rebuild_sparse_index()
                except Exception as e:
                    logger.info(f"Collection not found or error loading ({e}). Creating new collection 'knowledge_corpus'...")
                    self.chroma_collection = self.chroma_client.create_collection("knowledge_corpus")
                    
                    # Populate collection with documents and metadata
                    for doc in self.corpus:
                        vector = self._get_embedding(doc["content"])
                        self.chroma_collection.add(
                            embeddings=[vector],
                            documents=[doc["content"]],
                            metadatas=[doc["metadata"]],
                            ids=[doc["id"]]
                        )
                    self.rebuild_sparse_index()
                logger.info("ChromaDB persistent collection fully loaded.")
            except Exception as e:
                logger.warning(f"Could not load persistent ChromaDB: {e}. Defaulting to numpy TF-IDF.")
                self.chroma_client = None
                self.chroma_collection = None

    def _get_embedding(self, text: str) -> List[float]:
        # Generate dense embeddings (384 dim for all-MiniLM-L6-v2, or 1536 hash fallback)
        if self.embedder:
            try:
                emb = self.embedder.encode(text)
                return emb.tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformer encoding failed: {e}. Fallback hash active.")
        
        return self._generate_lightweight_vector(text, dimensions=384)

    def _generate_lightweight_vector(self, text: str, dimensions: int = 384) -> List[float]:
        vector = [0.0] * dimensions
        words = re.sub(r"[^\w\s]", "", text.lower()).split()
        if not words:
            return vector
            
        for word in words:
            h = hash(word)
            idx = abs(h) % dimensions
            vector[idx] += 1.0
            
        magnitude = math.sqrt(sum(v**2 for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        return vector

    def _build_sparse_index(self):
        for doc in self.documents:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            
            token_counts = {}
            for t in tokens:
                token_counts[t] = token_counts.get(t, 0) + 1
                self.vocab.add(t)
            
            self.doc_token_counts.append(token_counts)
            
            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1
        
        self.avg_doc_len = sum(self.doc_lengths) / self.num_docs if self.num_docs > 0 else 0

    def _tokenize(self, text: str) -> List[str]:
        return re.sub(r"[^\w\s]", "", text.lower()).split()

    def sparse_search(self, query: str) -> List[Dict[str, Any]]:
        query_tokens = self._tokenize(query)
        scores = []
        k1 = 1.5
        b = 0.75
        
        for idx in range(self.num_docs):
            score = 0.0
            doc_len = self.doc_lengths[idx]
            token_counts = self.doc_token_counts[idx]
            
            for token in query_tokens:
                if token in self.vocab:
                    tf = token_counts.get(token, 0)
                    df = self.df.get(token, 0)
                    idf = math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1.0)
                    numerator = tf * (k1 + 1.0)
                    denominator = tf + k1 * (1.0 - b + b * (doc_len / self.avg_doc_len))
                    score += idf * (numerator / denominator)
            
            scores.append((self.corpus[idx], score))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def dense_search(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if self.chroma_collection:
            try:
                query_vector = self._get_embedding(query)
                
                # Format filter rules
                chroma_where = {}
                if metadata_filter:
                    chroma_where = {k: v for k, v in metadata_filter.items() if v}
                
                # Prevent querying 0 or negative results; scale up if corpus grows
                query_limit = min(50, max(len(self.corpus), 5))
                results = self.chroma_collection.query(
                    query_embeddings=[query_vector],
                    n_results=query_limit,
                    where=chroma_where if chroma_where else None
                )
                
                parsed_res = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    ids = results["ids"][0]
                    metadatas = results["metadatas"][0]
                    distances = results["distances"][0] if "distances" in results else [0.0]*len(docs)
                    
                    for idx, doc_text in enumerate(docs):
                        original_doc = next((d for d in self.corpus if d["id"] == ids[idx]), None)
                        if original_doc:
                            title = original_doc["title"]
                        elif metadatas and metadatas[idx]:
                            title = metadatas[idx].get("title", metadatas[idx].get("source", "Vector Doc"))
                        else:
                            title = "Vector Doc"
                        
                        similarity = 1.0 / (1.0 + distances[idx])
                        parsed_res.append(({
                            "id": ids[idx],
                            "title": title,
                            "content": doc_text,
                            "metadata": metadatas[idx] if metadatas else {}
                        }, similarity))
                        
                parsed_res.sort(key=lambda x: x[1], reverse=True)
                return parsed_res
            except Exception as e:
                logger.error(f"ChromaDB persistent search failed: {e}. Falling back to cosine.")

        # Fallback to local character cosine calculation
        query_grams = self._get_char_ngrams(query, 3)
        scores = []
        
        for idx, doc in enumerate(self.corpus):
            if metadata_filter:
                match = True
                for k, v in metadata_filter.items():
                    if doc.get("metadata", {}).get(k) != v:
                        match = False
                if not match:
                    continue

            doc_grams = self._get_char_ngrams(doc["title"] + " " + doc["content"], 3)
            sim = self._cosine_sim(query_grams, doc_grams)
            scores.append((doc, sim))
            
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _get_char_ngrams(self, text: str, n: int) -> Dict[str, int]:
        clean_text = re.sub(r"\s+", " ", text.lower())
        grams = {}
        for i in range(len(clean_text) - n + 1):
            g = clean_text[i:i+n]
            grams[g] = grams.get(g, 0) + 1
        return grams

    def _cosine_sim(self, g1: Dict[str, int], g2: Dict[str, int]) -> float:
        intersection = set(g1.keys()).intersection(set(g2.keys()))
        if not intersection:
            return 0.0
        
        dot_product = sum(g1[k] * g2[k] for k in intersection)
        mag1 = math.sqrt(sum(v**2 for v in g1.values()))
        mag2 = math.sqrt(sum(v**2 for v in g2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    def hybrid_search(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None, top_k: int = 3, rrf_k: int = 60) -> List[Dict[str, Any]]:
        sparse_res = self.sparse_search(query)
        dense_res = self.dense_search(query, metadata_filter)
        
        rrf_scores = {}
        doc_map = {}
        
        for rank, (doc, _) in enumerate(sparse_res):
            doc_id = doc["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))
            doc_map[doc_id] = doc
            
        for rank, (doc, _) in enumerate(dense_res):
            doc_id = doc["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (rrf_k + rank + 1))
            doc_map[doc_id] = doc
            
        final_results = []
        for doc_id, score in rrf_scores.items():
            final_results.append({
                "document": doc_map[doc_id],
                "rrf_score": score
            })
                
        final_results.sort(key=lambda x: x["rrf_score"], reverse=True)
        return final_results[:top_k]
