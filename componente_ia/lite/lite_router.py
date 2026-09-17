"""Ordered rules only; no model, scoring contract or web lookup."""

import re
from .lite_entities import extract_entities, normalize

_UNSAFE = re.compile(r"\b(?:contrasena|password|passwd|secretos?|tokens?|credenciales|api[_ ]?key|"
                     r"system prompt|prompt (?:del |de )?sistema|base de datos|clientes?|cedula|"
                     r"datos (?:privados|personales|bancarios)|numero de cuenta|cuenta bancaria|"
                     r"ignora|ignorar|instrucciones|olvida|revela|revelar|hackear|hackea|"
                     r"elecciones|presidente|politica|politicos?|futbol|horoscopo)\b|"
                     r"\.env\b|\b(?:select|drop|delete|insert|update)\s|<script|/etc/|\\users\\|"
                     r"(?:https?://|file://)", re.I)


def is_unsafe(text):
    return bool(_UNSAFE.search(normalize(text)))


def route_intent(text, entities=None, state=None):
    value = normalize(text)
    entities = entities if entities is not None else extract_entities(text)
    state = state or {}
    if is_unsafe(text):
        return "unsupported"
    if re.search(r"\b(?:pago|pagos|pagar|zelle|binance|tarjeta|efectivo|transferencia)\b", value):
        return "payment_methods"
    if entities.get("service") or re.search(r"\bservicios?\b", value):
        return "services"
    if re.search(r"\b(?:categorias?|que (?:productos|venden)|cuales productos)\b", value):
        return "categories"
    fitment = bool(re.search(r"\b(?:que (?:caucho|goma|neumatico|medida)|(?:le )?(?:sirve|sirven|compatible|compatibilidad)|usa|lleva|calza)\b", value))
    if (entities.get("vehicle_model") or entities.get("vehicle_brand")) and (fitment or " para " in value):
        return "vehicle_fitment"
    if not entities.get("tire_size") and (entities.get("vehicle_model") or entities.get("vehicle_brand")):
        return "vehicle_fitment"
    if state.get("vehicle_model") and not entities.get("tire_size") and (
            fitment or (entities.get("vehicle_year") and re.fullmatch(r"(?:del? |ano )?\d{4}[.!? ]*", value))):
        return "vehicle_followup"
    if fitment and not entities.get("tire_size") and (state.get("vehicle_model") or re.search(r"\b(?:vehiculo|carro|camion|camioneta|mi)\b", value)):
        return "vehicle_fitment"
    if entities.get("asks_cheapest"):
        return "cheapest"
    if entities.get("asks_most_stock"):
        return "most_stock"
    if entities.get("asks_price"):
        return "price"
    if entities.get("tire_size") or entities.get("rim"):
        return "inventory_by_size"
    if entities.get("tire_type"):
        return "inventory_by_type"
    if entities.get("brand") or entities.get("model"):
        return "inventory_by_brand"
    if re.search(r"\b(?:sedes?|sucursales?|ubicacion|ubicados|direccion|donde estan)\b", value):
        return "branches"
    if re.search(r"\b(?:stock|existencia|disponibilidad|cauchos?|neumaticos?|gomas?)\b", value):
        return "stock"
    if state.get("last_products") and (entities.get("asks_stock") or re.search(r"\b(?:primer[oa]|segund[oa]|tercer[oa]|ese|esa|comparar?|comparacion|diferencia)\b", value)):
        return "stock"
    if re.fullmatch(r"[¡!¿? .]*(?:hola|buenas|buenos dias|buenas tardes|buenas noches|saludos|hey|gracias)[¡!¿? .]*", value):
        return "greeting"
    return "unsupported"
