from typing import List, Dict, Any, Optional
from app.rag.search import HybridSearch
from app.rag.rerank import CrossEncoderReranker

class AgentTools:
    def __init__(self):
        self.hybrid_searcher = HybridSearch()
        self.reranker = CrossEncoderReranker()

    def query_knowledge_base(self, query: str, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves matching documents from the vector database (ChromaDB) using metadata filters and reranks them.
        """
        # 1. Execute Sparse + Dense Hybrid Search with metadata filtration
        search_results = self.hybrid_searcher.hybrid_search(query, metadata_filter=metadata_filter, top_k=3)
        
        # 2. Run Cross-Encoder Reranker
        reranked_results = self.reranker.rerank(query, search_results)
        
        return [item["document"] for item in reranked_results]

    def web_search(self, query: str) -> Dict[str, Any]:
        """
        Mock tool simulating external web search.
        """
        return {
            "query": query,
            "source": "Mock External Web Search",
            "results": [
                {
                    "title": f"Web article regarding {query}",
                    "content": f"Here is a mock search snippet summarizing external web information for query: {query}. It contains standard reference details."
                }
            ]
        }
