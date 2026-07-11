"""Guardrails de entrada/salida para el dominio automotriz de Transalca."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from typing import Any

from componente_ia.entity_extractor import extract, normalize_message


DOMAIN_RESPONSE = "Puedo ayudarte con cauchos, productos, servicios, mantenimiento, inventario, pedidos y atención de Transalca."
SENSITIVE_RESPONSE = "No puedo ayudar a revelar datos privados, credenciales ni configuración interna. Puedo ayudarte con cauchos, productos, servicios, mantenimiento, inventario, pedidos y atención de Transalca."


@dataclass(frozen=True)
class GuardrailDecision:
    allowed: bool
    response: str = ""
    category: str = "allowed"
    reason: str = ""
    risk: float = 0.0

    @property
    def intent(self) -> str | None:
        if self.category in {"sensitive_request", "prompt_injection", "malicious_input"}:
            return "sensitive_request"
        if self.category == "out_of_scope":
            return "out_of_scope"
        return None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


_DOMAIN_TERMS = {
    "caucho", "cauchos", "llanta", "llantas", "goma", "gomas", "neumatico", "rin", "aro",
    "vehiculo", "carro", "camioneta", "camion", "gandola", "autobus", "remolque", "motor",
    "servicio", "servicios", "mantenimiento", "alineacion", "balanceo", "rotacion", "montaje",
    "aceite", "filtro", "bateria", "freno", "scanner", "inyector", "suspension", "repuesto",
    "producto", "productos", "inventario", "stock", "precio", "pedido", "pago", "comprobante",
    "garantia", "credito", "sucursal", "horario", "promocion", "delivery", "flota", "empresa",
    "toyota", "ford", "chevrolet", "nissan", "jeep", "hino", "isuzu", "mack", "hilux",
}

_OUT_OF_SCOPE_TERMS = {
    "politica", "elecciones", "presidente", "diputado", "futbol", "beisbol", "deportes",
    "noticias", "farandula", "pelicula", "peliculas", "series", "horoscopo", "receta",
    "novia", "novio", "bitcoin", "criptomoneda", "criptomonedas", "videojuego", "videojuegos",
    "cocina", "pareja", "historia", "moda",
}

_SECRET_PATTERNS = (
    r"\b(?:api[_ -]?key|secret(?:o|a)?|password|contrasena|credencial(?:es)?|bearer token|access token|refresh token|cookie(?:s)?)\b",
    r"\b[A-Z][A-Z0-9_]{2,}_(?:API_?KEY|TOKEN|SECRET|PASSWORD|PRIVATE_?KEY)\b",
    r"\b(?:variables? de entorno|archivo \.env|\.env|configuracion interna|rutas? internas?|logs? internos?|dump(?:s)?|consulta(?:s)? sql)\b",
    r"\b(?:datos? (?:privados?|personales?)|clientes?)\b.{0,30}\b(?:muestra|dame|revela|extrae|lista|exporta|descarga)\b",
    r"\b(?:muestra|dame|revela|extrae|lista|exporta|descarga)\b.{0,30}\b(?:datos? (?:privados?|personales?)|clientes?)\b",
    r"\b(?:lista|muestra|dame|ensena|revela)\b.{0,45}\b(?:direccion privada|todos los datos|nombre,? cedula y telefono)\b",
    r"\b(?:sin verificarme|sin autenticar|sin autorizacion)\b.{0,60}\b(?:datos?|pedido|orden)\b",
    r"\b(?:nombre|cedula|telefono)\b.{0,45}\b(?:pedido|orden)\b",
)

_INJECTION_PATTERNS = (
    r"\b(?:ignora|omite|olvida|desobedece|salta|desactiva)\b.{0,50}\b(?:instrucciones|reglas|sistema|prompt|guardrails?)\b",
    r"\b(?:system prompt|developer message|mensaje del sistema|prompt del sistema|modo desarrollador|jailbreak)\b",
    r"\b(?:actua|responde)\b.{0,30}\b(?:sin restricciones|como root|como administrador)\b",
    r"\b(?:ejecuta|obedece)\b.{0,35}\b(?:orden|instruccion)\b.{0,20}\boculta\b",
)

_MALICIOUS_PATTERNS = (
    r"<\s*script\b|javascript\s*:|onerror\s*=|onload\s*=",
    r"\bunion\s+(?:all\s+)?select\b|\bdrop\s+table\b|\binformation_schema\b",
    r"(?:'|\")\s*or\s+['\"]?1['\"]?\s*=\s*['\"]?1|;\s*--",
    r"\.\.[/\\].{0,30}(?:etc[/\\]passwd|\.env|config)",
    r"(?:\b[a-z]:\\|/(?:home|app|srv|var|etc|opt|root|users)/).{0,120}\b(?:\.env|config|logs?|secrets?|credentials?)\b",
    r"```\s*sql\b|\bselect\b[\s\S]{0,300}?\bfrom\b",
    r"\$\{\s*jndi\s*:[^}]+\}|\{\{\s*(?:config|settings?|request|self)\b[^}]*\}\}",
)

_OUTPUT_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:password|contrasena|api[_ -]?key)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:mysql|postgres(?:ql)?|mongodb)://[^\s]+", re.IGNORECASE),
    re.compile(r"\b[A-Za-z]:\\(?:[^\s\r\n<>|\"]+\\)*[^\s\r\n<>|\"]*"),
    re.compile(r"(?<![\w])/(?:home|app|srv|var|etc|opt|root|Users)/(?:[^\s\r\n]+/)*[^\s\r\n]*", re.IGNORECASE),
    re.compile(r"\bSELECT\b[\s\S]{0,500}?\bFROM\b", re.IGNORECASE),
    re.compile(r"\b(?:INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE)\b", re.IGNORECASE),
    re.compile(r"Traceback \(most recent call last\):[\s\S]{0,2000}", re.IGNORECASE),
)


class Guardrails:
    def __init__(self, max_message_length: int | None = None):
        configured = os.getenv("ASSISTANT_MAX_MESSAGE_LENGTH", "2000")
        self.max_message_length = int(max_message_length or configured or 2000)

    def check(self, message: Any, entities: Any = None) -> GuardrailDecision:
        raw = str(message or "").strip()
        if not raw:
            return GuardrailDecision(False, "Escribe tu consulta para poder ayudarte.", "invalid_input", "empty", 0.0)
        if len(raw) > self.max_message_length:
            return GuardrailDecision(False, f"La consulta supera el límite de {self.max_message_length} caracteres.", "invalid_input", "too_long", 0.2)
        text = normalize_message(raw)
        if any(re.search(pattern, raw, re.IGNORECASE | re.DOTALL) for pattern in _MALICIOUS_PATTERNS):
            return GuardrailDecision(False, SENSITIVE_RESPONSE, "malicious_input", "active_payload", 1.0)
        if any(re.search(pattern, text, re.IGNORECASE | re.DOTALL) for pattern in _INJECTION_PATTERNS):
            return GuardrailDecision(False, SENSITIVE_RESPONSE, "prompt_injection", "instruction_override", 1.0)
        if any(re.search(pattern, text, re.IGNORECASE | re.DOTALL) for pattern in _SECRET_PATTERNS):
            return GuardrailDecision(False, SENSITIVE_RESPONSE, "sensitive_request", "secret_or_private_data", 0.98)

        entity_values = entities or extract(raw)
        tokens = set(re.findall(r"[a-z0-9]+", text))
        has_domain = bool(tokens & _DOMAIN_TERMS) or any(
            _get(entity_values, key) for key in (
                "make", "model", "year", "requested_tire_size", "current_tire_size",
                "requested_rim", "current_rim", "service", "product_category", "order_reference",
            )
        )
        if tokens & _OUT_OF_SCOPE_TERMS:
            return GuardrailDecision(False, DOMAIN_RESPONSE, "out_of_scope", "outside_business_domain", 0.95)
        return GuardrailDecision(True)

    def validate_output(self, answer: Any) -> GuardrailDecision:
        text = str(answer or "")
        if not text.strip():
            return GuardrailDecision(False, "No pude generar una respuesta segura. Intenta reformular tu consulta.", "invalid_output", "empty", 0.5)
        if any(pattern.search(text) for pattern in _OUTPUT_SECRET_PATTERNS):
            return GuardrailDecision(False, SENSITIVE_RESPONSE, "sensitive_output", "possible_secret", 1.0)
        return GuardrailDecision(True, text)

    def redact(self, value: Any) -> str:
        text = str(value or "")
        for pattern in _OUTPUT_SECRET_PATTERNS:
            text = pattern.sub("[DATO PROTEGIDO]", text)
        return text


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default) if value is not None else default


_DEFAULT_GUARDRAILS = Guardrails()


def check(message: Any, entities: Any = None) -> GuardrailDecision:
    return _DEFAULT_GUARDRAILS.check(message, entities=entities)


def validate_output(answer: Any) -> GuardrailDecision:
    return _DEFAULT_GUARDRAILS.validate_output(answer)


__all__ = [
    "DOMAIN_RESPONSE", "SENSITIVE_RESPONSE", "GuardrailDecision", "Guardrails",
    "check", "validate_output",
]
