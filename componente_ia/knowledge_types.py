"""Serializable contracts shared by the assistant retrieval layer.

The assistant deliberately keeps evidence separate from prose.  An orchestrator or
LLM may phrase an answer, but facts such as stock, price, active services and
business policies must remain traceable to one of these records.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Mapping


_SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "secret",
    "token",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def evidence_id(prefix: str, *parts: object) -> str:
    """Build a stable, opaque id without leaking database identifiers in prose."""

    payload = "\x1f".join(str(part or "") for part in parts)
    digest = hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()[:16]
    clean_prefix = "".join(char for char in str(prefix).lower() if char.isalnum() or char in "_-")
    return f"{clean_prefix or 'ev'}:{digest}"


def to_jsonable(value: Any) -> Any:
    """Convert values to plain JSON types and redact common secret-bearing keys."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key)
            if normalized_key.lower() in _SENSITIVE_KEYS:
                result[normalized_key] = "[REDACTED]"
            else:
                result[normalized_key] = to_jsonable(item)
        return result
    if isinstance(value, (set, frozenset)):
        return sorted((to_jsonable(item) for item in value), key=str)
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return str(value)


@dataclass(frozen=True)
class Evidence:
    """One grounded fact or knowledge fragment.

    ``dynamic`` identifies values that may change (inventory, active services,
    branch data, and policies). ``verified`` means the configured source actually
    supplied the value for this request; it never means technical certainty beyond
    that source.
    """

    id: str
    kind: str
    source: str
    content: str
    title: str = ""
    confidence: float = 0.0
    verified: bool = False
    dynamic: bool = False
    data: Mapping[str, Any] = field(default_factory=dict)
    citations: tuple[str, ...] = ()
    retrieved_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", max(0.0, min(float(self.confidence), 1.0)))
        object.__setattr__(self, "data", dict(self.data or {}))
        object.__setattr__(self, "citations", tuple(str(item) for item in self.citations if item))

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable(asdict(self))


@dataclass
class RetrievalResult:
    """Uniform result returned by inventory, service, FAQ, RAG and web adapters."""

    query: str
    evidence: list[Evidence] = field(default_factory=list)
    status: str = "ok"
    available: bool = True
    partial: bool = False
    reason: str | None = None
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    @property
    def items(self) -> list[Evidence]:
        """Compatibility alias for callers that call retrieved evidence 'items'."""

        return self.evidence

    @property
    def grounded(self) -> bool:
        return bool(self.evidence) and all(item.verified or not item.dynamic for item in self.evidence)

    def extend(self, values: Iterable[Evidence]) -> None:
        self.evidence.extend(values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "evidence": [item.to_dict() for item in self.evidence],
            "status": self.status,
            "available": bool(self.available),
            "partial": bool(self.partial),
            "grounded": self.grounded,
            "reason": self.reason,
            "diagnostics": to_jsonable(self.diagnostics),
        }

