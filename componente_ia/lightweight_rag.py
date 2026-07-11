"""Small dependency-free BM25/fuzzy retriever for curated public knowledge."""

from __future__ import annotations

import math
import re
import threading
import unicodedata
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping

from componente_ia.knowledge_types import Evidence, RetrievalResult, evidence_id, to_jsonable


_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[/.-][a-z0-9]+)*", re.IGNORECASE)
_STOPWORDS = {
    "a", "al", "algo", "como", "con", "cual", "de", "del", "el", "en",
    "es", "esa", "ese", "esta", "este", "la", "las", "lo", "los", "me",
    "mi", "mis", "no", "o", "para", "pero", "por", "que", "se", "si", "su",
    "sus", "tengo", "un", "una", "y",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", text).strip()


def tokenize(value: object) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(normalize_text(value))
        if token not in _STOPWORDS and (len(token) > 1 or any(char.isdigit() for char in token))
    ]


@dataclass(frozen=True)
class RAGDocument:
    id: str
    title: str
    content: str
    kind: str = "knowledge"
    source: str = "curated_local"
    keywords: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "keywords", tuple(str(item) for item in self.keywords if item))
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable({
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "kind": self.kind,
            "source": self.source,
            "keywords": self.keywords,
            "metadata": self.metadata,
        })


@dataclass(frozen=True)
class RAGHit:
    document: RAGDocument
    score: float
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "score": round(float(self.score), 6),
            "matched_terms": list(self.matched_terms),
        }

    def to_evidence(self) -> Evidence:
        metadata = dict(self.document.metadata)
        dynamic = bool(metadata.pop("dynamic", False))
        verified = bool(metadata.pop("verified", not dynamic))
        confidence = min(0.92, 0.5 + max(0.0, self.score) / 12.0)
        return Evidence(
            id=evidence_id("rag", self.document.id),
            kind=self.document.kind,
            source=self.document.source,
            title=self.document.title,
            content=self.document.content,
            confidence=confidence,
            verified=verified,
            dynamic=dynamic,
            data={
                **metadata,
                "document_id": self.document.id,
                "retrieval_score": round(float(self.score), 6),
                "matched_terms": list(self.matched_terms),
            },
        )


class LightweightRAG:
    """In-memory BM25 index with a conservative typo-tolerant supplement.

    The index is designed for a few thousand public records. It has no model or
    network dependency and never accepts documents marked ``private``.
    """

    def __init__(
        self,
        documents: Iterable[RAGDocument | Mapping[str, Any]] = (),
        *,
        k1: float = 1.35,
        b: float = 0.72,
        cache_size: int = 128,
    ) -> None:
        self.k1 = float(k1)
        self.b = float(b)
        self.cache_size = max(0, int(cache_size))
        self._lock = threading.RLock()
        self._documents: dict[str, RAGDocument] = {}
        self._term_frequencies: dict[str, Counter[str]] = {}
        self._document_frequencies: Counter[str] = Counter()
        self._lengths: dict[str, int] = {}
        self._average_length = 1.0
        self._cache: OrderedDict[tuple[Any, ...], list[RAGHit]] = OrderedDict()
        self._version = 0
        self.replace(documents)

    def replace(self, documents: Iterable[RAGDocument | Mapping[str, Any]]) -> None:
        prepared: dict[str, RAGDocument] = {}
        for raw in documents or ():
            document = raw if isinstance(raw, RAGDocument) else RAGDocument(**dict(raw))
            if not document.id or bool(document.metadata.get("private")):
                continue
            prepared[document.id] = document
        with self._lock:
            self._documents = prepared
            self._rebuild()

    def upsert(self, documents: Iterable[RAGDocument | Mapping[str, Any]]) -> None:
        with self._lock:
            updated = dict(self._documents)
            for raw in documents or ():
                document = raw if isinstance(raw, RAGDocument) else RAGDocument(**dict(raw))
                if document.id and not bool(document.metadata.get("private")):
                    updated[document.id] = document
            self._documents = updated
            self._rebuild()

    def _rebuild(self) -> None:
        self._term_frequencies = {}
        self._document_frequencies = Counter()
        self._lengths = {}
        for doc_id, document in self._documents.items():

            tokens = (
                tokenize(document.content)
                + tokenize(document.title) * 2
                + [token for keyword in document.keywords for token in tokenize(keyword)] * 3
            )
            frequencies = Counter(tokens)
            self._term_frequencies[doc_id] = frequencies
            self._lengths[doc_id] = max(1, sum(frequencies.values()))
            self._document_frequencies.update(frequencies.keys())
        if self._lengths:
            self._average_length = sum(self._lengths.values()) / len(self._lengths)
        else:
            self._average_length = 1.0
        self._version += 1
        self._cache.clear()

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: Mapping[str, Any] | None = None,
        min_score: float = 0.08,
    ) -> list[RAGHit]:
        query_tokens = tokenize(query)
        if not query_tokens or limit <= 0:
            return []
        normalized_filters = tuple(sorted((str(key), str(value)) for key, value in (filters or {}).items()))
        cache_key = (self._version, normalize_text(query), int(limit), float(min_score), normalized_filters)
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._cache.move_to_end(cache_key)
                return list(cached)

            hits: list[RAGHit] = []
            for doc_id, document in self._documents.items():
                if filters and any(document.metadata.get(key) != value for key, value in filters.items()):
                    continue
                score, matched = self._score_document(doc_id, query_tokens, normalize_text(query))
                if score >= min_score:
                    hits.append(RAGHit(document=document, score=score, matched_terms=tuple(sorted(matched))))
            hits.sort(key=lambda hit: (-hit.score, hit.document.id))
            result = hits[:limit]
            if self.cache_size:
                self._cache[cache_key] = result
                self._cache.move_to_end(cache_key)
                while len(self._cache) > self.cache_size:
                    self._cache.popitem(last=False)
            return list(result)

    def retrieve(self, query: str, *, limit: int = 5, filters: Mapping[str, Any] | None = None) -> RetrievalResult:
        hits = self.search(query, limit=limit, filters=filters)
        evidence = [hit.to_evidence() for hit in hits]
        return RetrievalResult(
            query=query,
            evidence=evidence,
            status="ok" if evidence else "empty",
            available=True,
            reason=None if evidence else "no_local_knowledge_match",
            diagnostics={"documents": len(self), "algorithm": "bm25_fuzzy"},
        )

    def _score_document(self, doc_id: str, query_tokens: list[str], normalized_query: str) -> tuple[float, set[str]]:
        frequencies = self._term_frequencies[doc_id]
        document = self._documents[doc_id]
        length = self._lengths[doc_id]
        corpus_size = max(1, len(self._documents))
        score = 0.0
        matched: set[str] = set()
        vocabulary = tuple(frequencies.keys())
        for token in query_tokens:
            effective = token
            frequency = frequencies.get(token, 0)
            fuzzy_ratio = 0.0
            if not frequency and len(token) >= 5:
                candidates = (word for word in vocabulary if abs(len(word) - len(token)) <= 2)
                for candidate in candidates:
                    ratio = SequenceMatcher(None, token, candidate).ratio()
                    if ratio > fuzzy_ratio:
                        fuzzy_ratio = ratio
                        effective = candidate
                if fuzzy_ratio >= 0.84:
                    frequency = frequencies.get(effective, 0)
            if not frequency:
                continue
            matched.add(token)
            document_frequency = self._document_frequencies.get(effective, 0)
            inverse_frequency = math.log(1 + (corpus_size - document_frequency + 0.5) / (document_frequency + 0.5))
            denominator = frequency + self.k1 * (1 - self.b + self.b * length / self._average_length)
            token_score = inverse_frequency * (frequency * (self.k1 + 1)) / denominator
            score += token_score * (fuzzy_ratio if fuzzy_ratio else 1.0)
        searchable = normalize_text(" ".join((document.title, document.content, *document.keywords)))
        if normalized_query and len(normalized_query) >= 4 and normalized_query in searchable:
            score += 2.5
        return score, matched

    def __len__(self) -> int:
        return len(self._documents)


BM25Index = LightweightRAG
