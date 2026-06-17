import re

from model.connection import Connection
from config.validation import (
    ValidationError,
    normalize_int,
    optional_text,
    require_text,
)

SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{1,99}$")
RUTA_RE = re.compile(r"^/[A-Za-z0-9_\-/]*$")
MODULO_SELECT = (
    "SELECT id_modulo AS id, nombre_modulo AS nombre, titulo_modulo AS titulo, "
    "descripcion_modulo AS descripcion, ruta_modulo AS ruta, icono_modulo AS icono, "
    "grupo_modulo AS grupo, orden_modulo AS orden, en_sidebar, publico_modulo AS publico, "
    "estado_modulo AS estado, created_at, updated_at FROM modulos"
)


class ModuloModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_all(self):
        return self.fetch_all("mantenimiento",
            MODULO_SELECT + " WHERE estado_modulo = 1 ORDER BY grupo_modulo, orden_modulo, titulo_modulo")

    def _get_by_id(self, modulo_id):
        return self.fetch_one("mantenimiento", MODULO_SELECT + " WHERE id_modulo = %s", (modulo_id,))

    def _get_by_nombre(self, nombre):
        return self.fetch_one("mantenimiento", MODULO_SELECT + " WHERE nombre_modulo = %s", (nombre,))

    def _get_by_ruta(self, ruta):
        return self.fetch_one("mantenimiento", MODULO_SELECT + " WHERE ruta_modulo = %s", (ruta,))

    def _get_sidebar_modules(self):
        return self.fetch_all("mantenimiento",
            "SELECT nombre_modulo AS nombre, titulo_modulo AS titulo, ruta_modulo AS ruta, "
            "icono_modulo AS icono, grupo_modulo AS grupo, orden_modulo AS orden, publico_modulo AS publico "
            "FROM modulos WHERE estado_modulo = 1 AND en_sidebar = 1 AND ruta_modulo IS NOT NULL "
            "ORDER BY orden_modulo, titulo_modulo")

    def _get_permission_modules(self):
        return self.fetch_all("mantenimiento",
            "SELECT nombre_modulo AS modulo, titulo_modulo AS titulo, grupo_modulo AS grupo "
            "FROM modulos WHERE estado_modulo = 1 ORDER BY grupo_modulo, orden_modulo, titulo_modulo")

    def _nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            return self.fetch_one("mantenimiento", "SELECT id_modulo FROM modulos WHERE nombre_modulo = %s AND id_modulo != %s AND estado_modulo = 1", (nombre, exclude_id)) is not None
        return self.fetch_one("mantenimiento", "SELECT id_modulo FROM modulos WHERE nombre_modulo = %s AND estado_modulo = 1", (nombre,)) is not None

    def _ruta_exists(self, ruta, exclude_id=None):
        if exclude_id:
            return self.fetch_one("mantenimiento", "SELECT id_modulo FROM modulos WHERE ruta_modulo = %s AND id_modulo != %s AND estado_modulo = 1", (ruta, exclude_id)) is not None
        return self.fetch_one("mantenimiento", "SELECT id_modulo FROM modulos WHERE ruta_modulo = %s AND estado_modulo = 1", (ruta,)) is not None

    def _validate(self, data, current_id=None):
        errors = {}
        clean = {}
        nombre = (data.get('nombre') or '').strip().lower()
        if not nombre:
            errors['nombre'] = 'La clave del modulo es obligatoria.'
        elif not SLUG_RE.match(nombre):
            errors['nombre'] = 'La clave solo permite minusculas, numeros y guion bajo (ej: ordenes_compra).'
        clean['nombre'] = nombre
        clean['titulo'] = require_text(errors, 'titulo', data.get('titulo'), 'El nombre del modulo', min_len=2, max_len=150, allow_serial=True)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=255, allow_serial=True)
        ruta = (data.get('ruta') or '').strip()
        if not ruta:
            errors['ruta'] = 'La ruta es obligatoria.'
        elif len(ruta) > 150:
            errors['ruta'] = 'La ruta no puede superar 150 caracteres.'
        elif '..' in ruta or '://' in ruta or '<' in ruta or '>' in ruta or ' ' in ruta:
            errors['ruta'] = 'La ruta contiene caracteres no permitidos.'
        elif not RUTA_RE.match(ruta):
            errors['ruta'] = 'La ruta debe iniciar con / y ser una ruta interna valida.'
        clean['ruta'] = ruta
        clean['icono'] = (data.get('icono') or '').strip() or 'bi bi-app'
        if len(clean['icono']) > 60 or '<' in clean['icono'] or '>' in clean['icono']:
            errors['icono'] = 'El icono no es valido.'
        clean['grupo'] = require_text(errors, 'grupo', data.get('grupo'), 'El grupo', min_len=2, max_len=60, allow_serial=True)
        clean['orden'] = normalize_int(errors, 'orden', data.get('orden') if data.get('orden') not in (None, '') else 0, 'El orden', min_value=0, max_value=9999)
        clean['en_sidebar'] = 1 if str(data.get('en_sidebar', 1)) in ('1', 'true', 'True', 'on') else 0
        clean['publico'] = 1 if str(data.get('publico', 0)) in ('1', 'true', 'True', 'on') else 0
        clean['estado'] = 0 if str(data.get('estado', 1)) in ('0', 'false', 'False') else 1
        if errors:
            raise ValidationError(errors)
        if nombre and self._nombre_exists(nombre, current_id):
            raise ValidationError({'nombre': 'Ya existe un modulo con esa clave.'})
        if ruta and self._ruta_exists(ruta, current_id):
            raise ValidationError({'ruta': 'Ya existe un modulo con esa ruta.'})
        return clean

    def _create(self, data):
        clean = self._validate(data)
        existing = self._get_by_nombre(clean['nombre'])
        if existing and existing['estado'] == 0:
            return self._apply_update(existing['id'], clean, reactivate=True)
        return self.insert("mantenimiento",
            "INSERT INTO modulos (nombre_modulo, titulo_modulo, descripcion_modulo, ruta_modulo, icono_modulo, "
            "grupo_modulo, orden_modulo, en_sidebar, publico_modulo, estado_modulo) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (clean['nombre'], clean['titulo'], clean['descripcion'] or None, clean['ruta'], clean['icono'],
             clean['grupo'], clean['orden'], clean['en_sidebar'], clean['publico'], clean['estado']))

    def _update_modulo(self, modulo_id, data):
        clean = self._validate(data, current_id=modulo_id)
        return self._apply_update(modulo_id, clean)

    def _apply_update(self, modulo_id, clean, reactivate=False):
        estado = 1 if reactivate else clean['estado']
        return self.update("mantenimiento",
            "UPDATE modulos SET nombre_modulo=%s, titulo_modulo=%s, descripcion_modulo=%s, ruta_modulo=%s, "
            "icono_modulo=%s, grupo_modulo=%s, orden_modulo=%s, en_sidebar=%s, publico_modulo=%s, estado_modulo=%s "
            "WHERE id_modulo=%s",
            (clean['nombre'], clean['titulo'], clean['descripcion'] or None, clean['ruta'], clean['icono'],
             clean['grupo'], clean['orden'], clean['en_sidebar'], clean['publico'], estado, modulo_id))

    def _soft_delete(self, modulo_id):
        item = self._get_by_id(modulo_id)
        if not item:
            return None
        self.update("mantenimiento", "UPDATE modulos SET estado_modulo = 0 WHERE id_modulo = %s", (modulo_id,))
        return 0

    def _reactivar(self, modulo_id):
        return self.update("mantenimiento", "UPDATE modulos SET estado_modulo = 1 WHERE id_modulo = %s", (modulo_id,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "get_by_nombre": self._get_by_nombre,
            "get_by_ruta": self._get_by_ruta,
            "get_sidebar_modules": self._get_sidebar_modules,
            "get_permission_modules": self._get_permission_modules,
            "nombre_exists": self._nombre_exists,
            "ruta_exists": self._ruta_exists,
            "validate": self._validate,
            "create": self._create,
            "update_modulo": self._update_modulo,
            "soft_delete": self._soft_delete,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
