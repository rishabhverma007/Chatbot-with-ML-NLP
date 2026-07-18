import re
from typing import List, Dict, Any

class CrossEncoderReranker:
    def __init__(self):
        pass

    def _get_bigrams(self, text: str) -> set:
        words = re.sub(r"[^\w\s]", "", text.lower()).split()
        return set(zip(words[:-1], words[1:])) if len(words) > 1 else set(words)

    def compute_score(self, query: str, document_text: str) -> float:
        # Cross-Encoder simulation using token bigram overlap and word sequence distance
        query_words = re.sub(r"[^\w\s]", "", query.lower()).split()
        doc_words = re.sub(r"[^\w\s]", "", document_text.lower()).split()
        
        if not query_words or not doc_words:
            return 0.0

        # Feature 1: Term frequency / exact word overlap
        overlap = set(query_words).intersection(set(doc_words))
        word_overlap_ratio = len(overlap) / len(query_words)

        # Feature 2: Bigram overlap (checks order and syntax structure)
        q_bigrams = self._get_bigrams(query)
        d_bigrams = self._get_bigrams(document_text)
        bigram_overlap = q_bigrams.intersection(d_bigrams)
        bigram_overlap_ratio = len(bigram_overlap) / len(q_bigrams) if q_bigrams else 0.0

        # Feature 3: Sequence alignment (LCS - Longest Common Subsequence)
        lcs_len = self._lcs_length(query_words, doc_words)
        lcs_ratio = lcs_len / len(query_words)

        # Calculate weighted cross-encoder score
        score = (0.3 * word_overlap_ratio) + (0.4 * bigram_overlap_ratio) + (0.3 * lcs_ratio)
        return score

    def _lcs_length(self, list1: List[str], list2: List[str]) -> int:
        # Standard dynamic programming approach for LCS
        m, n = len(list1), len(list2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if list1[i-1] == list2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        return dp[m][n]

    def rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        reranked_results = []
        
        for item in candidates:
            # item is {"document": {...}, "rrf_score": ...}
            doc = item["document"]
            doc_content = doc["title"] + " " + doc["content"]
            cross_score = self.compute_score(query, doc_content)
            
            # Combine hybrid search score and cross-encoder score
            # RRF score is typically smaller (0.01 - 0.03), normalise cross-encoder score
            combined_score = (0.2 * item["rrf_score"]) + (0.8 * cross_score)
            
            reranked_results.append({
                "document": doc,
                "rrf_score": item["rrf_score"],
                "rerank_score": combined_score
            })
            
        # Sort by rerank score descending
        reranked_results.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked_results
