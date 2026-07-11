"""Recuperación ligera de conocimiento técnico general sobre cauchos."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id
from componente_ia.lightweight_rag import LightweightRAG, RAGDocument


DEFAULT_PATH = Path(__file__).with_name("data") / "tire_technical_knowledge.json"


class TechnicalKnowledge:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_PATH
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self.version = str(payload.get("version") or "unknown")
        self.disclaimer = str(payload.get("disclaimer") or "")
        entries = payload.get("entries") or []
        if not isinstance(entries, list) or not entries:
            raise ValueError("tire technical knowledge must contain entries")
        self.entries = {str(item["id"]): dict(item) for item in entries}
        if len(self.entries) != len(entries):
            raise ValueError("technical knowledge ids must be unique")
        self.rag = LightweightRAG([
            RAGDocument(
                id=item["id"],
                title=item["title"],
                content=item["content"],
                kind="technical_knowledge",
                source="tire_technical_knowledge.json",
                keywords=tuple(item.get("keywords") or []),
                metadata={"version": self.version},
            )
            for item in entries
        ])

    def search(self, query: str, limit: int = 3) -> RetrievalResult:
        hits = self.rag.search(query, limit=max(1, min(int(limit), 5)))
        evidence = []
        for hit in hits:
            item = self.entries[hit.document.id]
            evidence.append(Evidence(
                id=evidence_id("technical", item["id"], self.version),
                kind="technical_knowledge",
                source="tire_technical_knowledge.json",
                title=item["title"],
                content=item["content"],
                confidence=min(0.95, 0.72 + max(0.0, hit.score) / 20.0),
                verified=True,
                dynamic=False,
                data={
                    "topic": item["id"],
                    "version": self.version,
                    "disclaimer": self.disclaimer,
                    "matched_terms": list(hit.matched_terms),
                },
            ))
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status="ok" if evidence else "empty",
            available=True,
            reason=None if evidence else "no_technical_match",
            diagnostics={"version": self.version, "entries": len(self.entries)},
        )


_DEFAULT = TechnicalKnowledge()


def search_technical_knowledge(query: str, limit: int = 3) -> RetrievalResult:
    return _DEFAULT.search(query, limit=limit)


__all__ = ["TechnicalKnowledge", "search_technical_knowledge"]
