import pymysql

try:
    conn = pymysql.connect(host='localhost', user='root', password='', database='db_transalca')
    cursor = conn.cursor()
    
    
    try:
        cursor.execute("ALTER TABLE mecanicos ADD COLUMN nombre VARCHAR(100) NOT NULL AFTER id")
        cursor.execute("ALTER TABLE mecanicos ADD COLUMN apellido VARCHAR(100) NOT NULL AFTER nombre")
        cursor.execute("ALTER TABLE mecanicos ADD COLUMN cedula VARCHAR(20) NOT NULL AFTER apellido")
        cursor.execute("ALTER TABLE mecanicos ADD CONSTRAINT UNIQUE (cedula)")
        cursor.execute("ALTER TABLE mecanicos ADD COLUMN telefono VARCHAR(20) AFTER cedula")
        cursor.execute("ALTER TABLE mecanicos ADD COLUMN foto_perfil VARCHAR(255) DEFAULT 'default.png' AFTER especialidad")
        
        cursor.execute("UPDATE mecanicos SET nombre='Mecanico', apellido='Test', cedula=CAST(id AS CHAR)")
    except Exception as e:
        print("Columns might already exist or error:", e)

    try:
        cursor.execute("ALTER TABLE mecanicos DROP COLUMN usuario_id")
    except Exception as e:
        print("usuario_id might already be dropped or error:", e)

    conn.commit()
    conn.close()
    print("Migracion de mecanicos completada!")
except Exception as e:
    print("Error global:", e)
