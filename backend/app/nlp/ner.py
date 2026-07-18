import re
from typing import List, Dict, Any

class NamedEntityRecognizer:
    def __init__(self):
        # Keyword-based entities
        self.technologies = {
            "rag", "fastapi", "nextjs", "react", "typescript", "python",
            "threejs", "webgl", "websockets", "nlp", "bm25", "vector",
            "embeddings", "mongodb", "postgres", "redis", "docker", "kubernetes"
        }
        self.organizations = {
            "google", "deepmind", "openai", "microsoft", "meta", "aws", "github"
        }

        # Patterns for regex-based entities
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "date": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})|(?:\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s+\d{4})?)\b",
            "number": r"\b\d+(?:\.\d+)?\b"
        }

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        entities = []
        lower_text = text.lower()

        # Extract Technology entities
        for tech in self.technologies:
            matches = re.finditer(r"\b" + re.escape(tech) + r"\b", lower_text)
            for m in matches:
                entities.append({
                    "entity": text[m.start():m.end()],
                    "label": "TECHNOLOGY",
                    "start": m.start(),
                    "end": m.end()
                })

        # Extract Organization entities
        for org in self.organizations:
            matches = re.finditer(r"\b" + re.escape(org) + r"\b", lower_text)
            for m in matches:
                entities.append({
                    "entity": text[m.start():m.end()],
                    "label": "ORGANIZATION",
                    "start": m.start(),
                    "end": m.end()
                })

        # Extract patterns
        for label, pattern in self.patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                # Avoid overlapping entity spans
                if not any(e["start"] <= m.start() < e["end"] for e in entities):
                    entities.append({
                        "entity": m.group(),
                        "label": label.upper(),
                        "start": m.start(),
                        "end": m.end()
                    })

        # Sort entities by start index
        entities.sort(key=lambda x: x["start"])
        return entities
