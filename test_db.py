import pymysql
from config.config import DB_CONFIG_MANTENIMIENTO
conn = pymysql.connect(**DB_CONFIG_MANTENIMIENTO)
with conn.cursor() as cur:
    cur.execute("SELECT foto_perfil FROM usuarios WHERE email='admin@transalca.com'")
    print(cur.fetchone())
