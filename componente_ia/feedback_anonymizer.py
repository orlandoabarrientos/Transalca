"""Anonimizacion local y fail-closed para casos de aprendizaje.

Este modulo no usa red ni modelos externos. Su objetivo no es conservar una
representacion reversible de la persona, sino retener solamente la forma
linguistica util para mejorar el asistente. Cuando no puede demostrar que el
resultado es seguro, devuelve ``safe=False`` y el almacén debe descartar el caso.
"""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from dataclasses import dataclass, field
from typing import Any, Iterable


_PROCESS_SALT = secrets.token_bytes(32)

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?58[\s().-]*)?(?:0?4(?:12|14|16|24|26)|0?2\d{2})"
    r"[\s().-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}(?!\d)"
)
_INTERNATIONAL_PHONE_RE = re.compile(r"(?<![\d/])\+\d{1,3}(?:[\s().-]*\d){7,14}(?!\d)")
_DOCUMENT_RE = re.compile(r"\b(?:cedula|c[eé]dula|rif)?\s*[VEJPG]-?\s*\d{5,10}\b", re.I)
_BANK_ACCOUNT_RE = re.compile(r"(?<!\d)\d{20}(?!\d)")
_CARD_RE = re.compile(r"(?<![\d/])(?:\d[ -]?){13,19}(?!\d)")
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_COORDINATE_RE = re.compile(
    r"(?<!\d)(?:-?(?:[0-8]?\d(?:\.\d+)?|90(?:\.0+)?))\s*[,;]\s*"
    r"(?:-?(?:1[0-7]\d(?:\.\d+)?|\d?\d(?:\.\d+)?|180(?:\.0+)?))(?!\d)"
)
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}(?:\.[A-Za-z0-9_-]{8,})?\b")
_BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}", re.I)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|token|cookie|session|"
    r"password|passwd|contrasena|contrase[nñ]a|clave|secret)\s*[:=]\s*[^\s,;]+",
    re.I,
)
_URL_SECRET_RE = re.compile(r"(?i)([?&](?:token|key|secret|session|code)=)[^&\s]+")
_ORDER_RE = re.compile(
    r"\b(?:pedido|orden|order|referencia|ref(?:erencia)? bancaria|operaci[oó]n|"
    r"comprobante)\s*(?:n(?:ro|umero|úmero)?\.?\s*)?[:#-]?\s*[A-Z0-9][A-Z0-9-]{3,31}\b",
    re.I,
)
_PLATE_RE = re.compile(
    r"\b(?:placa|matr[ií]cula)\s*[:#-]?\s*[A-Z0-9][A-Z0-9 -]{4,11}\b",
    re.I,
)
_ADDRESS_RE = re.compile(
    r"\b(?:vivo en|mi direcci[oó]n es|direcci[oó]n|domicilio|entregar en|buscar en)\s*"
    r"[:#-]?\s*[^\n,;]{4,120}",
    re.I,
)
_PERSON_RE = re.compile(
    r"\b(?:me llamo|mi nombre es|soy|contacto|a nombre de)\s+"
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'.-]*"
    r"(?:\s+[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ'.-]*){0,3}",
    re.I,
)
_COMPANY_RE = re.compile(
    r"\b(?:mi empresa es|empresa|raz[oó]n social)\s*[:#-]?\s*"
    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][^\n,;]{2,80}",
    re.I,
)
_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{8,}(?!\d)")
_HIGH_ENTROPY_RE = re.compile(r"\b(?=[A-Za-z0-9_-]{28,}\b)(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9_-]+\b")

_PLACEHOLDERS = {
    "EMAIL", "TELEFONO", "DOCUMENTO", "CUENTA_BANCARIA", "NUMERO_SENSIBLE",
    "IP", "COORDENADAS", "SECRETO", "REFERENCIA", "PLACA", "DIRECCION",
    "PERSONA", "EMPRESA", "TOKEN",
}


@dataclass(frozen=True, slots=True)
class AnonymizationResult:
    text: str
    safe: bool
    redactions: dict[str, int] = field(default_factory=dict)
    uncertainty_reasons: tuple[str, ...] = ()


def _replace(pattern: re.Pattern[str], text: str, marker: str, counts: dict[str, int]) -> str:
    def substitute(_match: re.Match[str]) -> str:
        counts[marker] = counts.get(marker, 0) + 1
        return f"[{marker}]"

    return pattern.sub(substitute, text)


class FeedbackAnonymizer:
    """Deterministic redactor with a conservative residual-safety check."""

    def __init__(self, max_text_length: int = 1600, max_history_items: int = 12) -> None:
        self.max_text_length = max(80, int(max_text_length))
        self.max_history_items = max(0, min(50, int(max_history_items)))

    def anonymize(self, value: Any, limit: int | None = None) -> AnonymizationResult:
        maximum = max(0, min(20_000, int(limit or self.max_text_length)))
        raw = str(value or "")
        uncertainty: list[str] = []
        if "\x00" in raw or any(ord(character) < 9 for character in raw):
            uncertainty.append("contenido_binario_o_control")
        if len(raw) > maximum:
            raw = raw[:maximum]
            uncertainty.append("texto_truncado")
        text = raw.replace("\x00", " ")
        counts: dict[str, int] = {}
        rules = (
            (_JWT_RE, "SECRETO"),
            (_BEARER_RE, "SECRETO"),
            (_SECRET_ASSIGNMENT_RE, "SECRETO"),
            (_EMAIL_RE, "EMAIL"),
            (_PHONE_RE, "TELEFONO"),
            (_INTERNATIONAL_PHONE_RE, "TELEFONO"),
            (_DOCUMENT_RE, "DOCUMENTO"),
            (_BANK_ACCOUNT_RE, "CUENTA_BANCARIA"),
            (_CARD_RE, "NUMERO_SENSIBLE"),
            (_IP_RE, "IP"),
            (_COORDINATE_RE, "COORDENADAS"),
            (_ORDER_RE, "REFERENCIA"),
            (_PLATE_RE, "PLACA"),
            (_ADDRESS_RE, "DIRECCION"),
            (_PERSON_RE, "PERSONA"),
            (_COMPANY_RE, "EMPRESA"),
            (_HIGH_ENTROPY_RE, "TOKEN"),
        )
        for pattern, marker in rules:
            text = _replace(pattern, text, marker, counts)
        text, url_count = _URL_SECRET_RE.subn(r"\1[SECRETO]", text)
        if url_count:
            counts["SECRETO"] = counts.get("SECRETO", 0) + url_count
        text = " ".join(text.split())



        if _LONG_NUMBER_RE.search(text):
            uncertainty.append("numero_largo_no_clasificado")
        for pattern, reason in (
            (_EMAIL_RE, "correo_residual"),
            (_PHONE_RE, "telefono_residual"),
            (_INTERNATIONAL_PHONE_RE, "telefono_internacional_residual"),
            (_JWT_RE, "token_residual"),
            (_BEARER_RE, "credencial_residual"),
            (_SECRET_ASSIGNMENT_RE, "secreto_residual"),
        ):
            if pattern.search(text):
                uncertainty.append(reason)
        return AnonymizationResult(
            text=text,
            safe=not uncertainty,
            redactions=dict(sorted(counts.items())),
            uncertainty_reasons=tuple(sorted(set(uncertainty))),
        )

    def anonymize_history(self, history: Any) -> tuple[list[str], bool, tuple[str, ...]]:
        if history in (None, ""):
            return [], True, ()
        if not isinstance(history, (list, tuple)):
            return [], False, ("historial_invalido",)
        cleaned: list[str] = []
        reasons: list[str] = []
        for item in list(history)[-self.max_history_items:]:
            if isinstance(item, dict):
                value = item.get("content", item.get("message", item.get("text", "")))
            else:
                value = item
            result = self.anonymize(value, 800)
            if result.text:
                cleaned.append(result.text)
            reasons.extend(result.uncertainty_reasons)
        return cleaned, not reasons, tuple(sorted(set(reasons)))

    @staticmethod
    def has_private_placeholder(value: Any) -> bool:
        text = str(value or "")
        return any(f"[{marker}]" in text for marker in _PLACEHOLDERS)


def session_hash(session_id: Any) -> str:
    """Return a non-reversible pseudonym; no raw session identifier is stored."""

    value = str(session_id or "").strip()
    if not value:
        return "anon"
    configured = os.getenv("ASSISTANT_FEEDBACK_HASH_SALT", "").encode("utf-8")
    salt = configured or _PROCESS_SALT
    return hashlib.sha256(salt + b"\x00" + value.encode("utf-8", errors="ignore")).hexdigest()[:24]


def anonymize_text(value: Any, limit: int = 1600) -> str:
    """Compatibility helper. Persistence must additionally check ``safe``."""

    return FeedbackAnonymizer(max_text_length=max(80, int(limit))).anonymize(value, limit).text


def placeholders_in(values: Iterable[Any]) -> set[str]:
    found: set[str] = set()
    for value in values:
        text = str(value or "")
        found.update(marker for marker in _PLACEHOLDERS if f"[{marker}]" in text)
    return found


__all__ = [
    "AnonymizationResult", "FeedbackAnonymizer", "anonymize_text",
    "placeholders_in", "session_hash",
]
