import hashlib
import logging
import math
import os
import time
from datetime import datetime, timezone

from componente_ia.automotive_entities import (
    AutomotiveEntities,
    BUSINESS_TERMS,
    SERVICE_TERMS,
    SERVICE_SYMPTOMS,
    MODEL_MAKE,
    detect_intent_hint,
    extract_entities,
    extract_sizes,
    is_business_related,
    normalize_text,
)
from componente_ia.catalog_retriever import (
    CatalogSnapshot,
    CatalogProvider,
    active_stock,
    find_exact_size_products,
    find_rim_products,
    find_services,
    int_value,
    product_line,
    rank_tire_candidates,
    search_category,
    search_tire_text,
    serialize_match,
)
from componente_ia.session_memory import SessionMemory
from componente_ia.source_quality import evaluate_source
from componente_ia.web_search import WebSearchService, extract_tire_sizes_from_sources


logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = int(os.getenv('ASSISTANT_MAX_MESSAGE_LENGTH', '1000'))
LOCAL_RESPONSE_LIMIT = int(os.getenv('ASSISTANT_RESPONSE_LIMIT', '1200'))


TRAINING_DATA = [
    ('tienen cauchos rin 15', 'inventario_cauchos'),
    ('hay cauchos r17 disponibles', 'inventario_cauchos'),
    ('busco llantas aro 16', 'inventario_cauchos'),
    ('tienen 265/65r17', 'inventario_cauchos'),
    ('cual es el caucho mas economico', 'inventario_cauchos'),
    ('que cauchos utiliza un corolla 2016', 'medida_caucho'),
    ('que caucho usa una hilux 2021', 'medida_caucho'),
    ('medida de caucho para toyota 4runner', 'medida_caucho'),
    ('mi carro es una toyota hilux y necesito cauchos todo terreno', 'recomendacion_cauchos'),
    ('cauchos all terrain buenos', 'recomendacion_cauchos'),
    ('que llantas todo terreno recomiendas', 'recomendacion_cauchos'),
    ('cual es mejor para carretera y tierra', 'comparacion_cauchos'),
    ('mi volante vibra despues de 80 km/h', 'servicio'),
    ('necesito balancear mis cauchos', 'servicio'),
    ('servicio de alineacion y balanceo', 'servicio'),
    ('cambio de aceite', 'servicio'),
    ('pastillas de freno', 'producto'),
    ('revision de frenos', 'servicio'),
    ('bateria para carro', 'producto'),
    ('estado de mi pedido', 'pedido'),
    ('como subo el comprobante de pago', 'pedido'),
    ('precio de producto', 'producto'),
    ('sucursales disponibles', 'sucursal'),
]

for rim in range(13, 23):
    TRAINING_DATA.extend([
        (f'tienen cauchos rin {rim}', 'inventario_cauchos'),
        (f'hay llantas aro {rim}', 'inventario_cauchos'),
        (f'cauchos r{rim} disponibles', 'inventario_cauchos'),
    ])

for model in ('hilux', 'corolla', '4runner', 'fortuner', 'prado', 'yaris', 'rav4', 'terios', 'grand vitara'):
    TRAINING_DATA.extend([
        (f'que caucho usa una {model}', 'medida_caucho'),
        (f'medida de caucho para {model}', 'medida_caucho'),
        (f'necesito cauchos para {model}', 'recomendacion_cauchos'),
    ])


class LightIntentClassifier:
    def __init__(self, samples, buckets=512):
        self.samples = [(normalize_text(text), label) for text, label in samples]
        self.labels = sorted({label for _, label in self.samples})
        self.buckets = buckets
        self.weights = {label: [0.0] * buckets for label in self.labels}
        self.bias = {label: 0.0 for label in self.labels}
        self.train()

    def _hash(self, value):
        digest = hashlib.blake2b(value.encode('utf-8'), digest_size=4).digest()
        return int.from_bytes(digest, 'big') % self.buckets

    def features(self, text):
        tokens = normalize_text(text).split()
        feats = {}
        for token in tokens:
            feats[self._hash(f'w:{token}')] = feats.get(self._hash(f'w:{token}'), 0.0) + 1.0
            compact = f" {token} "
            for size in (3, 4):
                for idx in range(max(0, len(compact) - size + 1)):
                    key = self._hash(f'c:{compact[idx:idx + size]}')
                    feats[key] = feats.get(key, 0.0) + 0.25
        for left, right in zip(tokens, tokens[1:]):
            key = self._hash(f'b:{left}_{right}')
            feats[key] = feats.get(key, 0.0) + 1.0
        return feats

    def scores(self, features):
        result = {}
        for label in self.labels:
            weights = self.weights[label]
            result[label] = self.bias[label] + sum(weights[idx] * value for idx, value in features.items())
        return result

    def predict(self, text):
        features = self.features(text)
        if not features:
            return 'consulta', None, 0.0
        scores = self.scores(features)
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top, top_score = ordered[0]
        second, second_score = ordered[1] if len(ordered) > 1 else (None, 0.0)
        margin = top_score - second_score
        confidence = max(0.05, min(0.98, 1.0 / (1.0 + math.exp(-margin / 4.0))))
        return top, second, confidence

    def train(self):
        for _ in range(28):
            for text, label in self.samples:
                features = self.features(text)
                prediction, _, _ = self.predict(text)
                if prediction == label:
                    continue
                for idx, value in features.items():
                    self.weights[label][idx] += value
                    self.weights[prediction][idx] -= value
                self.bias[label] += 0.5
                self.bias[prediction] -= 0.5


LOCAL_FITMENT_SOURCE = 'referencia local curada; validar manual o etiqueta de puerta antes de vender'
LOCAL_FITMENT_UPDATED_AT = '2026-06-16'

LOCAL_FITMENT = [
    {'make': 'toyota', 'model': 'hilux', 'start': 2016, 'end': 2023, 'version': 'varias', 'sizes': ['225/70R17', '265/65R17', '265/60R18'], 'certainty': 0.68, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'varia por version y rin'},
    {'make': 'toyota', 'model': '4runner', 'start': 2010, 'end': 2024, 'version': 'varias', 'sizes': ['265/70R17', '245/60R20'], 'certainty': 0.78, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'rin 17 comun; Limited suele usar rin 20'},
    {'make': 'toyota', 'model': 'corolla', 'start': 2014, 'end': 2019, 'version': 'LE/S/XRS segun mercado', 'sizes': ['195/65R15', '205/55R16', '215/45R17'], 'certainty': 0.7, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'depende de version LE/S/XRS y rin instalado'},
    {'make': 'toyota', 'model': 'fortuner', 'start': 2016, 'end': 2023, 'version': 'varias', 'sizes': ['265/65R17', '265/60R18'], 'certainty': 0.68, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'varia por version'},
    {'make': 'toyota', 'model': 'prado', 'start': 2010, 'end': 2023, 'version': 'varias', 'sizes': ['265/65R17', '265/60R18'], 'certainty': 0.62, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'validar version'},
    {'make': 'toyota', 'model': 'yaris', 'start': 2014, 'end': 2022, 'version': 'varias', 'sizes': ['175/65R14', '185/60R15'], 'certainty': 0.62, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'validar carroceria y rin'},
    {'make': 'chevrolet', 'model': 'aveo', 'start': 2005, 'end': 2018, 'version': 'varias', 'sizes': ['185/60R14', '185/55R15'], 'certainty': 0.62, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'validar version'},
    {'make': 'ford', 'model': 'explorer', 'start': 2011, 'end': 2019, 'version': 'varias', 'sizes': ['245/60R18', '255/50R20'], 'certainty': 0.62, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'validar version'},
    {'make': 'suzuki', 'model': 'grand vitara', 'start': 2006, 'end': 2015, 'version': 'varias', 'sizes': ['225/65R17', '235/60R16'], 'certainty': 0.6, 'source': LOCAL_FITMENT_SOURCE, 'updated_at': LOCAL_FITMENT_UPDATED_AT, 'note': 'validar rin actual'},
]

TECHNICAL_TERMS = {
    'presion', 'psi', 'dot', 'fecha', 'indice', 'velocidad', 'xl',
    'offset', 'diametro', 'direccional', 'direccionales', 'asimetrico',
    'asimetricos', 'aquaplaning', 'hidroplaneo', 'remolque', 'carga',
    'remolcar', 'remolcando', 'hombro', 'reparado', 'reparacion',
    'consumo', 'comfort', 'confort', 'load', 'range', 'rango',
}


class AssistantEngine:
    def __init__(self, catalog_provider=None, search_service=None, memory=None, classifier=None):
        self.started_at = time.time()
        self.catalog_provider = catalog_provider or CatalogProvider()
        self.search_service = search_service or WebSearchService()
        self.memory = memory or SessionMemory()
        self.classifier = classifier or LightIntentClassifier(TRAINING_DATA)

    def handle(self, question, session_id=None, client_history=None, request_id=None, catalog_provider=None, search_provider=None):
        started = time.perf_counter()
        stage_ms = {}
        raw = str(question or '').strip()
        if not raw:
            return {'status': 'error', 'message': 'Mensaje requerido.'}, 400
        if len(raw) > MAX_MESSAGE_LENGTH:
            return {'status': 'error', 'message': f'La pregunta no puede superar {MAX_MESSAGE_LENGTH} caracteres.'}, 400

        t = time.perf_counter()
        original_entities = extract_entities(raw)
        state = self.memory.get(session_id, client_history)
        entities = self.memory.merge(original_entities, state)
        if state and not original_entities.followup:
            entities.intent_hint = detect_intent_hint(entities)
        stage_ms['entities'] = self._elapsed(t)

        t = time.perf_counter()
        model_intent, second_intent, model_confidence = self.classifier.predict(entities.clean)
        intent = self._choose_intent(entities, model_intent)
        stage_ms['intent'] = self._elapsed(t)

        if original_entities.followup and original_entities.tire_type and state:
            intent = 'inventario_cauchos'
        if original_entities.followup and (original_entities.rim or original_entities.tire_size) and entities.has_vehicle():
            intent = 'medida_caucho'

        if self._is_sensitive_request(raw, original_entities):
            return self._base_payload(
                'Solo puedo ayudarte con productos, servicios, mantenimiento, cauchos, compras, pagos o pedidos de Transalca.',
                'fuera_de_negocio',
                model_intent,
                second_intent,
                0.98,
                [],
                [],
                None,
                web_available=self._web_health(search_provider),
                needs_clarification=False,
                stage_ms=stage_ms,
                started=started,
                request_id=request_id,
            ), 200

        if intent == 'seguimiento' and self._has_actionable_entities(original_entities):
            if entities.rim or entities.tire_size or entities.tire_type:
                intent = 'medida_caucho' if entities.has_vehicle() and (entities.rim or entities.tire_size) else 'inventario_cauchos'
            elif entities.has_vehicle():
                intent = 'medida_caucho'

        if intent == 'seguimiento' and state and not state.get('last_candidates') and entities.has_vehicle():
            intent = 'medida_caucho'

        if self._is_candidate_followup(original_entities, state):
            return self._handle_followup(entities, state, model_intent, second_intent, model_confidence, stage_ms, started)

        if intent == 'seguimiento' and entities.followup and state and not self._has_actionable_entities(original_entities):
            return self._handle_followup(entities, state, model_intent, second_intent, model_confidence, stage_ms, started)

        t = time.perf_counter()
        try:
            catalog = (catalog_provider or self.catalog_provider).load()
        except Exception:
            logger.exception('assistant.catalog.provider_failed', extra={'request_id': request_id})
            catalog = CatalogSnapshot(catalog_available=False, product_error='CatalogProviderError', service_error='CatalogProviderError')
        stage_ms['catalog'] = self._elapsed(t)

        contextual = self._contextual_followup(raw, entities, state)
        if contextual and not entities.has_vehicle() and any(marker in normalize_text(raw, autocorrect=False) for marker in ('sesion', 'contexto', 'separad', 'no mezcles', '4x2', '4x4')):
            return self._base_payload(
                contextual,
                'seguimiento',
                model_intent,
                second_intent,
                0.58,
                [],
                [],
                catalog,
                web_available=self._web_health(search_provider),
                needs_clarification=True,
                stage_ms=stage_ms,
                started=started,
                request_id=request_id,
            ), 200

        if not is_business_related(entities) and not self._catalog_mentions(entities, catalog):
            if contextual:
                return self._base_payload(
                    contextual,
                    'seguimiento',
                    model_intent,
                    second_intent,
                    0.58,
                    [],
                    [],
                    catalog,
                    web_available=self._web_health(search_provider),
                    needs_clarification=True,
                    stage_ms=stage_ms,
                    started=started,
                    request_id=request_id,
                ), 200
            return self._base_payload(
                'Solo puedo ayudarte con productos, servicios, mantenimiento, cauchos, compras, pagos o pedidos de Transalca.',
                'fuera_de_negocio',
                model_intent,
                second_intent,
                0.96,
                [],
                [],
                catalog,
                web_available=self._web_health(search_provider),
                needs_clarification=False,
                stage_ms=stage_ms,
                started=started,
                request_id=request_id,
            ), 200

        sources = []
        web_available = self._web_health(search_provider)
        if intent in {'inventario_cauchos', 'medida_caucho', 'recomendacion_cauchos', 'comparacion_cauchos'}:
            response = self._handle_tire(entities, intent, catalog, search_provider or self.search_service, stage_ms)
            answer, matches, sources, needs_clarification, confidence = response
        elif intent == 'servicio':
            answer, matches, needs_clarification, confidence = self._handle_service(entities, catalog)
        elif intent == 'pedido':
            answer, matches, needs_clarification, confidence = self._handle_order(entities)
        elif intent == 'sucursal':
            answer, matches, needs_clarification, confidence = self._handle_sucursal()
        else:
            answer, matches, needs_clarification, confidence = self._handle_catalog_general(entities, catalog)

        memory_candidates = [self._memory_candidate(entry) for entry in matches]
        self.memory.update(session_id, entities, memory_candidates, answer)

        payload = self._base_payload(
            answer,
            intent,
            model_intent,
            second_intent,
            max(confidence, model_confidence * 0.7),
            [serialize_match(entry['item'], entry.get('compatibility'), entry.get('score')) for entry in self._actionable_matches(matches)],
            sources,
            catalog,
            web_available=web_available,
            needs_clarification=needs_clarification,
            stage_ms=stage_ms,
            started=started,
            request_id=request_id,
            entities=entities,
            original_entities=original_entities,
            state=state,
            inventory_query=self._inventory_query(entities),
            context_replaced=self._context_replaced(original_entities, state),
            web_reason=self._web_reason(entities, intent, bool(sources), 'web' in stage_ms),
        )
        return payload, 200

    def answer_user_message(self, message, session_id=None, history=None):
        return self.handle(message, session_id=session_id, client_history=history)

    def _actionable_matches(self, matches):
        visible = []
        for entry in matches or []:
            item = entry.get('item') or {}
            if item.get('kind') == 'producto' and int_value(item.get('stock')) <= 0:
                continue
            visible.append(entry)
        return visible

    def _choose_intent(self, entities, model_intent):
        hint = entities.intent_hint
        if entities.tokens & TECHNICAL_TERMS:
            return 'recomendacion_cauchos'
        if hint != 'consulta':
            return hint
        if self._category_from_tokens(entities.tokens) and not (entities.tokens & SERVICE_TERMS):
            symptom_words = set().union(*(words for words in SERVICE_SYMPTOMS.values() if words))
            if not (entities.tokens & symptom_words):
                return 'producto'
        if model_intent in {'inventario_cauchos', 'medida_caucho', 'recomendacion_cauchos', 'comparacion_cauchos', 'servicio', 'pedido'}:
            return model_intent
        return hint

    def _has_actionable_entities(self, entities):
        return bool(
            entities
            and (
                entities.tire_size
                or entities.rim
                or entities.tire_type
                or entities.has_vehicle()
            )
        )

    def _is_candidate_followup(self, entities, state):
        if not state or not state.get('last_candidates') or not entities:
            return False
        if self._has_actionable_entities(entities):
            return False
        if entities.tokens & {'medida', 'talla'}:
            return False
        if (entities.tokens & {'precio', 'precios', 'stock', 'disponible', 'disponibles'}) and (
            entities.tokens & {'viejo', 'vieja', 'actual', 'actualizado', 'actualizada', 'nuevo', 'nueva'}
        ):
            return False
        followup_tokens = {
            'stock', 'disponible', 'disponibles', 'hay', 'quedan',
            'precio', 'precios', 'barato', 'economico', 'menos',
            'primero', 'primera', 'ese', 'esa', 'sirve', 'lluvia',
            'tierra', 'barro', 'carretera', 'autopista', 'cual',
            'mejor', 'recomiendas', 'recomienda',
        }
        return bool(entities.followup or entities.tokens & followup_tokens)

    def _handle_tire(self, entities, intent, catalog, search_service, stage_ms):
        fitment = self._local_fitment(entities)
        technical_note = self._technical_note(entities)
        sources = []
        web_sizes = []
        expected_make = MODEL_MAKE.get(entities.model)
        if entities.make and expected_make and expected_make != entities.make:
            return (
                self._limit(
                    f"Veo datos contradictorios: la marca indicada es {entities.make}, pero el modelo {entities.model} suele asociarse a {expected_make}. "
                    "No tengo una medida validada con esos datos; necesito confirmar marca, modelo, ano y rin antes de recomendar."
                ),
                [],
                sources,
                True,
                0.4,
            )
        should_search_web = self._should_search_web(entities, fitment)
        if should_search_web:
            t = time.perf_counter()
            sources = self._web_fitment_sources(entities, search_service)
            extracted = extract_tire_sizes_from_sources(sources)
            web_sizes = [size for size, _, _ in extracted[:4]]
            stage_ms['web'] = self._elapsed(t)
        web_note = self._web_reference_note(sources, should_search_web, search_service)

        compatible_sizes = self._compatible_sizes(entities, fitment, web_sizes)
        needs_clarification = self._needs_tire_clarification(entities, compatible_sizes)
        matches = []

        if entities.tire_size:
            matches = rank_tire_candidates(catalog.products, entities, compatible_sizes=[entities.tire_size.normalized], limit=5)
            answer = self._answer_exact_size(entities, matches, fitment, sources, catalog)
            answer = self._append_note(self._append_note(answer, web_note), technical_note)
            return answer, matches, sources, False, 0.9 if matches else 0.72

        if compatible_sizes:
            matches = rank_tire_candidates(
                catalog.products,
                entities,
                compatible_sizes=compatible_sizes,
                allow_rim_possible=False,
                limit=5,
            )
            if not matches and entities.rim:
                matches = rank_tire_candidates(catalog.products, entities, compatible_sizes=None, allow_rim_possible=True, limit=5)
            answer = self._answer_fitment(entities, compatible_sizes, matches, fitment, sources, needs_clarification, catalog)
            answer = self._append_note(self._append_note(answer, web_note), technical_note)
            return answer, matches, sources, needs_clarification, 0.82 if compatible_sizes else 0.55

        if entities.rim:
            matches = rank_tire_candidates(catalog.products, entities, compatible_sizes=None, allow_rim_possible=True, limit=5)
            answer = self._answer_rim_only(entities, matches, catalog)
            answer = self._append_note(self._append_note(answer, web_note), technical_note)
            return answer, matches, sources, not bool(matches), 0.62 if matches else 0.45

        if entities.make and not entities.model and not entities.tire_size and not entities.rim:
            return (
                self._answer_make_only(entities, catalog, web_note, technical_note),
                [],
                sources,
                True,
                0.52,
            )

        if entities.has_vehicle() and not (fitment or web_sizes):
            vehicle = self._vehicle_label(entities)
            inventory_note = (
                'No pude verificar inventario en base de datos.'
                if not catalog.catalog_available
                else 'No cruce inventario porque falta una medida o rin confirmado.'
            )
            return (
                self._limit(
                    f"No tengo una medida validada para {vehicle} con los datos disponibles. "
                    f"Para validar la compatibilidad, revisa manual o etiqueta de puerta y necesito que me confirmes ano, version, rin o medida completa. "
                    "Si sabes solo el rin actual, puedo filtrar cauchos por rin en inventario. "
                    f"Inventario Transalca: {inventory_note} {web_note} {technical_note}"
                ),
                [],
                sources,
                True,
                0.42,
            )

        if technical_note:
            return (
                self._limit(technical_note + f' Si quieres que cruce inventario, dime medida completa o rin confirmado. {web_note}'),
                [],
                sources,
                True,
                0.62,
            )

        if entities.tokens & {'codigo', 'tir'}:
            matches = search_tire_text(catalog.products, entities.tokens, limit=5)
            if matches:
                answer = self._answer_generic_tires(entities, matches)
                answer = self._append_note(self._append_note(answer, web_note), technical_note)
                return answer, matches, sources, False, 0.68

        matches = rank_tire_candidates(catalog.products, entities, compatible_sizes=None, allow_rim_possible=False, limit=5)
        if matches:
            answer = self._answer_generic_tires(entities, matches)
            answer = self._append_note(self._append_note(answer, web_note), technical_note)
            return answer, matches, sources, False, 0.58
        catalog_note = ' No pude verificar el catalogo en este momento.' if not catalog.catalog_available else ''
        return (
            'Para recomendar cauchos con precision necesito al menos la medida completa, el rin o el vehiculo con ano. '
            'Si buscas uso mixto, normalmente conviene A/T; para carretera H/T; para barro fuerte M/T. '
            f'Valida siempre la medida en manual o etiqueta de puerta antes de comprar.{catalog_note} {web_note}',
            [],
            sources,
            True,
            0.38,
        )

    def _answer_exact_size(self, entities, matches, fitment, sources, catalog):
        size = entities.tire_size.normalized
        fit_sizes = sorted({size_item for entry in fitment for size_item in entry['sizes']}) if fitment else []
        requested_not_confirmed = bool(entities.has_vehicle() and fit_sizes and size not in fit_sizes)
        exact_stock = [entry for entry in matches if int_value(entry['item'].get('stock')) > 0]
        if entities.tire_type:
            typed_stock = [entry for entry in exact_stock if entry['item'].get('tire_type') == entities.tire_type]
            if typed_stock:
                exact_stock = typed_stock
            elif exact_stock:
                alternatives = '; '.join(product_line(entry['item']) for entry in exact_stock[:3])
                return self._limit(
                    f"Inventario Transalca: no veo stock positivo de {size} tipo {entities.tire_type}. "
                    f"En esa misma medida aparecen alternativas que no son {entities.tire_type}: {alternatives}. "
                    "No las trato como equivalentes si pediste ese tipo; valida uso, carga y velocidad antes de comprar."
                )
        if exact_stock:
            lines = '; '.join(product_line(entry['item']) for entry in exact_stock[:3])
            reason = self._usage_reason(entities)
            if entities.has_vehicle() and not fitment:
                vehicle = self._vehicle_label(entities)
                return self._limit(
                    f"Inventario Transalca: la medida {size} aparece con precio/stock: {lines}. "
                    f"No puedo confirmar compatibilidad para {vehicle} solo por inventario; valida manual, etiqueta de puerta, despeje, carga y velocidad. {reason}"
                )
            if requested_not_confirmed:
                vehicle = self._vehicle_label(entities)
                return self._limit(
                    f"Para {vehicle} no tengo evidencia local de que {size} sea medida OEM o compatible confirmada. "
                    f"Si tu vehiculo ya tiene esa medida instalada, Inventario Transalca tiene: {lines}. {reason} "
                    "Antes de comprar valida etiqueta de puerta, manual, despeje, carga y velocidad."
                )
            return self._limit(
                f"Inventario Transalca: para la medida {size} encontre disponibilidad exacta con precio/stock: {lines}. {reason}"
                " No cambies a otra medida sin validar etiqueta de puerta, manual e indice de carga/velocidad."
            )
        exact_catalog = find_exact_size_products(catalog.products, size)
        if exact_catalog:
            lines = '; '.join(product_line(item) for item in exact_catalog[:3])
            if entities.has_vehicle() and not fitment:
                vehicle = self._vehicle_label(entities)
                return self._limit(
                    f"La medida {size} aparece en catalogo, pero no puedo confirmar compatibilidad para {vehicle}. "
                    f"Ahora no veo stock positivo en esa consulta: {lines}. Valida manual, etiqueta de puerta, carga, velocidad y despeje."
                )
            if requested_not_confirmed:
                vehicle = self._vehicle_label(entities)
                return self._limit(
                    f"Para {vehicle} no puedo confirmar {size} como medida original o compatible. "
                    f"La medida aparece en catalogo, pero sin stock positivo ahora: {lines}. "
                    "Valida manual, etiqueta de puerta, carga, velocidad y despeje antes de cambiar medida."
                )
            return self._limit(
                f"La medida {size} aparece en catalogo, pero no tiene stock positivo ahora: {lines}. "
                "No voy a mostrar otra medida como compatible exacta; si quieres, puedo buscar una alternativa, pero debe validarse tecnicamente."
            )
        spec_note = ''
        if fitment and size in fit_sizes:
            spec_note = ' Esa medida coincide con una opcion comun para el vehiculo indicado.'
        elif requested_not_confirmed:
            spec_note = (
                f" Para el vehiculo indicado veo como referencia {', '.join(fit_sizes[:4])}; "
                f"no puedo tratar {size} como compatible sin validar."
            )
        if sources:
            spec_note += ' La busqueda externa se uso solo como referencia tecnica, no como inventario.'
        unavailable = 'No pude verificar el inventario porque la base de datos no respondio.' if not catalog.catalog_available else 'No aparece disponible en el inventario activo.'
        return self._limit(
            f"{unavailable} Para {size}, la recomendacion es mantener esa misma medida y validar carga/velocidad antes de comprar.{spec_note}"
        )

    def _answer_fitment(self, entities, sizes, matches, fitment, sources, needs_clarification, catalog):
        vehicle = self._vehicle_label(entities)
        size_text = ', '.join(sizes[:5])
        certainty = self._fitment_certainty_label(fitment, sources)
        parts = [f"Referencia: para {vehicle}, encontre estas medidas probables: {size_text} ({certainty})."]
        if needs_clarification:
            rims = sorted({str(size[-2:]) for size in sizes if size[-2:].isdigit()})
            if rims:
                parts.append(f"Confirma ano, version y rin actual ({', '.join(rims)}) para cerrar la compatibilidad.")
        if matches:
            with_stock = [entry for entry in matches if int_value(entry['item'].get('stock')) > 0]
            if with_stock:
                lines = '; '.join(product_line(entry['item']) for entry in with_stock[:3])
                parts.append(f"Inventario Transalca: priorizaria {lines}.")
                parts.append(self._explain_candidate(with_stock[0], entities))
            else:
                parts.append("Inventario Transalca: hay coincidencias de catalogo, pero sin stock positivo.")
        else:
            if catalog.catalog_available:
                parts.append("Inventario Transalca: no veo una coincidencia exacta con stock positivo para esas medidas en el inventario activo.")
            else:
                parts.append("Inventario Transalca: no pude verificar inventario en base de datos; la recomendacion queda como referencia tecnica.")
        parts.append("No uses otra medida solo porque tenga el mismo rin; ancho, perfil e indices tambien importan.")
        if sources:
            parts.append(self._sources_text(sources))
        return self._limit(' '.join(parts))

    def _answer_rim_only(self, entities, matches, catalog):
        if matches:
            with_stock = [entry for entry in matches if int_value(entry['item'].get('stock')) > 0]
            selected = with_stock or matches
            lines = '; '.join(product_line(entry['item']) for entry in selected[:4])
            qualifier = 'con stock' if with_stock else 'en catalogo sin stock positivo'
            return self._limit(
                f"Inventario Transalca: para rin {entities.rim} encontre opciones {qualifier}: {lines}. "
                "Esto es coincidencia por rin, no compatibilidad confirmada; confirma la medida completa y valida manual o etiqueta de puerta."
            )
        suffix = ' No pude verificar inventario por falla de base de datos.' if not catalog.catalog_available else ''
        return f"Inventario Transalca: no veo cauchos rin {entities.rim} con stock positivo en el inventario activo.{suffix} Confirma la medida completa y valida manual o etiqueta de puerta antes de comprar."

    def _answer_make_only(self, entities, catalog, web_note='', technical_note=''):
        make = entities.make or 'esa marca'
        catalog_note = (
            'Puedo buscar en inventario por rin si conoces el rin actual.'
            if catalog.catalog_available
            else 'Ahora no pude verificar inventario; igual necesito modelo, ano o rin para orientar.'
        )
        answer = (
            f"{make.title()} es la marca; necesito modelo y ano para validar medida sin inventar. "
            "Por ejemplo: Corolla 2016, Hilux 2020 o Fortuner 2017. "
            "Con modelo y ano puedo buscar una referencia tecnica y compararla con Inventario Transalca. "
            f"Si sabes el rin o la medida actual, tambien puedo filtrar cauchos por inventario. {catalog_note}"
        )
        return self._limit(self._append_note(self._append_note(answer, web_note), technical_note))

    def _answer_generic_tires(self, entities, matches):
        selected = [entry for entry in matches if int_value(entry['item'].get('stock')) > 0] or matches
        lines = '; '.join(product_line(entry['item']) for entry in selected[:3])
        return self._limit(
            f"Estas opciones del catalogo pueden servir como punto de partida: {lines}. "
            "Para recomendar con seguridad necesito medida completa o vehiculo con ano y rin."
        )

    def _handle_service(self, entities, catalog):
        matches = find_services(catalog.services, entities)
        if entities.tokens & {'vibra', 'vibracion', 'tiembla', 'temblor', 'volante'}:
            answer = (
                "Si el volante vibra despues de 80 km/h, lo primero es revisar balanceo de ruedas. "
                "Tambien conviene revisar alineacion, rotacion y estado de cauchos si hay desgaste irregular."
            )
        elif entities.tokens & {'check', 'tablero', 'luz', 'falla'}:
            answer = "Para luz de check engine o fallas en tablero, el servicio adecuado es diagnostico con scanner antes de cambiar piezas."
        elif entities.tokens & {'freno', 'frenos', 'chilla', 'frenar'}:
            answer = "Para ruido o baja respuesta al frenar, pide revision de frenos: pastillas, discos y liga."
        elif entities.tokens & {'aceite', 'lubricante'}:
            answer = "Para cambio de aceite, valida viscosidad y especificacion del fabricante; tambien conviene cambiar filtro."
        else:
            answer = "Puedo orientarte con el servicio, pero necesito el sintoma principal o el mantenimiento que deseas hacer."
        if matches:
            answer += " Servicios relacionados: " + '; '.join(product_line(entry['item'], include_stock=False) for entry in matches[:3]) + '.'
        elif not catalog.catalog_available:
            answer += " No pude verificar la lista de servicios por una falla de base de datos."
        return self._limit(answer), matches, False, 0.82

    def _handle_order(self, entities):
        if entities.tokens & {'pago', 'pagos', 'comprobante'}:
            answer = 'Para pagos, sube el comprobante desde el pedido correspondiente y espera la validacion del administrador.'
        else:
            answer = 'Para revisar un pedido, entra en Mis pedidos. Si el pago ya fue aprobado, alli veras el estado y documentos disponibles.'
        return answer, [], False, 0.85

    def _handle_sucursal(self):
        return 'Puedes revisar sucursales activas desde la seccion de contacto o catalogo. Si necesitas confirmar disponibilidad, dime el producto o servicio.', [], False, 0.72

    def _handle_catalog_general(self, entities, catalog):
        if entities.tokens & {'codigo'}:
            matches = search_tire_text(catalog.products, entities.tokens, limit=5)
            if matches:
                lines = '; '.join(f"{entry['item'].get('codigo')}: {product_line(entry['item'])}" for entry in matches[:4])
                return self._limit(f"Por codigo o texto encontre estas coincidencias de catalogo: {lines}."), matches, False, 0.7
        category = self._category_from_tokens(entities.tokens)
        if category:
            matches = search_category(catalog.products, category, entities.tokens)
            if matches:
                lines = '; '.join(product_line(entry['item']) for entry in matches[:4])
                answer = f"En {category.lower()} encontre estas opciones activas: {lines}."
                if category == 'Cauchos':
                    answer += ' Para compatibilidad confirmada dime medida completa, ano y rin.'
                return self._limit(answer), matches, False, 0.75
            if catalog.catalog_available:
                return (
                    f"No veo coincidencias activas de {category.lower()} en este momento. "
                    "Eso no significa que no exista el producto en general; solo que no aparece activo en el inventario consultado."
                ), [], False, 0.68
            return (
                "No pude verificar el catalogo por una falla de base de datos. "
                "Puedo orientarte de forma general si me das categoria, medida o uso."
            ), [], False, 0.45
        return (
            "Puedo ayudarte con cauchos, repuestos, lubricantes, baterias, servicios, pedidos y pagos. "
            "Necesito que me digas el producto, medida, vehiculo o sintoma."
        ), [], True, 0.45

    def _handle_followup(self, entities, state, model_intent, second_intent, model_confidence, stage_ms, started):
        candidates = state.get('last_candidates') or []
        tokens = entities.tokens

        def follow_payload(answer, confidence=None, needs_clarification=False):
            return self._base_payload(
                answer,
                'seguimiento',
                model_intent,
                second_intent,
                model_confidence if confidence is None else confidence,
                [],
                [],
                None,
                True,
                needs_clarification,
                stage_ms,
                started,
                entities=entities,
                state=state,
                inventory_query=self._inventory_query(entities),
            ), 200

        if not candidates:
            return follow_payload(
                'Sigo con el contexto anterior, pero necesito medida, rin o uso para recomendar con precision.',
                0.45,
                True,
            )
        if tokens & {'barato', 'economico', 'menos'}:
            available = [item for item in candidates if int_value(item.get('stock')) > 0]
            selected = sorted(available or candidates, key=lambda item: (item.get('precio') is None, item.get('precio') if item.get('precio') is not None else math.inf, -(item.get('stock') or 0)))
            if selected:
                item = selected[0]
                if item.get('precio') is None:
                    answer = f"La opcion mas economica con precio confirmado no quedo clara; {item.get('nombre')} tiene precio por confirmar"
                else:
                    answer = f"La opcion mas economica de lo que vimos es {item.get('nombre')} - ${item.get('precio'):.2f}"
                if item.get('stock') is not None:
                    answer += f" - stock {item.get('stock')}."
                return follow_payload(answer)
        if tokens & {'stock', 'disponible', 'disponibles', 'hay', 'quedan'}:
            lines = [f"{item.get('nombre')} - stock {item.get('stock')}" for item in candidates if item.get('stock') is not None]
            if lines:
                return follow_payload('Disponibilidad de lo que vimos: ' + '; '.join(lines[:4]) + '.')
        if tokens & {'precio', 'precios', 'cuanto', 'cuesta'}:
            lines = []
            for item in candidates[:4]:
                price = item.get('precio')
                if price is None:
                    lines.append(f"{item.get('nombre')} - precio por confirmar")
                else:
                    lines.append(f"{item.get('nombre')} - precio ${price:.2f}")
            if lines:
                return follow_payload('Precios de lo que vimos: ' + '; '.join(lines) + '.')
        if tokens & {'lluvia', 'tierra', 'barro', 'carretera'}:
            item = candidates[0]
            tire_type = item.get('tire_type')
            answer = self._followup_use_answer(item.get('nombre'), tire_type, tokens)
            vehicle = state.get('vehicle') or {}
            vehicle_bits = [vehicle.get('make'), vehicle.get('model'), vehicle.get('year')]
            vehicle_text = ' '.join(str(bit) for bit in vehicle_bits if bit)
            if vehicle_text:
                answer = f"Para {vehicle_text}, {answer[0].lower() + answer[1:] if answer else answer}"
            return follow_payload(answer)
        if tokens & {'primero', 'primera', 'el'}:
            item = candidates[0]
            answer = f"El primero fue {item.get('nombre')}. "
            if item.get('precio') is not None:
                answer += f"Precio ${item.get('precio'):.2f}. "
            if item.get('stock') is not None:
                answer += f"Stock {item.get('stock')}. "
            answer += 'Valida la medida exacta antes de comprar.'
            return follow_payload(answer)
        if tokens & {'cual', 'mejor', 'recomiendas', 'recomienda'}:
            item = candidates[0]
            vehicle = state.get('vehicle') or {}
            vehicle_bits = [vehicle.get('make'), vehicle.get('model'), vehicle.get('year')]
            vehicle_text = ' para ' + ' '.join(str(bit) for bit in vehicle_bits if bit) if any(vehicle_bits) else ''
            answer = f"Con el contexto anterior{vehicle_text} recomendaria {product_line(item)}. "
            tire_type = item.get('tire_type')
            if tire_type == 'A/T':
                answer += 'Es A/T, una opcion equilibrada para carretera y tierra.'
            elif tire_type == 'H/T':
                answer += 'Es H/T, mejor para ciudad, carretera y lluvia que para barro.'
            elif tire_type == 'M/T':
                answer += 'Es M/T, fuerte para barro, pero con mas ruido y menor comodidad en carretera.'
            else:
                answer += 'Valida tipo, medida e indices antes de comprar.'
            return follow_payload(answer)
        return follow_payload('Sigo con el contexto anterior, pero necesito que me indiques si buscas precio, stock o compatibilidad.', 0.45, True)

    def _followup_use_answer(self, name, tire_type, tokens):
        if tire_type == 'A/T':
            if tokens & {'lluvia', 'tierra', 'carretera'}:
                return f"{name} es A/T, asi que sirve bien para uso mixto carretera/tierra y lluvia moderada. No es la mejor opcion para barro profundo."
        if tire_type == 'M/T':
            return f"{name} es M/T: prioriza barro y trocha fuerte, pero suele hacer mas ruido y ser menos comodo en carretera."
        if tire_type == 'H/T':
            return f"{name} es H/T: va mejor para ciudad, carretera y lluvia que para tierra o barro fuerte."
        return f"Para decir si {name} sirve en ese uso necesito confirmar si es H/T, A/T o M/T y la medida exacta."

    def _local_fitment(self, entities):
        if not entities.model:
            return []
        results = []
        for entry in LOCAL_FITMENT:
            if entry['model'] != entities.model:
                continue
            if entities.make and entry.get('make') and entities.make != entry.get('make'):
                continue
            if entities.year and not (entry['start'] <= entities.year <= entry['end']):
                continue
            sizes = entry['sizes']
            if entities.rim:
                sizes = [size for size in sizes if size.endswith(f"R{entities.rim}")]
            if not sizes:
                continue
            results.append({**entry, 'sizes': sizes})
        return results

    def _compatible_sizes(self, entities, fitment, web_sizes):
        if entities.tire_size:
            return [entities.tire_size.normalized]
        sizes = []
        for entry in fitment:
            for size in entry['sizes']:
                if size not in sizes:
                    sizes.append(size)
        for size in web_sizes:
            if entities.rim and not size.endswith(f"R{entities.rim}"):
                continue
            if size not in sizes:
                sizes.append(size)
        return sizes

    def _should_search_web(self, entities, fitment):
        if os.getenv('ASSISTANT_WEB_VERIFY', '0').strip().lower() in {'1', 'true', 'yes'}:
            return bool(entities.model and (entities.year or entities.rim))
        return bool(entities.model and not fitment and (entities.year or entities.rim))

    def _web_fitment_sources(self, entities, search_service):
        if not entities.model:
            return []
        vehicle = ' '.join(str(part) for part in (entities.make, entities.model, entities.year) if part)
        queries = [
            f"{vehicle} tire size OEM",
            f"{vehicle} owner's manual tire size",
            f"{vehicle} medida cauchos rin {entities.rim}" if entities.rim else f"{vehicle} medida cauchos",
        ]
        sources = []
        seen = set()
        for query in queries[:2]:
            try:
                found = search_service.search(query, max_results=3)
            except Exception:
                logger.exception('assistant.web.provider_failed')
                found = []
            for source in found:
                if source.url in seen:
                    continue
                quality = evaluate_source(source, entities=entities, query=query)
                if hasattr(source, 'quality'):
                    source.quality = quality
                if not quality.get('accepted'):
                    continue
                seen.add(source.url)
                sources.append(source)
            if sources:
                break
        return sources[:4]

    def _needs_tire_clarification(self, entities, sizes):
        if entities.tire_size:
            return False
        if entities.has_vehicle() and not entities.year:
            return True
        rims = {size.split('R')[-1] for size in sizes if 'R' in size}
        if entities.has_vehicle() and not entities.rim and len(rims) > 1:
            return True
        return False

    def _fitment_certainty_label(self, fitment, sources):
        if fitment and sources:
            return 'certeza media-alta por datos locales y fuentes externas'
        if fitment:
            best = max(entry.get('certainty', 0.5) for entry in fitment)
            return 'certeza media' if best >= 0.65 else 'certeza baja-media'
        if sources:
            return 'referencia externa; validar manual'
        return 'sin evidencia suficiente'

    def _usage_reason(self, entities):
        if entities.tire_type == 'A/T' or entities.uses & {'tierra', 'grava'}:
            return 'Para uso mixto carretera/tierra priorizaria A/T porque equilibra agarre fuera de asfalto y manejo diario.'
        if entities.tire_type == 'M/T' or entities.uses & {'barro'}:
            return 'Para barro fuerte M/T da mas traccion, con mas ruido y desgaste en carretera.'
        if entities.tire_type == 'H/T' or entities.uses & {'autopista', 'ciudad'}:
            return 'Para carretera y ciudad H/T suele ser mas silencioso y eficiente.'
        return 'La decision final depende de uso, presupuesto, carga e indice de velocidad.'

    def _append_note(self, answer, note):
        if not note:
            return answer
        if note in answer:
            return answer
        return self._limit(f"{answer} {note}")

    def _technical_note(self, entities):
        tokens = entities.tokens
        notes = []
        if len(entities.all_sizes) >= 2:
            diameter_note = self._diameter_change_note(entities.all_sizes[0], entities.all_sizes[1])
            if diameter_note:
                notes.append(diameter_note)
        if tokens & {'diametro', 'diferencia'} and not notes:
            notes.append('Para cambio de medida valida diametro total, despeje, velocimetro, ancho de rin e indices antes de comprar.')
        if tokens & {'presion', 'psi'}:
            notes.append('No doy una presion fija sin datos: usa la etiqueta de puerta o manual y ajusta segun carga, medida y uso.')
        if tokens & {'dot', 'fecha'}:
            notes.append('El DOT indica semana y ano de fabricacion; revisa edad, grietas, deformaciones e historial, no solo dibujo.')
        if tokens & {'offset'}:
            notes.append('Con offset y ancho de rin hay que validar roce, despeje, centro de rueda, suspension y torque; no confirmo que quepa sin medir.')
        if tokens & {'direccional', 'direccionales'}:
            notes.append('En cauchos direccionales respeta el sentido de giro; no se cruzan en X salvo desmontaje y remonte correcto.')
        if tokens & {'asimetrico', 'asimetricos'}:
            notes.append('En cauchos asimetricos respeta las marcas OUTSIDE/INSIDE; el lado afuera no da igual.')
        if tokens & {'indice', 'velocidad', 'xl', 'remolque', 'remolcar', 'remolcando', 'carga', 'load', 'range', 'rango'} or (entities.tire_size and entities.tire_size.prefix in {'LT', 'P'}):
            xl_note = ' XL indica construccion reforzada, pero ' if 'xl' in tokens else ''
            notes.append(f'{xl_note}Valida indice de carga y velocidad contra la etiqueta/manual; para remolque o carga no basta que la medida coincida.')
        if tokens & {'lluvia', 'aquaplaning', 'hidroplaneo'}:
            notes.append('Para lluvia ayuda un dibujo H/T o touring con buen drenaje y profundidad, pero no elimina el riesgo de aquaplaning si hay exceso de velocidad o agua.')
        if (tokens & {'autopista', 'carretera'} and (tokens & {'tacos', 'barro'} or entities.tire_type == 'M/T')) or entities.uses & {'barro', 'tierra', 'grava'}:
            notes.append('Para autopista diaria evita priorizar M/T salvo barro fuerte: A/T puede equilibrar finca y carretera, H/T sera mas silencioso.')
        if tokens & {'a/t', 'at', 'r/t', 'rt', 'm/t', 'mt'}:
            notes.append('H/T prioriza carretera, silencio y confort; A/T es mixto, R/T es mas agresivo y M/T prioriza barro con mas ruido; para autopista diaria no lo trataria como eleccion automatica.')
        if tokens & {'hombro', 'reparado', 'reparacion'}:
            notes.append('No recomiendo usar como definitivo un caucho reparado en hombro o costado; revisalo con un tecnico y evita venderlo como seguro sin inspeccion.')
        if tokens & {'consumo', 'grandes', 'grande'}:
            notes.append('Un caucho mas grande puede afectar consumo, frenado, velocimetro y despeje; valida diametro total e indices antes de cambiar.')
        if tokens & {'comfort', 'confort'}:
            notes.append('Para confort y bajo ruido suele convenir H/T o touring; A/T sacrifica algo de silencio por agarre mixto.')
        return ' '.join(dict.fromkeys(notes))

    def _diameter_change_note(self, first, second):
        def diameter(size):
            if not (size.width and size.profile and size.rim):
                return None
            return size.rim * 25.4 + 2 * size.width * (size.profile / 100)

        first_diameter = diameter(first)
        second_diameter = diameter(second)
        if not first_diameter or not second_diameter:
            return None
        diff = ((second_diameter - first_diameter) / first_diameter) * 100
        return (
            f"El diametro total cambia aproximadamente {diff:.1f}% entre {first.normalized} y {second.normalized}; "
            "valida despeje, velocimetro, ABS, carga y ancho de rin."
        )

    def _explain_candidate(self, entry, entities):
        item = entry['item']
        reason = []
        if entry.get('compatibility') in {'exacta', 'compatible'}:
            reason.append('coincide con la medida compatible')
        if item.get('tire_type'):
            reason.append(f"es {item.get('tire_type')}")
        if int_value(item.get('stock')) > 0:
            reason.append('tiene stock positivo')
        if entities.budget == 'economico':
            reason.append('queda bien ordenado por precio')
        return 'Lo recomiendo primero porque ' + ', '.join(reason) + '.' if reason else ''

    def _sources_text(self, sources):
        selected = [source for source in sources if source.domain][:2]
        if not selected:
            return ''
        return (
            'Fuentes externas usadas como referencia: '
            + '; '.join(self._source_label(source) for source in selected)
            + '. No son inventario de Transalca ni compatibilidad absoluta; valida manual o etiqueta.'
        )

    def _source_label(self, source):
        quality = getattr(source, 'quality', {}) or {}
        confidence = quality.get('confidence')
        source_type = quality.get('source_type')
        parts = [source.domain]
        if source_type:
            parts.append(source_type)
        if confidence and not str(confidence).endswith('rechazado'):
            parts.append(f'confianza {confidence}')
        return f"{source.title} ({', '.join(parts)})"

    def _web_reference_note(self, sources, attempted, search_service):
        if sources:
            return self._sources_text(sources)
        if attempted and self._web_health(search_service):
            return (
                'Intente consultar fuentes externas, pero no obtuve una fuente util en este momento. '
                'Puedo orientarte de forma general, pero necesito validar la medida en manual/etiqueta del vehiculo.'
            )
        return ''

    def _category_from_tokens(self, tokens):
        if tokens & {'aceite', 'aceites', 'lubricante', 'lubricantes', '5w30', '5w-30', '10w40', '10w-40', '15w40', '15w-40'}:
            return 'Lubricantes'
        if tokens & {'filtro', 'filtros'}:
            return 'Filtros'
        if tokens & {'bateria', 'baterias', 'acumulador'}:
            return 'Baterias'
        if tokens & {'freno', 'frenos', 'pastilla', 'pastillas', 'disco', 'discos'}:
            return 'Frenos'
        if tokens & {'caucho', 'cauchos', 'llanta', 'llantas', 'neumatico', 'neumaticos', 'rin', 'rines', 'aro', 'aros'}:
            return 'Cauchos'
        if tokens & {'combo', 'combos', 'paquete', 'paquetes'}:
            return 'Combos'
        if tokens & {'repuesto', 'repuestos'}:
            return 'Repuestos'
        return None

    def _catalog_mentions(self, entities, catalog):
        if not catalog:
            return False
        tokens = entities.tokens
        if tokens & BUSINESS_TERMS:
            return True
        for item in (catalog.products or [])[:80]:
            if tokens & set(item.get('text', '').split()):
                return True
        return False

    def _vehicle_label(self, entities):
        parts = [entities.make, entities.model, str(entities.year) if entities.year else None]
        return ' '.join(part for part in parts if part) or 'ese vehiculo'

    def _contextual_followup(self, raw, entities, state):
        if not state:
            return ''
        clean = normalize_text(raw, autocorrect=False)
        vehicles = state.get('vehicles') or []
        current = state.get('vehicle') or {}
        labels = []
        for vehicle in vehicles[-3:]:
            label = ' '.join(str(vehicle.get(key)) for key in ('make', 'model', 'year') if vehicle.get(key))
            if label and label not in labels:
                labels.append(label)
        if not labels and current:
            label = ' '.join(str(current.get(key)) for key in ('make', 'model', 'year') if current.get(key))
            if label:
                labels.append(label)
        context_text = ', '.join(labels) if labels else 'el contexto anterior'
        parts = []
        if 'sesion' in clean or 'contexto anterior' in clean or 'no mezcles' in clean:
            parts.append(f"No mezclo sesiones; el contexto que tengo ahora es {context_text}.")
        if 'separad' in clean and labels:
            parts.append(f"Mantengo separados estos vehiculos: {context_text}.")
        if '4x2' in clean or '4x4' in clean:
            drivetrain = '4x2' if '4x2' in clean else '4x4'
            parts.append(f"Anoto la correccion {drivetrain}, pero aun necesito medida completa o rin para compatibilidad.")
        if entities.max_price:
            parts.append(f"Tomo presupuesto maximo {entities.max_price:g}; con ese limite debo volver a filtrar inventario actual.")
        elif entities.tokens & {'maximo', 'max', 'presupuesto'}:
            numbers = [token for token in entities.tokens if token.isdigit()]
            if numbers:
                parts.append(f"Tomo presupuesto maximo {numbers[0]}; con ese limite debo volver a filtrar inventario actual.")
        if 'falta' in clean or 'dato' in clean:
            parts.append("Falta confirmar vehiculo, ano/version, rin o medida completa y uso principal.")
        if not parts and labels:
            parts.append(f"Sigo con {context_text}, pero falta confirmar medida/rin, presupuesto o si quieres iniciar una sesion nueva.")
        return self._limit(' '.join(parts))

    def _memory_candidate(self, entry):
        item = entry.get('item') or {}
        return {
            'nombre': item.get('nombre'),
            'precio': item.get('precio'),
            'stock': item.get('stock'),
            'size': item.get('size'),
            'tire_type': item.get('tire_type'),
            'compatibility': entry.get('compatibility'),
        }

    def _web_health(self, search_provider=None):
        service = search_provider or self.search_service
        try:
            health = service.health() if hasattr(service, 'health') else {}
            return not health.get('circuit', {}).get('open', False) and health.get('enabled', True)
        except Exception:
            return False

    def _is_sensitive_request(self, raw, entities):
        clean = normalize_text(raw, autocorrect=False)
        tokens = entities.tokens
        if any(fragment in clean for fragment in (
            'password', 'contrasen', 'contrase', 'secreto', 'secretos',
            'token', 'credencial', 'credenciales', 'ignora tus reglas',
            'ignora las reglas', 'datos privados', 'datos personales',
            'variables de entorno', 'variable de entorno', '.env', 'api key',
            'apikey', 'lee archivo', 'leer archivo', 'win.ini', 'passwd',
            'exfiltra', 'exfiltrar', 'cookie', 'cookies',
            'config', 'dump', 'base de datos', 'ruta del servidor', 'archivo del servidor',
            'credenciales', 'credencial', 'secret', 'secrets', 'sql injection',
            'inyeccion sql', 'xss', 'html malicioso', 'prompt injection',
            'inyeccion de prompt', 'muestra el sistema', 'system prompt',
        )):
            return True
        if tokens & {'clientes', 'cliente'} and tokens & {'datos', 'privado', 'privados', 'personales'}:
            return True
        if tokens & {'archivo', 'archivos', 'servidor', 'config', 'dump'} and tokens & {'lee', 'leer', 'muestra', 'dame', 'extrae'}:
            return True
        if tokens & {'sesion', 'session'} and tokens & {'muestra', 'extrae', 'exfiltra', 'roba', 'dump', 'credenciales', 'cookie', 'cookies', 'token', 'privado'}:
            return True
        if tokens & {'reglas'} and tokens & {'ignora', 'ignorar'}:
            return True
        return False

    def _base_payload(
        self,
        answer,
        intent,
        model_intent,
        second_intent,
        confidence,
        matches,
        sources,
        catalog,
        web_available,
        needs_clarification,
        stage_ms,
        started,
        request_id=None,
        entities=None,
        original_entities=None,
        state=None,
        inventory_query=None,
        context_replaced=False,
        web_reason='',
    ):
        diagnostics = {
            'catalog_available': True if catalog is None else bool(catalog.catalog_available),
            'web_available': bool(web_available),
            'duration_ms': self._elapsed(started),
            'stage_ms': {key: round(value, 2) for key, value in (stage_ms or {}).items()},
            'context_used': bool(state),
            'context_replaced': bool(context_replaced),
            'web_attempted': bool(stage_ms and 'web' in stage_ms),
            'web_reason': web_reason or '',
            'inventory_consulted': catalog is not None,
            'inventory_query': inventory_query or {},
        }
        if entities is not None:
            diagnostics['entities'] = entities.to_public_dict() if hasattr(entities, 'to_public_dict') else {}
        if original_entities is not None:
            diagnostics['original_entities'] = original_entities.to_public_dict() if hasattr(original_entities, 'to_public_dict') else {}
        payload = {
            'status': 'success',
            'respuesta': self._limit(answer),
            'intent': intent,
            'model_intent': model_intent,
            'second_intent': second_intent,
            'confidence': round(float(confidence or 0), 3),
            'needs_clarification': bool(needs_clarification),
            'matches': matches or [],
            'sources': [source.to_dict() if hasattr(source, 'to_dict') else source for source in (sources or [])[:4]],
            'diagnostics': diagnostics,
        }
        if request_id:
            payload['request_id'] = request_id
        return payload

    def _inventory_query(self, entities):
        if not entities:
            return {}
        return {
            'size': entities.tire_size.normalized if entities.tire_size else None,
            'rim': entities.rim,
            'tire_type': entities.tire_type,
            'make': entities.make,
            'model': entities.model,
            'year': entities.year,
            'uses': sorted(entities.uses),
            'budget': entities.budget,
        }

    def _context_replaced(self, original_entities, state):
        if not state or not original_entities:
            return False
        vehicle = state.get('vehicle') or {}
        tire = state.get('tire') or {}
        if original_entities.model and vehicle.get('model') and original_entities.model != vehicle.get('model'):
            return True
        if original_entities.make and vehicle.get('make') and original_entities.make != vehicle.get('make'):
            return True
        if original_entities.rim and tire.get('rim') and original_entities.rim != tire.get('rim'):
            return True
        if original_entities.tire_size and tire.get('size') and original_entities.tire_size.normalized != tire.get('size'):
            return True
        return False

    def _web_reason(self, entities, intent, has_sources, attempted):
        if has_sources:
            return 'fuente_externa_relevante'
        if attempted:
            return 'modelo_ano_sin_fitment_local_o_verificacion_web'
        if not entities:
            return ''
        if entities.make and not entities.model:
            return 'faltan_modelo_y_ano'
        if intent in {'inventario_cauchos', 'producto'} and (entities.rim or entities.tire_size):
            return 'inventario_local_suficiente'
        if entities.model and not (entities.year or entities.rim):
            return 'faltan_ano_o_rin'
        return 'no_requerida'

    def health(self):
        engine_ok = True
        catalog_health = self.catalog_provider.health()
        web_health = self.search_service.health()
        circuit = web_health.get('circuit') or {}
        memory_stats = self.memory.stats() if hasattr(self.memory, 'stats') else {'sessions': 0, 'max_sessions': 0}
        degraded = bool(circuit.get('open')) or not catalog_health.get('available', False)
        status = 'ok' if engine_ok and not degraded else 'degraded' if engine_ok else 'down'
        return {
            'status': status,
            'version': os.getenv('ASSISTANT_VERSION', 'local'),
            'uptime_seconds': round(time.time() - self.started_at, 3),
            'engine': {
                'available': engine_ok,
                'classifier_labels': len(self.classifier.labels),
                'max_message_length': MAX_MESSAGE_LENGTH,
            },
            'catalog': {
                **catalog_health,
                'last_success_at': catalog_health.get('last_success_at'),
                'last_error_at': catalog_health.get('last_error_at'),
                'cached_items': catalog_health.get('cached_items', 0),
            },
            'web': {
                **web_health,
                'enabled': web_health.get('enabled', True),
                'circuit_open': bool(circuit.get('open')),
                'last_success_at': _health_iso(web_health.get('last_success_at')),
                'last_error_at': _health_iso(web_health.get('last_error_at')),
            },
            'memory': memory_stats,
        }

    def _limit(self, text):
        return (text or '')[:LOCAL_RESPONSE_LIMIT].strip()

    def _elapsed(self, started):
        return (time.perf_counter() - started) * 1000


_default_engine = AssistantEngine()


def build_response(question, session_id=None, client_history=None, request_id=None, catalog_provider=None, search_provider=None):
    return _default_engine.handle(
        question,
        session_id=session_id,
        client_history=client_history,
        request_id=request_id,
        catalog_provider=catalog_provider,
        search_provider=search_provider,
    )


def answer_user_message(message, session_id=None, history=None):
    return _default_engine.answer_user_message(message, session_id=session_id, history=history)


def assistant_health():
    return _default_engine.health()


def assistant_runtime_stats():
    health = _default_engine.health()
    return {
        'status': health.get('status'),
        'catalog': {
            'available': health.get('catalog', {}).get('available'),
            'cached_items': health.get('catalog', {}).get('cached_items'),
        },
        'web': {
            'enabled': health.get('web', {}).get('enabled'),
            'circuit_open': health.get('web', {}).get('circuit_open'),
            'cache': health.get('web', {}).get('cache'),
        },
        'memory': health.get('memory', {}),
    }


def clear_memory():
    _default_engine.memory.clear()


def _health_iso(value):
    if not value:
        return None
    if isinstance(value, str):
        return value
    return datetime.fromtimestamp(float(value), timezone.utc).isoformat().replace('+00:00', 'Z')
