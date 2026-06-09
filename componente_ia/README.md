# componente_ia

Asistente automotriz ligero para Transalca, integrado en Flask por:

- `POST /api/asistente/mensaje`
- `GET /api/asistente/health`

No usa modelos locales pesados, GPU, PyTorch, TensorFlow, Transformers, bases vectoriales ni servidores de embeddings.

## Arquitectura

- `automotive_entities.py`: normalizacion conservadora, correccion ortografica, medidas de cauchos, rin, ano, marca, modelo, tipo A/T-M/T-H/T, uso, presupuesto y seguimiento.
- `catalog_retriever.py`: carga productos/servicios reales, normaliza `Decimal`, stock, sucursal, categoria, medida, tipo de caucho y ranking base.
- `web_search.py`: proveedor web configurable, fallback DuckDuckGo HTML sin JavaScript, cache TTL/LRU, timeouts separados y circuit breaker.
- `session_memory.py`: memoria estructurada por sesion con TTL y limite de sesiones.
- `asistente_engine.py`: orquestacion, clasificador liviano, compatibilidad, ranking explicable y generacion controlada.
- `api_asistente.py`: blueprint Flask, logging, `request_id`, healthcheck y rate limit simple.

## Variables de entorno

Ver `componente_ia/.env.example`.

Principales:

- `ASSISTANT_MAX_MESSAGE_LENGTH`: limite de caracteres. Default `1000`.
- `ASSISTANT_RESPONSE_LIMIT`: limite de respuesta. Default `1200`.
- `ASSISTANT_WEB_ENABLED`: `1` habilita busqueda web. Default `1`.
- `ASSISTANT_WEB_VERIFY`: `1` fuerza verificacion web aun si existe conocimiento local. Default `0`.
- `ASSISTANT_SEARCH_PROVIDER`: `brave`, `serper`, `bing` o vacio para fallback.
- `BRAVE_SEARCH_API_KEY`, `SERPER_API_KEY`, `BING_SEARCH_API_KEY`: claves opcionales.
- `ASSISTANT_WEB_CONNECT_TIMEOUT`: timeout de conexion web. Default `2`.
- `ASSISTANT_WEB_READ_TIMEOUT`: timeout de lectura web. Default `4`.
- `ASSISTANT_RATE_LIMIT`: solicitudes por IP por ventana. Default `60`.
- `ASSISTANT_RATE_WINDOW_SECONDS`: ventana del rate limit. Default `60`.

## Proveedores web

Orden de uso:

1. Proveedor indicado por `ASSISTANT_SEARCH_PROVIDER`.
2. Brave si existe `BRAVE_SEARCH_API_KEY`.
3. Serper si existe `SERPER_API_KEY`.
4. Bing si existe `BING_SEARCH_API_KEY`.
5. DuckDuckGo HTML como fallback gratuito.

El asistente no descarga paginas arbitrarias del usuario, no ejecuta JavaScript y no bloquea la respuesta si internet falla. Las fuentes se devuelven en `sources` solo como evidencia tecnica, nunca como inventario.

## Contrato API

Respuesta minima compatible:

```json
{
  "status": "success",
  "respuesta": "...",
  "intent": "...",
  "model_intent": "...",
  "matches": [],
  "session_id": "..."
}
```

Campos nuevos compatibles:

```json
{
  "confidence": 0.87,
  "needs_clarification": false,
  "second_intent": "...",
  "sources": [],
  "diagnostics": {
    "catalog_available": true,
    "web_available": true,
    "duration_ms": 180.5
  },
  "request_id": "..."
}
```

## Pruebas

Las pruebas automatizadas no dependen de MySQL ni de internet real; usan proveedores falsos de catalogo y busqueda.

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\componente_ia -m "not live_web"
```

Matriz determinista completa de 100 casos:

```powershell
.\.venv\Scripts\python.exe -m tests.componente_ia.matrix_runner --phase final_100 --include-reserved --output artifacts\ia_test_results.json
```

Casos de desarrollo y reservados por separado:

```powershell
.\.venv\Scripts\python.exe -m tests.componente_ia.matrix_runner --phase initial_dev_85 --output artifacts\ia_test_results_initial.json
.\.venv\Scripts\python.exe -m tests.componente_ia.matrix_runner --phase reserved_15 --only-reserved --output artifacts\ia_test_results_reserved.json
```

Rendimiento:

```powershell
.\.venv\Scripts\python.exe -m tests.componente_ia.matrix_runner --phase performance --markers performance --include-reserved --output artifacts\ia_test_results_performance.json
```

Internet real opcional:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\componente_ia -m live_web
$env:RUN_LIVE_WEB="1"
.\.venv\Scripts\python.exe -m pytest -q tests\componente_ia -m live_web
```

Prueba HTTP de la app principal:

```powershell
.\.venv\Scripts\python.exe app.py
```

```powershell
.\.venv\Scripts\python.exe -c "import requests; r=requests.post('http://127.0.0.1:5000/api/asistente/mensaje', json={'mensaje':'Tengo una 4Runner 2018 rin 17, que A/T tienen disponibles?'}); print(r.status_code); print(r.text)"
```

Prueba HTTP de la app independiente:

```powershell
.\.venv\Scripts\python.exe componente_ia\api_asistente.py
```

```powershell
.\.venv\Scripts\python.exe -c "import requests; r=requests.get('http://127.0.0.1:5090/api/asistente/health'); print(r.status_code); print(r.text)"
```

El informe de auditoria queda en `docs/ia_test_report.md`; los resultados ejecutados quedan en `artifacts/ia_test_results*.json`.

## Comportamiento tecnico

- Coincidencia exacta de medida no se mezcla con medidas parecidas.
- Productos con stock cero no se presentan como disponibles.
- Precio nulo se conserva como no registrado; no se muestra como `$0.00`.
- Si la base de datos falla, responde con orientacion general y marca `catalog_available=false`.
- Si internet falla, sigue respondiendo con catalogo/conocimiento local.
- Si faltan ano, version o rin y hay varias medidas posibles, pregunta el dato minimo.
- Las recomendaciones explican compatibilidad, tipo de terreno, stock y precio cuando aplica.

## Limites para servidor modesto

- Memoria de sesion: TTL 30 minutos, maximo 200 sesiones.
- Cache web: TTL 30 minutos, maximo 64 consultas.
- Sin entrenamiento por peticion y sin inferencia pesada.
- Timeout web configurable con `ASSISTANT_WEB_CONNECT_TIMEOUT` y `ASSISTANT_WEB_READ_TIMEOUT`.
- Longitud de mensaje por defecto: 1000 caracteres.
