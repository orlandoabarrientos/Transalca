from model.connection import Connection


class ProductModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, s.nombre as sucursal_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN sucursales s ON p.sucursal_id = s.id LEFT JOIN inventario i ON p.codigo = i.producto_codigo GROUP BY p.codigo ORDER BY p.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, s.nombre as sucursal_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN sucursales s ON p.sucursal_id = s.id LEFT JOIN inventario i ON p.codigo = i.producto_codigo WHERE p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre")

    def get_by_estado(self, estado):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, s.nombre as sucursal_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN sucursales s ON p.sucursal_id = s.id LEFT JOIN inventario i ON p.codigo = i.producto_codigo WHERE p.estado = %s GROUP BY p.codigo ORDER BY p.nombre", (estado,))

    def get_by_codigo(self, codigo):
        return self.fetch_one("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, s.nombre as sucursal_nombre FROM productos p LEFT JOIN sucursales s ON p.sucursal_id = s.id WHERE p.codigo = %s", (codigo,))

    def get_by_category(self, categoria_nombre):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN inventario i ON p.codigo = i.producto_codigo WHERE p.categoria = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre", (categoria_nombre,))

    def get_by_brand(self, marca_nombre):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN inventario i ON p.codigo = i.producto_codigo WHERE p.marca = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre", (marca_nombre,))

    def get_by_sucursal(self, sid):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN inventario i ON p.codigo = i.producto_codigo WHERE p.sucursal_id = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre", (sid,))

    def search(self, q):
        q = f"%{q}%"
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, COALESCE(SUM(i.stock),0) as stock FROM productos p LEFT JOIN inventario i ON p.codigo = i.producto_codigo WHERE (p.nombre LIKE %s OR p.codigo LIKE %s OR p.descripcion LIKE %s) AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre", (q, q, q))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO productos (codigo, nombre, descripcion, precio, categoria, marca, sucursal_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (data['codigo'].strip(), data['nombre'].strip(), data.get('descripcion', '').strip(),
             float(data['precio']), data.get('categoria') or None, data.get('marca') or None,
             data.get('sucursal_id') or None))

    def update_product(self, old_codigo, data):
        return self.update("transalca",
            "UPDATE productos SET codigo = %s, nombre = %s, descripcion = %s, precio = %s, categoria = %s, marca = %s, sucursal_id = %s WHERE codigo = %s",
            (data['codigo'].strip(), data['nombre'].strip(), data.get('descripcion', '').strip(),
             float(data['precio']), data.get('categoria') or None, data.get('marca') or None,
             data.get('sucursal_id') or None, old_codigo))

    def soft_delete(self, codigo):
        return self.update("transalca", "UPDATE productos SET estado = 0 WHERE codigo = %s", (codigo,))

    def toggle_estado(self, codigo):
        return self.update("transalca", "UPDATE productos SET estado = IF(estado=1,0,1) WHERE codigo = %s", (codigo,))

    def codigo_exists(self, codigo, exclude_codigo=None):
        if exclude_codigo:
            result = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s AND codigo != %s", (codigo, exclude_codigo))
        else:
            result = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s", (codigo,))
        return result is not None
