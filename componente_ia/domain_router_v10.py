from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping

CANONICAL_DOMAINS_V10 = (
    "tires", "services", "business", "orders", "security", "out_of_scope",
)

SEMANTIC_TEXT_NORMALIZATION_VERSION_V10 = "v10-semantic-text-2026.09.08.1"
_SEMANTIC_TOKEN_ALIASES_V10 = {
    "presio": "precio",
    "cauxos": "cauchos",
    "cauchoz": "cauchos",
    "neumaticoz": "neumaticos",
    "serbicios": "servicios",
    "price": "precio",
    "services": "servicios",
    "rinn": "rin",
    "xfa": "por favor",
    "pa": "para",
    "q": "que",
}
_SEMANTIC_ALIAS_PATTERN_V10 = re.compile(
    r"(?<![a-z0-9_])(?:" + "|".join(
        sorted(map(re.escape, _SEMANTIC_TOKEN_ALIASES_V10), key=len, reverse=True)
    ) + r")(?![a-z0-9_]|[-/.+]\d)"
)

def normalize_domain_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9./+_\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return _SEMANTIC_ALIAS_PATTERN_V10.sub(
        lambda match: _SEMANTIC_TOKEN_ALIASES_V10[match.group(0)],
        text,
    )

_STRUCTURAL_SIZE = re.compile(
    r"(?<![a-z0-9])(?:lt|p)?(?:\d{3}[ /.-]\d{2}\s*r?\s*\d{2}(?:\.5)?c?|"
    r"\d{3}\d{2}r\d{2}(?:\.5)?|\d{2}(?:\.\d{1,2})?x\d{1,2}(?:\.\d{1,2})?r?\d{2}(?:\.5)?|"
    r"\d{1,2}(?:\.\d{1,2})?r\d{2}(?:\.5)?|\d{3}r\d{2}(?:\.5)?c)(?![a-z0-9])"
)
_TIRE = re.compile(
    r"\b(?:cauchos?|gomas?|llantas?|neumaticos?|rin|aro|medida|a/t|h/t|r/t|m/t|"
    r"rustiquear|trocha|barro|off[ -]?road|indice de carga|velocidad)\b"
)
_SERVICE = re.compile(
    r"\b(?:alineacion|balanceo|rotacion|montaje|desmontaje|reparacion de cauchos|"
    r"cambio de aceite|filtros?|scanner|frenos?|suspension|tren delantero|"
    r"prueba de bateria|mantenimiento preventivo|servicios?(?: de taller)?)\b"
)
_SERVICE_DIRECTORY = re.compile(
    r"\b(?:que|cuales|lista(?:me)?|muestra(?:me)?|dime)\b.{0,40}"
    r"\bservicios?\b|"
    r"\bservicios?\s+(?:activos?|disponibles?|ofrecen|tienen|manejan)\b"
)
_BUSINESS = re.compile(
    r"\b(?:metodos? de pago|como (?:puedo )?pagar|pago movil|binance|zelle|"
    r"transferencia|tarjeta|efectivo|dolares?|bolivares?|categorias?|que productos|sedes?|sucursales?|"
    r"tipo de productos|productos (?:venden|tienen|manejan)|"
    r"horarios?|garantia|credito|flotas?|delivery|direccion|contacto)\b"
)
_BUSINESS_PRODUCT = re.compile(
    r"\b(?:tienen|venden|manejan|busco)\b.{0,24}\b(?:aceites?|lubricantes?|baterias?|filtros?|repuestos?)\b|"
    r"\b(?:aceites?|lubricantes?|baterias?|filtros?|repuestos?)\b.{0,24}\b(?:tienen|venden|manejan|hay)\b"
)
_ORDERS = re.compile(
    r"\b(?:mi pedido|mi orden|estado del pedido|estado de la orden|comprobante|"
    r"numero de pedido|referencia del pedido|factura)\b"
)
_OUTSIDE = re.compile(
    r"\b(?:politica nacional|elecciones|futbol|beisbol|pelicula|horoscopo|"
    r"receta de cocina|videojuego|poema|tarea escolar)\b"
)
_RETURN_TIRES = re.compile(
    r"\b(?:volviendo|regresando)\b.{0,30}\b(?:caucho|goma|llanta|rin|medida)\b|"
    r"^\s*(?:y\s+)?(?:el|la|los|las)?\s*(?:caucho|goma|llanta)s?\b"
)
_RETURN_SERVICES = re.compile(
    r"\b(?:volviendo|regresando)\b.{0,30}\b(?:servicio|taller|alineacion|balanceo)\b"
)
_FOLLOWUP = re.compile(
    r"^(?:y\s+)?(?:ese|esa|esos|esas|el primero|la primera|el mas barato|"
    r"cual|cuales|cuanto cuesta|cuanto vale|(?:el\s+)?precio|"
    r"(?:el\s+)?stock|cuantos quedan|cuantas unidades (?:hay|quedan)|"
    r"donde esta|en que sede|hay stock)\b"
)
_PRODUCT_BRANCH_FOLLOWUP = re.compile(
    r"^(?:y\s+)?(?:en (?:que|cual) (?:sede|sucursal)|donde esta disponible)\b"
)
_PRODUCT_BRANCH_QUERY = re.compile(
    r"\b(?:en (?:que|cual) (?:sede|sucursal)|donde (?:esta|tienen|hay)|"
    r"sede (?:tienen|disponible))\b"
)
_SESSION_RESET = re.compile(
    r"\b(?:reinicia|reiniciar|restablece|restablecer|borra|borrar|limpia|limpiar|olvida)\b"
    r".{0,28}\b(?:sesion|conversacion|contexto)\b|"
    r"\bolvida\s+lo\s+anterior\b|"
    r"\b(?:empieza|empecemos|comienza|comencemos)\b.{0,20}\b(?:consulta\s+)?nuev[oa]\b|"
    r"\b(?:empecemos|comencemos)\s+(?:de\s+)?nuevo\b"
)
_EXPLICIT_NEGATED_CLAUSE = re.compile(
    r"\b(?:no\s+(?:quiero|necesito|busco|deseo|me\s+interesan?|"
    r"emitas?|incluyas?|consultes?|uses?|muestres?|digas?|menciones?)|sin)\b"
    r"[^,;.!?]{0,96}",
    re.IGNORECASE,
)

def _without_explicitly_negated_clauses(value: Any) -> str:

    raw = unicodedata.normalize("NFKD", str(value or "").casefold())
    raw = "".join(char for char in raw if not unicodedata.combining(char))
    return normalize_domain_text(_EXPLICIT_NEGATED_CLAUSE.sub(" ", raw))

def without_explicitly_negated_clauses(value: Any) -> str:

    return _without_explicitly_negated_clauses(value)

@dataclass(frozen=True)
class DomainDecisionV10:
    domain: str | None
    confidence: float
    margin: float
    scores: dict[str, float]
    evidence: tuple[str, ...] = ()
    source: str = "deterministic"
    abstained: bool = False
    needs_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["evidence"] = list(self.evidence)
        return value

ResidualRouter = Callable[[str], Mapping[str, Any] | tuple[str, float] | None]

@dataclass
class DomainRouterV10:

    residual: ResidualRouter | None = None
    min_confidence: float = 0.62
    ambiguity_margin: float = 0.16
    _weights: dict[str, float] = field(default_factory=lambda: {
        "structural_size": 4.0,
        "lexical_primary": 3.0,
        "lexical_secondary": 1.25,
        "context_followup": 3.75,
        "entity": 2.0,
        "residual": 1.0,
    })

    @staticmethod
    def _state_domain(state: Mapping[str, Any] | None) -> str | None:
        domain = str((state or {}).get("active_domain") or "")
        return domain if domain in CANONICAL_DOMAINS_V10 else None

    @staticmethod
    def _entity_domains(entities: Mapping[str, Any] | None) -> set[str]:
        values = entities or {}
        result: set[str] = set()
        if any(values.get(key) not in (None, "", [], {}) for key in (
            "tire_size", "rim", "tire_type", "vehicle_brand", "vehicle_model",
            "truck_axle", "load_index", "speed_rating", "product_brand",
            "product_model",
        )):
            result.add("tires")
        if values.get("service"):
            result.add("services")
        if any(values.get(key) for key in ("payment_method", "branch")):
            result.add("business")
        return result

    @staticmethod
    def _confidence(top: float, total: float, margin: float) -> float:
        if top <= 0:
            return 0.0
        share = top / max(top, total)
        separation = margin / max(top, 1.0)
        return round(min(0.999, 0.58 * share + 0.42 * min(1.0, separation + 0.35)), 6)

    def route(
        self,
        message: Any,
        *,
        entities: Mapping[str, Any] | None = None,
        authoritative_entities: Mapping[str, Any] | None = None,
        state: Mapping[str, Any] | None = None,
        security_blocked: bool = False,
    ) -> DomainDecisionV10:
        text = normalize_domain_text(message)
        routing_text = without_explicitly_negated_clauses(message)
        scores = {domain: 0.0 for domain in CANONICAL_DOMAINS_V10}
        evidence: list[str] = []

        if routing_text != text:
            evidence.append("explicit_negation_removed")

        if security_blocked:
            scores["security"] = 100.0
            return DomainDecisionV10(
                "security", 1.0, 100.0, scores,
                ("input_guardrail:block",), "input_guardrail", False, False,
            )

        if _STRUCTURAL_SIZE.search(routing_text):
            scores["tires"] += self._weights["structural_size"]
            evidence.append("structural:tire_size")
        for domain, pattern in (
            ("tires", _TIRE), ("services", _SERVICE), ("business", _BUSINESS),
            ("orders", _ORDERS), ("out_of_scope", _OUTSIDE),
        ):
            matches = pattern.findall(routing_text)
            if matches:
                scores[domain] += self._weights["lexical_primary"]
                if len(matches) > 1:
                    scores[domain] += self._weights["lexical_secondary"]
                evidence.append(f"lexicon:{domain}")
        if _SERVICE_DIRECTORY.search(routing_text):

            scores["services"] += self._weights["structural_size"]
            evidence.append("structural:service_directory")
        if _BUSINESS_PRODUCT.search(routing_text):

            scores["business"] += (
                self._weights["lexical_primary"]
                + 2 * self._weights["lexical_secondary"]
            )
            evidence.append("lexicon:business_product")

        for domain in self._entity_domains(entities):
            scores[domain] += self._weights["entity"]
            evidence.append(f"entity:{domain}")

        for domain in self._entity_domains(authoritative_entities):
            scores[domain] += self._weights["structural_size"]
            evidence.append(f"authoritative_entity:{domain}")

        entity_values = entities or {}
        if (
            _PRODUCT_BRANCH_QUERY.search(routing_text)
            and any(entity_values.get(key) for key in ("product_brand", "product_model", "tire_size"))
        ):
            scores["tires"] += self._weights["structural_size"]
            evidence.append("relation:product_branch_inventory")

        previous = self._state_domain(state)
        if previous and _SESSION_RESET.search(routing_text):

            scores[previous] += self._weights["structural_size"]
            evidence.append(f"session_reset:{previous}")
        if _RETURN_TIRES.search(routing_text):
            scores["tires"] += self._weights["structural_size"]
            evidence.append("return:tires")
        elif _RETURN_SERVICES.search(routing_text):
            scores["services"] += self._weights["structural_size"]
            evidence.append("return:services")
        elif previous == "tires" and _PRODUCT_BRANCH_FOLLOWUP.search(routing_text):
            scores["tires"] += self._weights["structural_size"]
            evidence.append("product_branch_followup:tires")
        elif previous and _FOLLOWUP.search(routing_text) and max(scores.values()) <= 0:
            scores[previous] += self._weights["context_followup"]
            evidence.append(f"followup_context:{previous}")

        deterministic_max = max(scores.values())
        if self.residual is not None and deterministic_max < self._weights["structural_size"]:
            prediction = self.residual(routing_text)
            if isinstance(prediction, tuple) and len(prediction) >= 2:
                label, confidence = prediction[0], prediction[1]
            elif isinstance(prediction, Mapping):
                label = prediction.get("domain") or prediction.get("label")
                confidence = prediction.get("confidence", 0.0)
            else:
                label, confidence = None, 0.0

            if label in CANONICAL_DOMAINS_V10 and label != "security":
                try:
                    residual_confidence = float(confidence)
                except (TypeError, ValueError):
                    residual_confidence = 0.0
                if math.isfinite(residual_confidence) and residual_confidence >= 0.0:
                    scores[str(label)] += self._weights["residual"] * min(1.0, residual_confidence)
                    evidence.append(f"residual:{label}")

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        top_domain, top_score = ranked[0]
        second_score = ranked[1][1]
        margin = round(top_score - second_score, 6)
        confidence = self._confidence(top_score, sum(scores.values()), margin)

        if top_score <= 0:
            if previous and _FOLLOWUP.search(routing_text):
                return DomainDecisionV10(
                    previous, 0.72, 0.72, scores,
                    tuple(evidence + [f"state_only:{previous}"]), "state", False, False,
                )
            return DomainDecisionV10(
                None, 0.0, 0.0, scores, tuple(evidence),
                "abstention", True, True,
            )

        ambiguous = margin < self.ambiguity_margin or confidence < self.min_confidence
        if ambiguous and previous and _FOLLOWUP.search(routing_text):
            return DomainDecisionV10(
                previous, max(confidence, 0.68), margin, scores,
                tuple(evidence + [f"ambiguity_resolved_by_state:{previous}"]),
                "state", False, False,
            )
        if ambiguous:
            return DomainDecisionV10(
                None, confidence, margin, scores, tuple(evidence),
                "abstention", True, True,
            )
        source = "hybrid" if any(item.startswith("residual:") for item in evidence) else "deterministic"
        return DomainDecisionV10(
            top_domain, confidence, margin, scores, tuple(evidence), source, False, False,
        )

__all__ = [
    "CANONICAL_DOMAINS_V10", "DomainDecisionV10", "DomainRouterV10",
    "SEMANTIC_TEXT_NORMALIZATION_VERSION_V10", "normalize_domain_text",
    "without_explicitly_negated_clauses",
]
