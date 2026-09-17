from __future__ import annotations

from dataclasses import asdict, dataclass
import re
import unicodedata
from typing import Any, Mapping

_UNCONFIGURED = frozenset({
    "",
    "null",
    "none",
    "undefined",
    "por configurar",
    "configurar en panel admin",
    "todo config",
    "not configured",
})

_PUBLIC_MESSAGES = {
    "price": "El precio debe confirmarse con la administración.",
    "service_price": "El precio debe confirmarse con la administración.",
    "duration": "La duración se confirma según el vehículo y el servicio.",
    "service_duration": "La duración se confirma según el vehículo y el servicio.",
    "phone": "El contacto debe confirmarse con la administración.",
    "contact": "El contacto debe confirmarse con la administración.",
    "email": "El contacto debe confirmarse con la administración.",
    "hours": "El horario debe confirmarse con la administración.",
    "business_hours": "El horario debe confirmarse con la administración.",
    "address": "La dirección debe confirmarse con la administración.",
    "default": "Ese dato debe confirmarse con la administración.",
}

_PLACEHOLDER_TEXT_RE = re.compile(
    r"(?i)\b(?:POR(?:[\s_-]+)CONFIGURAR|"
    r"CONFIGURAR(?:[\s_-]+)EN(?:[\s_-]+)PANEL(?:[\s_-]+)ADMIN|"
    r"TODO(?:[\s_-]+)CONFIG|NULL|NONE|UNDEFINED|"
    r"NOT(?:[\s_-]+)CONFIGURED)\b"
)

def _fold(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[_-]+", " ", text.casefold())
    return re.sub(r"\s+", " ", text).strip()

def is_unconfigured_business_value(value: Any) -> bool:

    if value is None:
        return True
    if isinstance(value, str):
        return _fold(value) in _UNCONFIGURED
    return False

def public_confirmation_message(field: str | None) -> str:
    name = re.sub(r"[^a-z0-9]+", "_", _fold(field)).strip("_")
    return _PUBLIC_MESSAGES.get(name, _PUBLIC_MESSAGES["default"])

@dataclass(frozen=True)
class SanitizedBusinessValue:
    field: str
    configured: bool
    public_value: Any
    source: str
    public_message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def claim_metadata(self) -> dict[str, Any]:

        return {
            "configured": self.configured,
            "public_value": self.public_value,
            "source": self.source,
        }

def sanitize_public_business_value(
    value: Any,
    *,
    field: str,
    source: str,
) -> SanitizedBusinessValue:

    configured = not is_unconfigured_business_value(value)
    public_value: Any
    if configured and isinstance(value, str):
        public_value = re.sub(r"\s+", " ", value).strip()
    elif configured:
        public_value = value
    else:
        public_value = None
    return SanitizedBusinessValue(
        field=str(field or "default"),
        configured=configured,
        public_value=public_value,
        source=str(source or ""),
        public_message=(
            str(public_value)
            if configured
            else public_confirmation_message(field)
        ),
    )

def sanitize_public_business_text(
    value: Any,
    *,
    field: str = "default",
) -> str:

    text = str(value or "")
    message = public_confirmation_message(field)
    return _PLACEHOLDER_TEXT_RE.sub(message.rstrip("."), text)

def contains_unconfigured_business_placeholder(value: Any) -> bool:

    return bool(_PLACEHOLDER_TEXT_RE.search(str(value or "")))

def configured_public_value(
    value: Any,
    *,
    field: str,
    source: str,
) -> Any:
    return sanitize_public_business_value(
        value, field=field, source=source,
    ).public_value

def metadata_from_mapping(
    value: Mapping[str, Any] | None,
    *,
    field: str,
    source: str,
) -> dict[str, Any]:

    if isinstance(value, Mapping) and {
        "configured", "public_value", "source",
    } <= set(value):
        return {
            "configured": bool(value.get("configured")),
            "public_value": value.get("public_value"),
            "source": str(value.get("source") or source),
        }
    return sanitize_public_business_value(
        value, field=field, source=source,
    ).claim_metadata()

__all__ = [
    "SanitizedBusinessValue", "configured_public_value",
    "contains_unconfigured_business_placeholder",
    "is_unconfigured_business_value", "metadata_from_mapping",
    "public_confirmation_message", "sanitize_public_business_text",
    "sanitize_public_business_value",
]
