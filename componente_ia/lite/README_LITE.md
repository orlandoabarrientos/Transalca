# IA temporal — Lite Mode

Activación: `TRANSALCA_AI_MODE=lite`. `TRANSALCA_AI_MODE=full`, o variable ausente,
conserva la IA actual. Reiniciar el backend después de cambiar el entorno.

Lite usa reglas y respuestas breves, sin entrenamiento, tuning, generación,
candidatos V10 ni búsquedas web. El módulo se puede retirar junto con el switch
de entrada. No altera scorer, normalizer, contratos, registry ni esquema SQL.

## Alcance y fuentes

Intents: `greeting`, `payment_methods`, `branches`, `services`, `categories`,
`inventory_by_size`, `inventory_by_brand`, `inventory_by_type`, `price`, `stock`,
`cheapest`, `most_stock`, `vehicle_fitment`, `vehicle_followup`, `unsupported`.

Se reutilizan `InventoryRetriever`, `ServiceRetriever.list_active` y
`BusinessRetriever.resolve`: solo lecturas de DB/config existentes, sin SQL nuevo.
Los pagos públicos se limitan a Pago Móvil, Binance y Zelle, únicamente cuando
la fuente real los devuelve. No se publican cuentas ni datos privados.
Servicios y sucursales salen de registros verificados, nunca de conocimiento
genérico o del texto del usuario. Los errores de fuente producen una respuesta
breve de información no configurada/verificada, sin detalles internos.

El parser local preserva medidas métricas, comerciales y de flotación, prefijos
LT/P, sufijo C y rines decimales. No modifica el parser canónico. Las consultas
de inventario comparan medidas exactas: no equiparan prefijos ni afirman fitment.
Precio mínimo y mayor stock se calculan sobre todas las coincidencias recuperadas,
antes de recortar la respuesta. La comparación básica muestra precio, stock y
sucursal de hasta tres opciones; no compara cualidades técnicas sin evidencia.

## Vehículos verificados

`vehicle_catalog_lite.json` comienza **vacío**. Se revisó la evidencia local
`componente_ia/data/curated_fitment.json`: contiene referencias por rangos de año,
varias versiones, confianza limitada y advertencias de confirmar; no aporta
documentación suficiente para afirmar una compatibilidad específica VERIFIED.
Los nombres reconocidos por el parser son vocabulario, no vehículos verificados.

Para agregar una entrada, revisar primero evidencia documental aplicable al
vehículo y año exactos. Añadir al array `vehicles` los campos `brand`, `model`,
`year` (entero), `tire_size` (una medida válida), `status: "VERIFIED"` y `evidence`
(referencia local verificable y descripción de la revisión). No promover datos
de pruebas, ejemplos, rangos ambiguos, inferencias ni una medida escrita por el
usuario. Conservar versión/mercado en la evidencia; si no es válida para toda la
identidad consultable, mantenerla sin verificar hasta ampliar el identificador.

Solo se responde con una medida si coinciden marca/modelo/año y existe una única
medida VERIFIED con evidencia. Cualquier ausencia o ambigüedad produce:

> No tengo esa compatibilidad verificada actualmente. Si me indicas la medida
> del caucho, puedo revisar disponibilidad y precios.

No hay fitment web automático ni fitment inferido. Reiniciar tras editar catálogo.

## Memoria y uso

`LiteAssistant.respond(message, session_id=None, history=None, request_id=None)`
devuelve `(payload, http_status)` con `respuesta`, `message`, `intent`, `matches`,
`entities` y `diagnostics.ai_mode="lite"`. `build_response` es equivalente.
`reset_session(session_id)` borra solo esa sesión. `health()` no consulta registry.

La memoria por proceso conserva vehículo, medida, tipo, último intent, productos
y selección, más filtros mínimos de rin/marca/modelo/sucursal. Se limita a 1000
sesiones. Sin `session_id` no se comparte memoria. El parámetro `history` no se
usa como evidencia; los precios/stock se vuelven a consultar en los follow-ups
(con la caché vigente del retriever). No persiste entre reinicios ni workers.

## Limitaciones vigentes

- El stock marcado `synthetic_inventory_mode` o `stock_source=synthetic_seed`
  mantiene esa procedencia en `matches` y en la respuesta: **stock sintético
  registrado; no garantiza el conteo físico**. Lite no cambia los datos.
- Una sucursal informada pertenece al producto; el stock puede ser agregado entre
  sucursales. Consultar una sede filtra productos, no inventa conteos físicos por sede.
- Tres productos como máximo en el texto, seis en `matches`; el conteo inicial
  corresponde a todas las opciones encontradas. Sin fuente se declara ausencia.
- El catálogo de vehículos real contiene cero entradas VERIFIED inicialmente.
- No hay consejos técnicos inferidos, pagos/órdenes, datos de clientes ni escritura
  de DB. Un intent fuera de alcance recibe una respuesta fija.

Validación: `python -m pytest componente_ia/tests/lite -q`.
