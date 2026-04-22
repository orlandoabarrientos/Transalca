import pymysql
from config.config import DB_CONFIG_TRANSALCA

conn = pymysql.connect(
    host=DB_CONFIG_TRANSALCA['host'],
    user=DB_CONFIG_TRANSALCA['user'],
    password=DB_CONFIG_TRANSALCA['password'],
    database=DB_CONFIG_TRANSALCA['database'],
    charset='utf8mb4'
)

cursor = conn.cursor()

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasas_cambio (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fecha DATE NOT NULL,
            monto DECIMAL(12,4) NOT NULL,
            fuente VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_tasa_fecha (fecha)
        )
    """)
    print("Tabla tasas_cambio creada/verificada.")
except Exception as e:
    print(f"Error tabla: {e}")

try:
    cursor.execute("SHOW INDEX FROM ordenes_venta WHERE Key_name = 'idx_ordenes_venta_cliente'")
    if not cursor.fetchone():
        cursor.execute("CREATE INDEX idx_ordenes_venta_cliente ON ordenes_venta (cliente_cedula)")
        print("Indice idx_ordenes_venta_cliente creado.")
    else:
        print("Indice idx_ordenes_venta_cliente ya existe.")
except Exception as e:
    print(f"Error indice: {e}")

conn.commit()
cursor.close()
conn.close()
print("Migracion completada.")
