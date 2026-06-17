from model.connection import Connection
from config.validation import ValidationError, optional_text, require_text

MARCA_ALIAS = "m.*, m.nombre_marca AS nombre, m.descripcion_marca AS descripcion"


class BrandModel(Connection):
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
            "SELECT " + MARCA_ALIAS + ", (SELECT COUNT(*) FROM productos WHERE marca = m.nombre_marca AND estado = 1) as total_productos "
            "FROM marcas m WHERE m.estado = 1 ORDER BY m.nombre_marca")

    def _get_active(self):
        return self.fetch_all("transalca",
            "SELECT " + MARCA_ALIAS + " FROM marcas m WHERE m.estado = 1 ORDER BY m.nombre_marca")

    def _get_by_nombre(self, nombre):
        return self.fetch_one("transalca",
            "SELECT " + MARCA_ALIAS + " FROM marcas m WHERE m.nombre_marca = %s", (nombre,))

    def _validate(self, data):
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=30, allow_serial=True)
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
                raise ValidationError({'nombre': 'La marca ya existe'})
            self.update("transalca", "UPDATE marcas SET descripcion_marca = %s, estado = 1 WHERE nombre_marca = %s",
                        (self._descripcion, existing['nombre']))
            return existing['nombre']
        self.insert("transalca",
            "INSERT INTO marcas (nombre_marca, descripcion_marca) VALUES (%s, %s)",
            (self._nombre, self._descripcion))
        return self._nombre

    def _update_brand(self, old_nombre, data):
        clean = self._validate(data)
        old_nombre = (old_nombre or '').strip()
        if not old_nombre:
            raise ValidationError({'old_nombre': 'Identificador de marca requerido'})
        if clean['nombre'] != old_nombre and self._nombre_exists(clean['nombre']):
            raise ValidationError({'nombre': 'La marca ya existe'})
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '')
        return self.update("transalca",
            "UPDATE marcas SET nombre_marca = %s, descripcion_marca = %s WHERE nombre_marca = %s",
            (self._nombre, self._descripcion, old_nombre))

    def _soft_delete(self, nombre):
        return self.update("transalca", "UPDATE marcas SET estado = 0 WHERE nombre_marca = %s", (nombre,))

    def _toggle_estado(self, nombre):
        return self._soft_delete(nombre)

    def _nombre_exists(self, nombre, exclude_nombre=None):
        if exclude_nombre:
            return self.fetch_one("transalca", "SELECT nombre_marca FROM marcas WHERE nombre_marca = %s AND nombre_marca != %s AND estado = 1", (nombre, exclude_nombre)) is not None
        return self.fetch_one("transalca", "SELECT nombre_marca FROM marcas WHERE nombre_marca = %s AND estado = 1", (nombre,)) is not None

    def _reactivar(self, nombre):
        return self.update("transalca", "UPDATE marcas SET estado = 1 WHERE nombre = %s", (nombre,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_nombre": self._get_by_nombre,
            "create": self._create,
            "update_brand": self._update_brand,
            "soft_delete": self._soft_delete,
            "toggle_estado": self._toggle_estado,
            "nombre_exists": self._nombre_exists,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
