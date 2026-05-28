# componente_ia

Modulo ligero para el asistente de Transalca.

## Diseno

- Usa una red neuronal local muy pequena para clasificar intenciones, datos de entrenamiento generados por variantes reales del negocio, autocorreccion ligera de palabras mal escritas, memoria de los ultimos 3 turnos por sesion, reglas de negocio y el catalogo real de productos/servicios.
- No usa modelos grandes ni dependencias pesadas.
- No procesa imagenes ni archivos.
- Valida maximo 255 caracteres en frontend y backend.
- El widget guarda el session_id y el historial reciente en localStorage para conservar la conversacion al recargar la pagina.
- Solo responde temas del negocio: productos, servicios, mantenimiento, compras, pagos y pedidos.
- Usa consulta externa opcional a DuckDuckGo Instant Answer con timeout y cache corta. Si internet falla, responde con informacion local o indica que no tiene suficiente informacion.

## Pruebas manuales

Con la app levantada:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/asistente/mensaje -ContentType "application/json" -Body '{"mensaje":"Que cauchos son buenos para todo terreno?"}'
```

Debe responder sobre cauchos all terrain y, si existen productos relacionados, listarlos.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/asistente/mensaje -ContentType "application/json" -Body ('{"mensaje":"' + ('a' * 256) + '"}')
```

Debe devolver HTTP 400 por superar 255 caracteres.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/asistente/mensaje -ContentType "application/json" -Body '{"mensaje":"Quien gano el mundial?"}'
```

Debe rechazar la pregunta por estar fuera del negocio.

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/asistente/mensaje -ContentType "application/json" -Body '{"mensaje":"Mantenimiento de pieza xyz desconocida"}'
```

Debe indicar que no tiene informacion suficiente si no encuentra coincidencias.

Para simular fallo de internet, desconectar la red y repetir una pregunta de negocio. El sistema no debe romperse.
