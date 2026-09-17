# Transalca

Aplicación Flask de Transalca con catálogo, servicios y asistente comercial.
La configuración y las conexiones existentes se mantienen en `config/`.

## Instalación y ejecución

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Configura las variables de conexión y de la aplicación indicadas en `config/config.py`
para tu entorno. Los scripts SQL de `db/` y las migraciones se mantienen intactos;
activar Lite no requiere importar SQL ni cambiar el esquema.

## IA temporal — Lite Mode

Activa el asistente determinista antes de arrancar Flask:

```powershell
$env:TRANSALCA_AI_MODE = "lite"
.\.venv\Scripts\python.exe app.py
```

`TRANSALCA_AI_MODE=lite` usa `LiteAssistant` para cauchos, precios, disponibilidad,
servicios, categorías, sucursales y métodos públicos de pago configurados
(Pago Móvil, Binance y Zelle). Reutiliza los retrievers y consulta DB/config.
Los datos ausentes se declaran como no configurados/verificados. El stock sintético
se identifica como tal y no garantiza un conteo físico.

`TRANSALCA_AI_MODE=full` usa la IA existente. Sin la variable se conserva ese
comportamiento. Reinicia el proceso tras cambiar el modo.

Lite no entrena modelos ni usa fitment web o inferido. El catálogo
[`vehicle_catalog_lite.json`](componente_ia/lite/vehicle_catalog_lite.json) comienza
vacío: la evidencia local disponible no verifica compatibilidades.
Para agregar un vehículo `VERIFIED`, verifica marca, modelo, año, medida exacta
y alcance de la versión con evidencia fiable; registra su referencia conforme a
[`README_LITE.md`](componente_ia/lite/README_LITE.md). Una medida escrita por el
usuario no verifica compatibilidad.

La memoria es temporal, por `session_id`, dentro del proceso. Puedes reiniciar una
sesión con `POST /api/asistente/reset` y `{"session_id":"tu-session-id"}` en Lite.

```powershell
.\.venv\Scripts\python.exe -m pytest componente_ia/tests/lite -q -p no:cacheprovider
```

Consulta [la arquitectura y API existentes](componente_ia/README.md) y
[el alcance de Lite](componente_ia/lite/README_LITE.md).
