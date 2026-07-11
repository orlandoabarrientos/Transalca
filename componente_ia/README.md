# componente_ia

Asesor automotriz y comercial híbrido de Transalca. Combina reglas de alta precisión, clasificador local, RAG BM25/fuzzy, memoria por sesión, catálogo real, conocimiento de servicios/negocio, fitment curado, web con control de fuentes y un LLM externo opcional sujeto a evidencia.

No instala frameworks de ML pesados ni entrena durante una solicitud.

## API

- `POST /api/asistente/mensaje`
- `GET /api/asistente/health`
- `GET /api/asistente/metrics` (rol autorizado/testing)
- `POST /api/asistente/feedback` (rol autorizado/testing)

La respuesta conserva el contrato anterior (`respuesta`, `intent`, `matches`, `sources`) y agrega intención múltiple, confianza, grounding, fallback y diagnósticos seguros.

## Arquitectura

- `assistant_orchestrator.py`: guardrails → entidades → memoria → intención → plan → evidencia → composición → métricas/feedback.
- `intent_router.py`, `semantic_intent_retriever.py`, `models/intent_model.json`: router por capas.
- `entity_extractor.py`, `vehicle_resolver.py`, `vehicle_aliases.py`: lenguaje real, medidas, carga, vehículos conocidos/desconocidos y alias regionales.
- `tire_fitment.py`, `technical_knowledge.py`: referencia curada y cálculos geométricos sin afirmar compatibilidad.
- `inventory_retriever.py`, `service_retriever.py`, `business_knowledge.py`: fuentes dinámicas separadas del conocimiento general.
- `lightweight_rag.py`: índice local BM25/fuzzy.
- `web_search.py`, `source_quality.py`: proveedores configurados/directos/DDG, fake/disabled, presupuesto duro, cache y circuit breaker.
- `providers/`: proveedor local, externo agnóstico y fallback.
- `conversation_memory.py`: TTL, capacidad e aislamiento.
- `feedback_store.py`, `learning_pipeline.py`, `training_pipeline.py`, `evaluation.py`: mejora offline controlada.
- `metrics.py`, `health.py`, `production_validation.py`: operación y pruebas de carga.

La lógica anterior queda en `asistente_engine.py` para compatibilidad, pero `api_asistente.py` usa el orquestador nuevo.

## Inicio local

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe componente_ia\api_asistente.py
```

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5090/api/asistente/mensaje `
  -ContentType application/json `
  -Body '{"mensaje":"Tengo una Hilux 2020, quiero A/T rin 17 y dime cuál tienen barato","session_id":"demo-session-01"}'
```

## Dataset, entrenamiento y evaluación

```powershell
python -m componente_ia.tools.generate_assistant_training_cases
python -m componente_ia.model_selection benchmark
python -m componente_ia.training_pipeline train
python -m componente_ia.evaluation evaluate
python -m componente_ia.production_validation --sequential 1000 --concurrent 100 --catalog-size 10000 --soak 1000 --live-web
```

Promoción fail-closed:

```powershell
python -m componente_ia.training_pipeline promote --evidence componente_ia/artifacts/ia_release_evidence.json
python -m componente_ia.training_pipeline rollback
```

## Aprendizaje seguro

```powershell
python -m componente_ia.learning_pipeline collect
python -m componente_ia.learning_pipeline review
python -m componente_ia.learning_pipeline build-dataset
```

La persistencia de feedback está apagada por defecto. Ningún fitment, precio, política o regla de seguridad se activa automáticamente.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest -q componente_ia\tests
```

Las suites usan catálogos y web simulados, salvo la opción explícita `--live-web` del validador de producción.

## Configuración

Consulte `.env.example`. El LLM externo requiere `ASSISTANT_LLM_ENABLED=1`; aun habilitado no recibe conexión DB ni puede inventar hechos dinámicos. La web usa un presupuesto total de 1,30 s. DB dinámica usa acceso fail-fast de 80 ms y actualiza cache en segundo plano.

## Informes

- `docs/ia_intelligence_architecture.md`
- `docs/ia_training_dataset_report.md`
- `docs/ia_learning_pipeline.md`
- `docs/ia_business_knowledge.md`
- `docs/ia_production_validation.md`
