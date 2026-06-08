from model.connection import Connection


class ProductModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self):
        rows = self.fetch_all("transalca", "SHOW COLUMNS FROM productos")
        return {r['Field'] for r in rows}

    def _product_select(self, where="p.estado = 1"):
        return (
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, "
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre ORDER BY su.nombre SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id "
            f"WHERE {where} GROUP BY p.codigo ORDER BY p.nombre"
        )

    def get_all(self):
        return self.fetch_all("transalca", self._product_select())

    def get_all_paginated(self, page, per_page, q=None):
        offset = (page - 1) * per_page
        where = ["p.estado = 1"]
        params = []
        if q:
            like = f"%{q}%"
            where.append("(p.nombre LIKE %s OR p.codigo LIKE %s OR p.descripcion LIKE %s)")
            params.extend([like, like, like])
        
        where_sql = " AND ".join(where)
        total_query = f"SELECT COUNT(DISTINCT p.codigo) as total FROM productos p WHERE {where_sql}"
        total = self.fetch_one("transalca", total_query, tuple(params))['total']
        
        select_query = (
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, "
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre ORDER BY su.nombre SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id "
            f"WHERE {where_sql} GROUP BY p.codigo ORDER BY p.nombre "
            "LIMIT %s OFFSET %s"
        )
        data = self.fetch_all("transalca", select_query, tuple(params + [per_page, offset]))
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    def get_active_paginated(self, page, per_page, category=None, branch=None, q=None, sort=None):
        where = ["p.estado = 1"]
        params = []

        if category:
            where.append("p.categoria = %s")
            params.append(category)
        if branch:
            where.append(
                "EXISTS (SELECT 1 FROM stock st_filter "
                "WHERE st_filter.producto_codigo = p.codigo AND st_filter.sucursal_id = %s)"
            )
            params.append(branch)
        if q:
            like = f"%{q}%"
            where.append("(p.nombre LIKE %s OR p.codigo LIKE %s OR p.descripcion LIKE %s)")
            params.extend([like, like, like])

        where_sql = " AND ".join(where)
        count_query = f"SELECT COUNT(DISTINCT p.codigo) as total FROM productos p WHERE {where_sql}"
        total_row = self.fetch_one("transalca", count_query, tuple(params))
        total = total_row['total'] if total_row else 0
        pages = (total + per_page - 1) // per_page if total else 0
        if pages and page > pages:
            page = pages
        offset = (page - 1) * per_page

        order_by = {
            'price_asc': 'p.precio ASC, p.nombre ASC',
            'price_desc': 'p.precio DESC, p.nombre ASC',
            'name': 'p.nombre ASC'
        }.get(sort, 'p.nombre ASC')

        select_query = (
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, "
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre ORDER BY su.nombre SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id "
            f"WHERE {where_sql} GROUP BY p.codigo ORDER BY {order_by} "
            "LIMIT %s OFFSET %s"
        )
        data = self.fetch_all("transalca", select_query, tuple(params + [per_page, offset]))
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

    def get_active(self):
        return self.fetch_all("transalca", self._product_select())

    def get_by_estado(self, estado):
        return self.fetch_all("transalca", self._product_select("p.estado = %s"), (estado,))

    def get_by_codigo(self, codigo):
        return self.fetch_one("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, "
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre ORDER BY su.nombre SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id WHERE p.codigo = %s GROUP BY p.codigo", (codigo,))

    def get_by_category(self, categoria_nombre):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p LEFT JOIN categorias c ON p.categoria = c.nombre LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "WHERE p.categoria = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre", (categoria_nombre,))

    def get_by_brand(self, marca_nombre):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p LEFT JOIN categorias c ON p.categoria = c.nombre LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "WHERE p.marca = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre", (marca_nombre,))

    def get_by_sucursal(self, sid):
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, su.nombre as sucursal_nombre, "
            "COALESCE(st.stock,0) as stock FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre "
            "INNER JOIN stock st ON p.codigo = st.producto_codigo "
            "INNER JOIN sucursales su ON st.sucursal_id = su.id "
            "WHERE st.sucursal_id = %s AND p.estado = 1 ORDER BY p.nombre", (sid,))

    def search(self, q):
        q = f"%{q}%"
        return self.fetch_all("transalca",
            "SELECT p.*, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen as categoria_imagen, COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p LEFT JOIN categorias c ON p.categoria = c.nombre LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "WHERE (p.nombre LIKE %s OR p.codigo LIKE %s OR p.descripcion LIKE %s) AND p.estado = 1 "
            "GROUP BY p.codigo ORDER BY p.nombre", (q, q, q))

    def _sync_sucursales(self, codigo, sucursal_ids):
        ids = []
        for value in sucursal_ids or []:
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                continue
            if parsed not in ids:
                ids.append(parsed)
        if ids:
            placeholders = ", ".join(["%s"] * len(ids))
            self.update("transalca", f"DELETE FROM stock WHERE producto_codigo = %s AND sucursal_id NOT IN ({placeholders})", (codigo, *ids))
        else:
            self.update("transalca", "DELETE FROM stock WHERE producto_codigo = %s", (codigo,))
        for sucursal_id in ids:
            existing = self.fetch_one("transalca", "SELECT 1 FROM stock WHERE producto_codigo = %s AND sucursal_id = %s", (codigo, sucursal_id))
            if not existing:
                self.insert("transalca", "INSERT INTO stock (producto_codigo, sucursal_id, stock) VALUES (%s, %s, 0)", (codigo, sucursal_id))

    def create(self, data):
        columns = self._columns()
        values = {
            'codigo': data['codigo'].strip(),
            'nombre': data['nombre'].strip(),
            'descripcion': data.get('descripcion', '').strip(),
            'precio': float(data['precio']),
            'categoria': data.get('categoria') or None,
            'marca': data.get('marca') or None,
            'imagen': data.get('imagen') or 'default_product.png'
        }
        keys = [k for k in values if k in columns]
        pid = self.insert("transalca",
            f"INSERT INTO productos ({', '.join(keys)}) VALUES ({', '.join(['%s'] * len(keys))})",
            tuple(values[k] for k in keys))
        self._sync_sucursales(values['codigo'], data.get('sucursal_ids') or [])
        return pid

    def update_product(self, old_codigo, data):
        columns = self._columns()
        values = {
            'codigo': data['codigo'].strip(),
            'nombre': data['nombre'].strip(),
            'descripcion': data.get('descripcion', '').strip(),
            'precio': float(data['precio']),
            'categoria': data.get('categoria') or None,
            'marca': data.get('marca') or None
        }
        if 'imagen' in data:
            values['imagen'] = data['imagen']
        keys = [k for k in values if k in columns]
        params = [values[k] for k in keys] + [old_codigo]
        res = self.update("transalca",
            f"UPDATE productos SET {', '.join([f'{k} = %s' for k in keys])} WHERE codigo = %s",
            tuple(params))
        self._sync_sucursales(values['codigo'], data.get('sucursal_ids') or [])
        return res

    def soft_delete(self, codigo):
        return self.update("transalca", "UPDATE productos SET estado = 0 WHERE codigo = %s", (codigo,))

    def toggle_estado(self, codigo):
        return self.soft_delete(codigo)

    def codigo_exists(self, codigo, exclude_codigo=None):
        if exclude_codigo:
            result = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s AND codigo != %s AND estado = 1", (codigo, exclude_codigo))
        else:
            result = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s AND estado = 1", (codigo,))
        return result is not None

    def category_exists(self, nombre):
        if not nombre:
            return True
        return self.fetch_one("transalca", "SELECT nombre FROM categorias WHERE nombre = %s AND estado = 1", (nombre,)) is not None

    def brand_exists(self, nombre):
        if not nombre:
            return True
        return self.fetch_one("transalca", "SELECT nombre FROM marcas WHERE nombre = %s AND estado = 1", (nombre,)) is not None

    def supplier_exists(self, rif):
        if not rif:
            return True
        return self.fetch_one("transalca", "SELECT rif FROM proveedores WHERE rif = %s AND estado = 1", (rif,)) is not None
