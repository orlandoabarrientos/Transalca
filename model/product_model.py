from model.connection import Connection
from config.validation import (
    SELECT_TAMPER_MESSAGE,
    ValidationError,
    normalize_decimal,
    optional_text,
    require_text,
)


class ProductModel(Connection):
    def __init__(self):
        super().__init__()
        self._codigo = None
        self._nombre = None
        self._descripcion = None
        self._precio = None

    @property
    def codigo(self):
        return self._codigo

    @codigo.setter
    def codigo(self, valor):
        if valor:
            valor = str(valor).strip()
        self._codigo = valor

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def descripcion(self):
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._descripcion = valor

    @property
    def precio(self):
        return self._precio

    @precio.setter
    def precio(self, valor):
        self._precio = float(valor)

    def _columns(self):
        rows = self.fetch_all("transalca", "SHOW COLUMNS FROM productos")
        return {r['Field'] for r in rows}

    def _product_select(self, where="p.estado = 1"):
        allowed_where = {"p.estado = 1", "p.estado = %s"}
        if where not in allowed_where:
            raise ValueError("Filtro de producto no permitido.")
        base_sql = (
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,"
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre_sucursal ORDER BY su.nombre_sucursal SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre_categoria "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id_sucursal "
        )
        if where == "p.estado = 1":
            return base_sql + "WHERE p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre_producto"
        return base_sql + "WHERE p.estado = %s GROUP BY p.codigo ORDER BY p.nombre_producto"

    def _get_all(self):
        return self.fetch_all("transalca", self._product_select())

    def _get_all_paginated(self, page, per_page, q=None):
        offset = (page - 1) * per_page
        q_value = (q or '').strip()
        like = f"%{q_value}%"
        filter_params = [q_value, like, like, like]
        total_query = (
            "SELECT COUNT(DISTINCT p.codigo) as total FROM productos p "
            "WHERE p.estado = 1 AND (%s = '' OR p.nombre_producto LIKE %s OR p.codigo LIKE %s OR p.descripcion_producto LIKE %s)"
        )
        total = self.fetch_one("transalca", total_query, tuple(filter_params))['total']
        
        select_query = (
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,"
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre_sucursal ORDER BY su.nombre_sucursal SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre_categoria "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id_sucursal "
            "WHERE p.estado = 1 AND (%s = '' OR p.nombre_producto LIKE %s OR p.codigo LIKE %s OR p.descripcion_producto LIKE %s) "
            "GROUP BY p.codigo ORDER BY p.nombre_producto "
            "LIMIT %s OFFSET %s"
        )
        data = self.fetch_all("transalca", select_query, tuple(filter_params + [per_page, offset]))
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    def _get_active_paginated(self, page, per_page, category=None, branch=None, q=None, sort=None):
        category_value = category or None
        branch_value = branch or None
        q_value = (q or '').strip()
        like = f"%{q_value}%"
        filter_params = [category_value, category_value, branch_value, branch_value, q_value, like, like, like]

        count_query = (
            "SELECT COUNT(DISTINCT p.codigo) as total FROM productos p WHERE p.estado = 1 "
            "AND (%s IS NULL OR p.categoria = %s) "
            "AND (%s IS NULL OR EXISTS (SELECT 1 FROM stock st_filter WHERE st_filter.producto_codigo = p.codigo AND st_filter.sucursal_id = %s)) "
            "AND (%s = '' OR p.nombre_producto LIKE %s OR p.codigo LIKE %s OR p.descripcion_producto LIKE %s)"
        )
        total_row = self.fetch_one("transalca", count_query, tuple(filter_params))
        total = total_row['total'] if total_row else 0
        pages = (total + per_page - 1) // per_page if total else 0
        if pages and page > pages:
            page = pages
        offset = (page - 1) * per_page

        select_base = (
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,"
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre_sucursal ORDER BY su.nombre_sucursal SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre_categoria "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id_sucursal "
            "WHERE p.estado = 1 "
            "AND (%s IS NULL OR p.categoria = %s) "
            "AND (%s IS NULL OR EXISTS (SELECT 1 FROM stock st_filter WHERE st_filter.producto_codigo = p.codigo AND st_filter.sucursal_id = %s)) "
            "AND (%s = '' OR p.nombre_producto LIKE %s OR p.codigo LIKE %s OR p.descripcion_producto LIKE %s) "
            "GROUP BY p.codigo ORDER BY "
        )
        select_queries = {
            'price_asc': select_base + "p.precio_producto ASC, p.nombre_producto ASC LIMIT %s OFFSET %s",
            'price_desc': select_base + "p.precio_producto DESC, p.nombre_producto ASC LIMIT %s OFFSET %s",
            'name': select_base + "p.nombre_producto ASC LIMIT %s OFFSET %s"
        }
        select_query = select_queries.get(sort, select_queries['name'])
        data = self.fetch_all("transalca", select_query, tuple(filter_params + [per_page, offset]))
        return {
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages
        }

    def _get_active(self):
        return self.fetch_all("transalca", self._product_select())

    def _get_by_estado(self, estado):
        return self.fetch_all("transalca", self._product_select("p.estado = %s"), (estado,))

    def _get_by_codigo(self, codigo):
        return self.fetch_one("transalca",
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,"
            "COALESCE(GROUP_CONCAT(DISTINCT su.nombre_sucursal ORDER BY su.nombre_sucursal SEPARATOR ', '), 'Sin stock') as sucursal_nombre, "
            "GROUP_CONCAT(DISTINCT st.sucursal_id ORDER BY st.sucursal_id SEPARATOR ',') as sucursal_ids, "
            "COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre_categoria "
            "LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "LEFT JOIN sucursales su ON st.sucursal_id = su.id_sucursal WHERE p.codigo = %s GROUP BY p.codigo", (codigo,))

    def _get_by_category(self, categoria_nombre):
        return self.fetch_all("transalca",
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p LEFT JOIN categorias c ON p.categoria = c.nombre_categoria LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "WHERE p.categoria = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre_producto", (categoria_nombre,))

    def _get_by_brand(self, marca_nombre):
        return self.fetch_all("transalca",
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p LEFT JOIN categorias c ON p.categoria = c.nombre_categoria LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "WHERE p.marca = %s AND p.estado = 1 GROUP BY p.codigo ORDER BY p.nombre_producto", (marca_nombre,))

    def _get_by_sucursal(self, sid):
        return self.fetch_all("transalca",
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,su.nombre_sucursal as sucursal_nombre, "
            "COALESCE(st.stock,0) as stock FROM productos p "
            "LEFT JOIN categorias c ON p.categoria = c.nombre_categoria "
            "INNER JOIN stock st ON p.codigo = st.producto_codigo "
            "INNER JOIN sucursales su ON st.sucursal_id = su.id_sucursal "
            "WHERE st.sucursal_id = %s AND p.estado = 1 ORDER BY p.nombre_producto", (sid,))

    def _search(self, q):
        q = f"%{q}%"
        return self.fetch_all("transalca",
            "SELECT p.*, p.nombre_producto AS nombre, p.precio_producto AS precio, p.descripcion_producto AS descripcion, p.imagen_producto AS imagen, p.categoria as categoria_nombre, p.marca as marca_nombre, c.imagen_categoria as categoria_imagen,COALESCE(SUM(st.stock),0) as stock "
            "FROM productos p LEFT JOIN categorias c ON p.categoria = c.nombre_categoria LEFT JOIN stock st ON p.codigo = st.producto_codigo "
            "WHERE (p.nombre_producto LIKE %s OR p.codigo LIKE %s OR p.descripcion_producto LIKE %s) AND p.estado = 1 "
            "GROUP BY p.codigo ORDER BY p.nombre_producto", (q, q, q))

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
            existing_rows = self.fetch_all("transalca", "SELECT sucursal_id FROM stock WHERE producto_codigo = %s", (codigo,))
            for row in existing_rows:
                sucursal_id = row.get('sucursal_id')
                if sucursal_id not in ids:
                    self.update("transalca", "DELETE FROM stock WHERE producto_codigo = %s AND sucursal_id = %s", (codigo, sucursal_id))
        else:
            self.update("transalca", "DELETE FROM stock WHERE producto_codigo = %s", (codigo,))
        for sucursal_id in ids:
            existing = self.fetch_one("transalca", "SELECT 1 FROM stock WHERE producto_codigo = %s AND sucursal_id = %s", (codigo, sucursal_id))
            if not existing:
                self.insert("transalca", "INSERT INTO stock (producto_codigo, sucursal_id, stock) VALUES (%s, %s, 0)", (codigo, sucursal_id))

    def _validate(self, data, old_codigo=None):
        errors = {}
        codigo = optional_text(errors, 'codigo', data.get('codigo'), 'El codigo', max_len=50, allow_serial=True)
        if not codigo or len(codigo) < 2:
            errors['codigo'] = 'El codigo debe tener al menos 2 caracteres.'
        clean = {
            'codigo': (codigo or '').upper(),
            'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=150, allow_serial=False),
            'descripcion': optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=500, allow_serial=True),
            'precio': normalize_decimal(errors, 'precio', data.get('precio'), 'El precio'),
            'categoria': require_text(errors, 'categoria', data.get('categoria'), 'La categoria', min_len=1, max_len=150, allow_serial=True),
            'marca': require_text(errors, 'marca', data.get('marca'), 'La marca', min_len=1, max_len=150, allow_serial=True),
        }
        existing = self._get_by_codigo(old_codigo) if old_codigo else None
        if clean['categoria'] and not errors.get('categoria'):
            is_current_cat = existing and existing.get('categoria') == clean['categoria']
            if not is_current_cat and not self._category_exists(clean['categoria']):
                errors['categoria'] = SELECT_TAMPER_MESSAGE
        if clean['marca'] and not errors.get('marca'):
            is_current_brand = existing and existing.get('marca') == clean['marca']
            if not is_current_brand and not self._brand_exists(clean['marca']):
                errors['marca'] = SELECT_TAMPER_MESSAGE
        sucursal_ids = data.get('sucursal_ids')
        if sucursal_ids is not None:
            if not isinstance(sucursal_ids, list):
                errors['sucursal_id'] = 'Formato de sucursales invalido.'
            else:
                cleaned_ids = []
                for s_id in sucursal_ids:
                    try:
                        cleaned_ids.append(int(s_id))
                    except (ValueError, TypeError):
                        continue
                if not cleaned_ids:
                    errors['sucursal_id'] = 'Seleccione al menos una sucursal.'
                else:
                    clean['sucursal_ids'] = cleaned_ids
        else:
            errors['sucursal_id'] = 'Seleccione al menos una sucursal.'
        if errors:
            raise ValidationError(errors)
        return clean

    def _apply_update(self, old_codigo, clean):
        self.codigo = clean['codigo']
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '') or ''
        self.precio = clean['precio']
        columns = self._columns()
        values = {
            'codigo': self._codigo,
            'nombre_producto': self._nombre,
            'descripcion_producto': self._descripcion,
            'precio_producto': self._precio,
            'categoria': clean.get('categoria') or None,
            'marca': clean.get('marca') or None,
        }
        if clean.get('imagen') is not None:
            values['imagen_producto'] = clean['imagen']
        keys = [k for k in values if k in columns]
        params = [values[k] for k in keys] + [old_codigo]
        res = self.update("transalca",
            self.build_update_by_key_sql("productos", keys, "codigo", {"productos"}, columns),
            tuple(params))
        self._sync_sucursales(self._codigo, clean.get('sucursal_ids') or [])
        return res

    def _create(self, data):
        clean = self._validate(data)
        if data.get('imagen') is not None:
            clean['imagen'] = data['imagen']
        existing = self._get_by_codigo(clean['codigo'])
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'codigo': 'Este codigo ya esta registrado.'})
            self._apply_update(existing['codigo'], clean)
            self._reactivar(existing['codigo'])
            return existing['codigo']
        self.codigo = clean['codigo']
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '') or ''
        self.precio = clean['precio']
        columns = self._columns()
        values = {
            'codigo': self._codigo,
            'nombre_producto': self._nombre,
            'descripcion_producto': self._descripcion,
            'precio_producto': self._precio,
            'categoria': clean.get('categoria') or None,
            'marca': clean.get('marca') or None,
            'imagen_producto': clean.get('imagen') or 'default_product.png'
        }
        keys = [k for k in values if k in columns]
        pid = self.insert("transalca",
            self.build_insert_sql("productos", keys, {"productos"}, columns),
            tuple(values[k] for k in keys))
        self._sync_sucursales(self._codigo, clean.get('sucursal_ids') or [])
        return pid

    def _update_product(self, old_codigo, data):
        old_codigo = (old_codigo or '').strip()
        if not old_codigo:
            raise ValidationError({'old_codigo': 'Identificador de producto requerido.'})
        clean = self._validate(data, old_codigo)
        if clean['codigo'] != old_codigo and self._codigo_exists(clean['codigo']):
            raise ValidationError({'codigo': 'Este codigo ya esta registrado.'})
        if 'imagen' in data:
            clean['imagen'] = data['imagen']
        return self._apply_update(old_codigo, clean)

    def _soft_delete(self, codigo):
        return self.update("transalca", "UPDATE productos SET estado = 0 WHERE codigo = %s", (codigo,))

    def _toggle_estado(self, codigo):
        return self._soft_delete(codigo)

    def _codigo_exists(self, codigo, exclude_codigo=None):
        if exclude_codigo:
            result = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s AND codigo != %s AND estado = 1", (codigo, exclude_codigo))
        else:
            result = self.fetch_one("transalca", "SELECT codigo FROM productos WHERE codigo = %s AND estado = 1", (codigo,))
        return result is not None

    def _category_exists(self, nombre):
        if not nombre:
            return True
        return self.fetch_one("transalca", "SELECT nombre_categoria FROM categorias WHERE nombre_categoria = %s AND estado = 1", (nombre,)) is not None

    def _brand_exists(self, nombre):
        if not nombre:
            return True
        return self.fetch_one("transalca", "SELECT nombre_marca FROM marcas WHERE nombre_marca = %s AND estado = 1", (nombre,)) is not None

    def _supplier_exists(self, rif):
        if not rif:
            return True
        return self.fetch_one("transalca", "SELECT rif_proveedor FROM proveedores WHERE rif_proveedor = %s AND estado = 1", (rif,)) is not None

    def _reactivar(self, codigo):
        return self.update("transalca", "UPDATE productos SET estado = 1 WHERE codigo = %s", (codigo,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_all_paginated": self._get_all_paginated,
            "get_active_paginated": self._get_active_paginated,
            "get_active": self._get_active,
            "get_by_estado": self._get_by_estado,
            "get_by_codigo": self._get_by_codigo,
            "get_by_category": self._get_by_category,
            "get_by_brand": self._get_by_brand,
            "get_by_sucursal": self._get_by_sucursal,
            "search": self._search,
            "validate": self._validate,
            "create": self._create,
            "update_product": self._update_product,
            "soft_delete": self._soft_delete,
            "toggle_estado": self._toggle_estado,
            "codigo_exists": self._codigo_exists,
            "category_exists": self._category_exists,
            "brand_exists": self._brand_exists,
            "supplier_exists": self._supplier_exists,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
