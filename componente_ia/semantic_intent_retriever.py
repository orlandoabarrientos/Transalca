"""BM25/fuzzy fallback over curated intent examples."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from componente_ia.intent_router import INTENTS
from componente_ia.lightweight_rag import LightweightRAG, RAGDocument


DEFAULT_PATH = Path(__file__).with_name("data") / "intent_examples.jsonl"


class SemanticIntentRetriever:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PATH
        rows = []
        with self.path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("intent") in INTENTS and item.get("message"):
                    rows.append(item)
        self.index = LightweightRAG([
            RAGDocument(
                id=str(item.get("id") or f"intent-{index}"),
                title=str(item["message"]),
                content=str(item["message"]),
                kind="intent_example",
                source=str(item.get("source") or "curated"),
                keywords=(str(item["intent"]),),
                metadata={"intent": item["intent"]},
            )
            for index, item in enumerate(rows, 1)
        ])

    def classify(self, message: str, entities: Any = None, context: Any = None) -> dict[str, Any] | None:
        hits = self.index.search(message, limit=6, min_score=0.12)
        if not hits:
            return None
        scores: defaultdict[str, float] = defaultdict(float)
        for rank, hit in enumerate(hits):
            intent = str(hit.document.metadata.get("intent") or "")
            if intent in INTENTS:
                scores[intent] += float(hit.score) / (1.0 + rank * 0.35)
        if not scores:
            return None
        ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        primary, top = ordered[0]
        if top < 0.2:
            return None
        confidence = min(0.91, 0.52 + (top / (top + 5.0)) * 0.43)
        secondary = [intent for intent, score in ordered[1:3] if score >= top * 0.72]
        return {
            "primary": primary,
            "secondary": secondary,
            "confidence": round(confidence, 4),
            "score": round(top, 4),
        }


__all__ = ["SemanticIntentRetriever"]
