"""Router hibrido de intenciones con reglas y puntuacion lexica ligera."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from componente_ia.entity_extractor import ExtractedEntities, extract, normalize_message


INTENTS = (
    "tire_inventory", "tire_size_lookup", "tire_recommendation", "tire_comparison",
    "tire_change_compatibility", "tire_technical_explanation", "truck_tire_advice",
    "service_list", "service_explanation", "service_recommendation", "service_price",
    "service_duration", "service_booking", "product_inventory", "product_recommendation",
    "product_price", "promotion", "branch", "business_hours", "payment", "order_status",
    "upload_receipt", "warranty", "credit", "fleet_service", "business_customer",
    "followup", "clarification", "out_of_scope", "sensitive_request",
    "business_info",
)


_OUT_OF_SCOPE = {
    "politica", "presidente", "elecciones", "futbol", "beisbol", "deporte", "deportes",
    "noticias", "farandula", "pelicula", "peliculas", "serie", "series", "receta",
    "novia", "novio", "horoscopo", "criptomoneda", "bitcoin",
}

_BUSINESS_WORDS = {
    "caucho", "cauchos", "llanta", "llantas", "goma", "gomas", "neumatico", "neumaticos",
    "rin", "aro", "vehiculo", "carro", "camioneta", "camion", "gandola", "autobus",
    "servicio", "servicios", "mantenimiento", "alineacion", "balanceo", "rotacion",
    "aceite", "filtro", "bateria", "freno", "scanner", "suspension", "repuesto",
    "producto", "productos", "pedido", "pago", "comprobante", "sucursal", "horario",
    "garantia", "credito", "promocion", "flota", "stock", "precio", "delivery",
}


@dataclass
class IntentResult:
    primary: str
    secondary: list[str] = field(default_factory=list)
    confidence: float = 0.0
    method: str = "rules+lexical"
    scores: dict[str, float] = field(default_factory=dict)
    needs_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __str__(self) -> str:
        return self.primary


def _entity(entities: Any, key: str, default: Any = None) -> Any:
    if entities is None:
        return default
    if isinstance(entities, dict):
        return entities.get(key, default)
    return getattr(entities, key, default)


def _context_value(context: Any, key: str, default: Any = None) -> Any:
    if isinstance(context, dict):
        return context.get(key, default)
    return getattr(context, key, default) if context is not None else default


def _has(text: str, pattern: str) -> bool:
    return bool(re.search(pattern, text, re.IGNORECASE))


class IntentRouter:
    """Combina reglas de precision y puntuacion de señales independientes."""

    def __init__(self, local_classifier: Any = None, semantic_retriever: Any = None):
        self.local_classifier = local_classifier
        self.semantic_retriever = semantic_retriever

    @staticmethod
    def _coerce_layer_result(value: Any, method: str) -> IntentResult | None:
        if isinstance(value, IntentResult):
            value.method = method
            return value if value.primary in INTENTS else None
        if isinstance(value, str):
            return IntentResult(value, confidence=0.7, method=method) if value in INTENTS else None
        if isinstance(value, (tuple, list)) and value:
            primary = value[0]
            confidence = float(value[2] if len(value) > 2 and isinstance(value[2], (int, float)) else value[1] if len(value) > 1 and isinstance(value[1], (int, float)) else 0.7)
            return IntentResult(primary, confidence=confidence, method=method) if primary in INTENTS else None
        if isinstance(value, dict):
            primary = value.get("primary") or value.get("intent") or value.get("label")
            if primary not in INTENTS:
                return None
            secondary = [item for item in value.get("secondary", []) if item in INTENTS and item != primary]
            return IntentResult(primary, secondary, float(value.get("confidence") or value.get("score") or 0.7), method=method)
        return None

    def _layered_fallback(self, text: str, entities: Any, context: Any) -> IntentResult | None:
        if self.local_classifier is not None:
            try:
                value = self.local_classifier.predict(text) if hasattr(self.local_classifier, "predict") else self.local_classifier.classify(text)
                result = self._coerce_layer_result(value, "local_model")
                if result and result.confidence >= 0.55:
                    return result
            except Exception:
                pass
        if self.semantic_retriever is not None:
            try:
                if hasattr(self.semantic_retriever, "classify"):
                    value = self.semantic_retriever.classify(text, entities=entities, context=context)
                else:
                    value = self.semantic_retriever.retrieve(text, limit=3)
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        value = value[0]
                result = self._coerce_layer_result(value, "semantic_retrieval")
                if result and result.confidence >= 0.55:
                    return result
            except Exception:
                pass
        return None

    def classify(self, message: Any, entities: Any = None, context: Any = None) -> IntentResult:
        text = normalize_message(message)
        entities = entities or extract(message)
        tokens = set(_entity(entities, "tokens", []) or [])
        scores = {intent: 0.0 for intent in INTENTS}

        sensitive = _has(
            text,
            r"\b(?:api[_ -]?key|contrasena|password|credencial(?:es)?|token(?:es)?|cookie(?:s)?|"
            r"variables? de entorno|\.env|dump|logs? internos?|consulta sql|ruta interna|datos? de clientes?)\b",
        ) or _has(text, r"\b(?:ignora|omite|olvida)\b.{0,35}\b(?:reglas|instrucciones|sistema|guardrails?)\b")
        if sensitive:
            return IntentResult("sensitive_request", confidence=0.995, scores={"sensitive_request": 1.0})

        inherited = set(_context_value(context, "inherited_fields", []) or [])
        has_business = bool(tokens & _BUSINESS_WORDS) or any(
            _entity(entities, key) for key in ("make", "model", "year", "requested_tire_size", "current_tire_size", "service", "product_category")
            if key not in inherited
        )
        if tokens & _OUT_OF_SCOPE and not has_business:
            return IntentResult("out_of_scope", confidence=0.99, scores={"out_of_scope": 1.0})

        bare_followup = bool(_entity(entities, "followup")) and not any(
            _entity(entities, key) for key in (
                "make", "model", "year", "requested_tire_size", "current_tire_size",
                "requested_rim", "current_rim", "tire_type", "service", "product_category",
            )
        )
        if bare_followup:
            last_intent = _context_value(context, "last_intent")
            if last_intent in INTENTS and last_intent not in {"out_of_scope", "sensitive_request"}:
                return IntentResult(last_intent, ["followup"], 0.78, method="context_followup", scores={last_intent: 0.78, "followup": 0.7})
            return IntentResult("followup", confidence=0.8, method="followup_rule", scores={"followup": 0.8}, needs_clarification=True)


        if _has(text, r"\b(?:subir|adjuntar|cargar|enviar)\b.{0,30}\bcomprobante\b|\bcomprobante\b.{0,20}\b(?:pago|transferencia)\b"):
            scores["upload_receipt"] += 10
        if _has(text, r"\b(?:estado|estatus|rastrear|seguimiento|revis\w*|consultar|donde va|como)\b.{0,30}\b(?:pedido|orden)\b") or _entity(entities, "order_reference"):
            scores["order_status"] += 9
        if _has(text, r"\b(?:metodo|forma|como)\w*\b.{0,20}\bpag|\b(?:pago movil|transferencia|efectivo|tarjeta|divisas)\b"):
            scores["payment"] += 8
        if "garantia" in tokens:
            scores["warranty"] += 14
        if tokens & {"credito", "financiamiento", "financiar"}:
            scores["credit"] += 9
        if tokens & {"promocion", "promociones", "oferta", "ofertas", "descuento"}:
            scores["promotion"] += 9
        if tokens & {"sucursal", "sucursales", "ubicacion", "ubicados", "direccion", "queda"}:
            scores["branch"] += 8
        if tokens & {"horario", "horarios", "abren", "cierran"}:
            scores["business_hours"] += 9
        if tokens & {"empresa", "empresas", "corporativo", "mayorista"}:
            scores["business_customer"] += 8
        if tokens & {"flota", "flotas"}:
            scores["fleet_service"] += 9
        if (
            tokens & {"delivery", "despacho", "envio", "contacto", "reservas", "devolucion", "devoluciones", "reclamo", "reclamos", "apartar"}
            or _has(text, r"\b(?:como|donde)\b.{0,20}\b(?:hago|realizo|creo)\b.{0,20}\b(?:pedido|compra)\b")
            or _has(text, r"\b(?:llevar|traer)\b.{0,25}\b(?:mis|propios|propias)\b.{0,20}\b(?:cauchos|productos|repuestos|piezas)\b")
            or _has(text, r"\b(?:puedo|quiero)\b.{0,15}\b(?:apartar|reservar)\b.{0,20}\b(?:producto|caucho|repuesto)\b")
        ):
            scores["business_info"] += 10

        service = _entity(entities, "service")
        service_context = bool(service or tokens & {
            "servicio", "servicios", "alineacion", "balanceo", "rotacion", "montaje",
            "scanner", "mantenimiento", "frenos", "suspension", "inyectores",
        })
        if service_context:
            if _has(text, r"\b(?:que|cuales|lista|todos)\b.{0,25}\bservicios\b|^servicios$"):
                scores["service_list"] += 9
            if _has(text, r"\b(?:como funciona|que incluye|que hacen|explica|diferencia)\b"):
                scores["service_explanation"] += 9
            if _has(text, r"\b(?:(?:que|cual) servicio\b|que necesito\b|recomiend\w*)") or tokens & {"vibra", "vibracion", "jala", "desvia", "chilla"}:
                scores["service_recommendation"] += 10
            if _entity(entities, "asks_price"):
                scores["service_price"] += 10
            if tokens & {"tarda", "demora", "duracion", "tiempo"}:
                scores["service_duration"] += 10
            if tokens & {"cita", "agendar", "reservar", "reserva"}:
                scores["service_booking"] += 10
            if max(scores[name] for name in ("service_list", "service_explanation", "service_recommendation", "service_price", "service_duration", "service_booking")) == 0:
                scores["service_explanation"] += 5

        tire_context = bool(
            _entity(entities, "product_category") == "tires"
            or _entity(entities, "requested_tire_size") or _entity(entities, "current_tire_size")
            or _entity(entities, "requested_rim") or _entity(entities, "current_rim")
            or _entity(entities, "tire_type") or _entity(entities, "load_index") or _entity(entities, "speed_rating")
            or tokens & {"rin", "aro"}
        )
        vehicle_context = bool(_entity(entities, "make") or _entity(entities, "model"))
        truck_context = _entity(entities, "vehicle_type") in {
            "camion liviano", "camion mediano", "camion pesado", "gandola", "autobus", "vehiculo comercial",
        } or bool(tokens & {"gandola", "camion", "autobus", "remolque", "eje"})

        non_tire_product = _entity(entities, "product_category") not in {None, "tires"}
        recommendation_without_tire_word = bool(_entity(entities, "usage") or _entity(entities, "budget")) and not service_context and not non_tire_product and not (tokens & {"flota", "flotas", "empresa", "empresas"})
        if tire_context or truck_context or recommendation_without_tire_word or (vehicle_context and not non_tire_product):
            if truck_context:
                scores["truck_tire_advice"] += 18
            if len(_entity(entities, "tire_sizes", []) or []) >= 2 or _has(text, r"\b(?:le puedo poner|puedo cambiar|paso de|en vez de|compatible)\b"):
                scores["tire_change_compatibility"] += 17
            if _has(text, r"\b(?:que significa|significa|explic\w*|indice de carga|indice de velocidad|diametro|offset|dot|psi|load range)\b"):
                scores["tire_technical_explanation"] += 16
            tire_type_comparison = len(_entity(entities, "tire_sizes", []) or []) < 2 and (
                _entity(entities, "asks_comparison") or _has(text, r"\b(?:mejor|diferencia|compara\w*)\b.{0,35}\b(?:a/?t|h/?t|r/?t|m/?t)\b")
            )
            if tire_type_comparison:
                scores["tire_comparison"] += 17
            lookup_words = _has(text, r"\b(?:que|cual|medida|rin|aro)\b.{0,25}\b(?:usa|lleva|corresponde|original|oem|recomiendas?)\b") or _has(text, r"\b(?:que cauchos?|que llantas?)\s+(?:usa|lleva)\b")
            if vehicle_context and lookup_words:
                scores["tire_size_lookup"] += 10
            recommendation_signals = bool(
                _entity(entities, "tire_type") or _entity(entities, "usage") or _entity(entities, "budget")
                or tokens & {"recomienda", "recomiendas", "recomendacion", "silencioso", "economico", "premium"}
            )
            if recommendation_signals:
                scores["tire_recommendation"] += 14
            inventory_signals = bool(_entity(entities, "asks_stock") or _has(text, r"\b(?:tienen|hay|inventario|disponible|stock|marcas)\b"))
            if inventory_signals or ((_entity(entities, "requested_tire_size") or _entity(entities, "requested_rim")) and not vehicle_context):
                scores["tire_inventory"] += 9
            if _entity(entities, "asks_price"):
                scores["product_price"] += 8
                scores["tire_inventory"] += 3
            if max(scores[name] for name in (
                "tire_inventory", "tire_size_lookup", "tire_recommendation", "tire_comparison",
                "tire_change_compatibility", "tire_technical_explanation", "truck_tire_advice",
            )) == 0:
                scores["tire_recommendation" if vehicle_context else "tire_inventory"] += 5

        product_context = bool(_entity(entities, "product_category") and _entity(entities, "product_category") != "tires") or bool(tokens & {"producto", "productos", "repuesto", "repuestos"})
        if product_context:
            if _entity(entities, "asks_price"):
                scores["product_price"] += 10
            if _entity(entities, "asks_stock") or tokens & {"venden", "catalogo", "productos"}:
                scores["product_inventory"] += 9
            if vehicle_context or tokens & {"recomienda", "recomiendas", "usa", "lleva"}:
                scores["product_recommendation"] += 8
            if max(scores[name] for name in ("product_inventory", "product_recommendation", "product_price")) == 0:
                scores["product_inventory"] += 5

        ranked = sorted(scores.items(), key=lambda item: (-item[1], INTENTS.index(item[0])))
        positive = [(name, score) for name, score in ranked if score > 0]
        followup = bool(_entity(entities, "followup"))
        if not positive and followup:
            last_intent = _context_value(context, "last_intent")
            if last_intent in INTENTS and last_intent not in {"out_of_scope", "sensitive_request"}:
                return IntentResult(last_intent, ["followup"], 0.78, scores={last_intent: 0.78, "followup": 0.7})
            return IntentResult("followup", confidence=0.72, scores={"followup": 0.72}, needs_clarification=True)
        if not positive:
            layered = self._layered_fallback(text, entities, context)
            if layered:
                return layered
            if not text or tokens <= {"hola", "buenas", "buenos", "dias", "tardes", "noches", "gracias"}:
                return IntentResult("clarification", confidence=0.8, method="fallback", scores={"clarification": 0.8}, needs_clarification=True)
            return IntentResult("out_of_scope" if not has_business else "clarification", confidence=0.9 if not has_business else 0.65, method="fallback", needs_clarification=has_business)

        primary, top_score = positive[0]
        secondary = [name for name, score in positive[1:] if score >= max(5.0, top_score * 0.55) and name != primary][:4]
        if followup and primary != "followup":
            secondary.append("followup")
        confidence = min(0.99, 0.58 + top_score * 0.035)
        needs_clarification = primary in {"tire_size_lookup", "tire_recommendation"} and not _entity(entities, "year") and not _entity(entities, "requested_tire_size")
        method = "high_precision_rules" if top_score >= 14 else "hybrid_rules_lexical"
        return IntentResult(primary, list(dict.fromkeys(secondary)), confidence, method=method, scores={name: round(score, 3) for name, score in positive}, needs_clarification=needs_clarification)


_DEFAULT_ROUTER = IntentRouter()


def classify(message: Any, entities: Any = None, context: Any = None) -> IntentResult:
    return _DEFAULT_ROUTER.classify(message=message, entities=entities, context=context)


__all__ = ["INTENTS", "IntentResult", "IntentRouter", "classify"]
