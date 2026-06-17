from model.connection import Connection
from config.validation import ValidationError, optional_text, require_text

CATEGORIA_ALIAS = (
    "c.*, c.nombre_categoria AS nombre, c.descripcion_categoria AS descripcion, c.imagen_categoria AS imagen"
)


class CategoryModel(Connection):
    def __init__(self):
        super().__init__()
        self._nombre = None
        self._descripcion = None

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

    def _get_all(self):
        return self.fetch_all("transalca",
            "SELECT " + CATEGORIA_ALIAS + ", (SELECT COUNT(*) FROM productos WHERE categoria = c.nombre_categoria AND estado = 1) as total_productos "
            "FROM categorias c WHERE c.estado = 1 ORDER BY c.nombre_categoria")

    def _get_active(self):
        return self.fetch_all("transalca",
            "SELECT " + CATEGORIA_ALIAS + " FROM categorias c WHERE c.estado = 1 ORDER BY c.nombre_categoria")

    def _get_by_nombre(self, nombre):
        return self.fetch_one("transalca",
            "SELECT " + CATEGORIA_ALIAS + " FROM categorias c WHERE c.nombre_categoria = %s", (nombre,))

    def _validate(self, data):
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=30, allow_serial=True)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=150)
        if errors:
            raise ValidationError(errors)
        return clean

    def _create(self, data):
        clean = self._validate(data)
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '')
        existing = self._get_by_nombre(self._nombre)
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'nombre': 'La categoria ya existe'})
            if 'imagen' in data:
                self.update("transalca", "UPDATE categorias SET descripcion_categoria=%s, imagen_categoria=%s, estado=1 WHERE nombre_categoria=%s",
                            (self._descripcion, data['imagen'], existing['nombre']))
            else:
                self.update("transalca", "UPDATE categorias SET descripcion_categoria=%s, estado=1 WHERE nombre_categoria=%s",
                            (self._descripcion, existing['nombre']))
            return existing['nombre']
        self.insert("transalca",
            "INSERT INTO categorias (nombre_categoria, descripcion_categoria, imagen_categoria) VALUES (%s, %s, %s)",
            (self._nombre, self._descripcion, data.get('imagen', 'product-default-parts.png')))
        return self._nombre

    def _update_category(self, old_nombre, data):
        clean = self._validate(data)
        old_nombre = (old_nombre or '').strip()
        if not old_nombre:
            raise ValidationError({'old_nombre': 'Identificador de categoria requerido'})
        if clean['nombre'] != old_nombre and self._nombre_exists(clean['nombre']):
            raise ValidationError({'nombre': 'La categoria ya existe'})
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '')
        if 'imagen' in data:
            return self.update("transalca",
                "UPDATE categorias SET nombre_categoria = %s, descripcion_categoria = %s, imagen_categoria = %s WHERE nombre_categoria = %s",
                (self._nombre, self._descripcion, data['imagen'], old_nombre))
        else:
            return self.update("transalca",
                "UPDATE categorias SET nombre_categoria = %s, descripcion_categoria = %s WHERE nombre_categoria = %s",
                (self._nombre, self._descripcion, old_nombre))

    def _soft_delete(self, nombre):
        return self.update("transalca", "UPDATE categorias SET estado = 0 WHERE nombre_categoria = %s", (nombre,))

    def _toggle_estado(self, nombre):
        return self._soft_delete(nombre)

    def _nombre_exists(self, nombre, exclude_nombre=None):
        if exclude_nombre:
            return self.fetch_one("transalca", "SELECT nombre_categoria FROM categorias WHERE nombre_categoria = %s AND nombre_categoria != %s AND estado = 1", (nombre, exclude_nombre)) is not None
        return self.fetch_one("transalca", "SELECT nombre_categoria FROM categorias WHERE nombre_categoria = %s AND estado = 1", (nombre,)) is not None

    def _reactivar(self, nombre):
        return self.update("transalca", "UPDATE categorias SET estado = 1 WHERE nombre_categoria = %s", (nombre,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_nombre": self._get_by_nombre,
            "validate": self._validate,
            "create": self._create,
            "update_category": self._update_category,
            "soft_delete": self._soft_delete,
            "toggle_estado": self._toggle_estado,
            "nombre_exists": self._nombre_exists,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
