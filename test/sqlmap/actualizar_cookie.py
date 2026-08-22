import os
import re
import requests

# ── Configuración ──
LOGIN_URL = "http://127.0.0.1:5000/auth/do_login"
LOGIN_DATA = {"email": "admin@transalca.com", "password": "Admin123!"}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 1. Hacer login y obtener cookie ──
print("[*] Iniciando sesion...")
resp = requests.post(LOGIN_URL, json=LOGIN_DATA)
cookie = resp.cookies.get("session")

if not cookie:
    print("[ERROR] No se obtuvo cookie de sesion. Verifica credenciales y que el servidor este corriendo.")
    print(f"        Status: {resp.status_code} | Respuesta: {resp.text[:200]}")
    exit(1)

print(f"[OK] Cookie obtenida: {cookie[:40]}...")

# ── 2. Actualizar todos los archivos .txt ──
updated = []
skipped = []

for root, dirs, files in os.walk(BASE_DIR):
    for fname in files:
        if fname.endswith('.txt'):
            fpath = os.path.join(root, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'Cookie: session=' in content:
                new_content = re.sub(r'Cookie: session=[^\r\n]+', f'Cookie: session={cookie}', content)
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                rel = os.path.relpath(fpath, BASE_DIR)
                updated.append(rel)
            else:
                skipped.append(fname)

print(f"\n[OK] Archivos actualizados ({len(updated)}):")
for f in updated:
    print(f"   + {f}")

if skipped:
    print(f"\n[--] Sin cookie (omitidos):")
    for f in skipped:
        print(f"   - {f}")
