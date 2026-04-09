from model.connection import Connection


class ProductModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, s.nombre as sucursal_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN sucursales s ON p.sucursal_id = s.id LEFT JOIN inventario i ON p.id = i.producto_id ORDER BY p.nombre")

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, s.nombre as sucursal_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN sucursales s ON p.sucursal_id = s.id LEFT JOIN inventario i ON p.id = i.producto_id WHERE p.estado = 1 ORDER BY p.nombre")

    def get_by_estado(self, estado):
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, s.nombre as sucursal_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN sucursales s ON p.sucursal_id = s.id LEFT JOIN inventario i ON p.id = i.producto_id WHERE p.estado = %s ORDER BY p.nombre", (estado,))

    def get_by_id(self, pid):
        return self.fetch_one("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, s.nombre as sucursal_nombre FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN sucursales s ON p.sucursal_id = s.id WHERE p.id = %s", (pid,))

    def get_by_category(self, cid):
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN inventario i ON p.id = i.producto_id WHERE p.categoria_id = %s AND p.estado = 1 ORDER BY p.nombre", (cid,))

    def get_by_brand(self, bid):
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN inventario i ON p.id = i.producto_id WHERE p.marca_id = %s AND p.estado = 1 ORDER BY p.nombre", (bid,))

    def get_by_sucursal(self, sid):
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN inventario i ON p.id = i.producto_id WHERE p.sucursal_id = %s AND p.estado = 1 ORDER BY p.nombre", (sid,))

    def search(self, q):
        q = f"%{q}%"
        return self.fetch_all("transalca",
            "SELECT p.*, c.nombre as categoria_nombre, m.nombre as marca_nombre, COALESCE(i.stock,0) as stock FROM productos p LEFT JOIN categorias c ON p.categoria_id = c.id LEFT JOIN marcas m ON p.marca_id = m.id LEFT JOIN inventario i ON p.id = i.producto_id WHERE (p.nombre LIKE %s OR p.codigo LIKE %s OR p.descripcion LIKE %s) AND p.estado = 1 ORDER BY p.nombre", (q, q, q))

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO productos (codigo, nombre, descripcion, precio, categoria_id, marca_id, sucursal_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (data['codigo'].strip(), data['nombre'].strip(), data.get('descripcion', '').strip(),
             float(data['precio']), data.get('categoria_id') or None, data.get('marca_id') or None,
             data.get('sucursal_id') or None))

    def update_product(self, pid, data):
        return self.update("transalca",
            "UPDATE productos SET codigo = %s, nombre = %s, descripcion = %s, precio = %s, categoria_id = %s, marca_id = %s, sucursal_id = %s WHERE id = %s",
            (data['codigo'].strip(), data['nombre'].strip(), data.get('descripcion', '').strip(),
             float(data['precio']), data.get('categoria_id') or None, data.get('marca_id') or None,
             data.get('sucursal_id') or None, pid))

    def soft_delete(self, pid):
        return self.update("transalca", "UPDATE productos SET estado = 0 WHERE id = %s", (pid,))

    def toggle_estado(self, pid):
        return self.update("transalca", "UPDATE productos SET estado = IF(estado=1,0,1) WHERE id = %s", (pid,))

    def codigo_exists(self, codigo, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca", "SELECT id FROM productos WHERE codigo = %s AND id != %s", (codigo, exclude_id))
        else:
            result = self.fetch_one("transalca", "SELECT id FROM productos WHERE codigo = %s", (codigo,))
        return result is not None
