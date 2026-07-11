"""Contratos de proveedores deterministas ejecutados localmente."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from componente_ia.knowledge_types import Evidence, to_jsonable


ALLOWED_ASSISTANT_TOOLS = frozenset({
    "search_inventory",
    "search_services",
    "search_business_faq",
    "search_web",
    "get_vehicle_fitment",
    "get_order_public_status",
    "get_branches",
})


@dataclass
class ProviderRequest:
    message: str
    intent: str | Mapping[str, Any] | None = None
    entities: Any = None
    context: Mapping[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable({
            "message": self.message,
            "intent": self.intent,
            "entities": self.entities,
            "context": self.context,
            "evidence": [item.to_dict() for item in self.evidence],
        })


@dataclass
class ProviderResult:
    provider: str
    answer: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    grounded: bool = False
    status: str = "ok"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(float(self.confidence), 1.0))
        if not self.evidence_ids and self.evidence:
            self.evidence_ids = [item.id for item in self.evidence]

    @property
    def available(self) -> bool:
        return self.status not in {"disabled", "unavailable", "error", "rejected"}

    def to_dict(self) -> dict[str, Any]:
        return to_jsonable({
            "provider": self.provider,
            "answer": self.answer,
            "evidence": [item.to_dict() for item in self.evidence],
            "evidence_ids": self.evidence_ids,
            "confidence": self.confidence,
            "grounded": self.grounded,
            "status": self.status,
            "tool_calls": self.tool_calls,
            "error": self.error,
            "metadata": self.metadata,
        })


class BaseProvider(ABC):
    name = "base"

    @abstractmethod
    def complete(
        self,
        messages: Sequence[Mapping[str, Any]] | ProviderRequest,
        tools: Sequence[Mapping[str, Any] | str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ProviderResult:
        raise NotImplementedError

    def health(self) -> dict[str, Any]:
        return {"provider": self.name, "enabled": True, "available": True}


def last_user_message(messages: Sequence[Mapping[str, Any]] | ProviderRequest) -> str:
    if isinstance(messages, ProviderRequest):
        return messages.message
    for item in reversed(list(messages or [])):
        if str(item.get("role") or "").lower() == "user":
            content = item.get("content")
            if isinstance(content, str):
                return content
    return ""


def tool_name(tool: Mapping[str, Any] | str) -> str:
    if isinstance(tool, str):
        return tool
    function = tool.get("function") if isinstance(tool, Mapping) else None
    if isinstance(function, Mapping):
        return str(function.get("name") or "")
    return str(tool.get("name") or "") if isinstance(tool, Mapping) else ""
