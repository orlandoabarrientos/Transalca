from model.connection import Connection
from config.validation import (
    SELECT_TAMPER_MESSAGE,
    ValidationError,
    normalize_decimal,
    normalize_int,
    optional_text,
    require_text,
)

SERVICIO_ALIAS = (
    "s.*, s.id_servicio AS id, s.nombre_servicio AS nombre, s.descripcion_servicio AS descripcion, "
    "s.precio_servicio AS precio, s.tipo_servicio AS tipo"
)


class ServiceModel(Connection):
    def __init__(self):
        super().__init__()
        self._nombre = None
        self._descripcion = None
        self._tipo = None
        self._precio = None

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
    def tipo(self):
        return self._tipo

    @tipo.setter
    def tipo(self, valor):
        if valor:
            valor = str(valor).strip()
        self._tipo = valor

    @property
    def precio(self):
        return self._precio

    @precio.setter
    def precio(self, valor):
        self._precio = float(valor)

    def _get_all(self):
        return self.fetch_all("transalca",
            "SELECT " + SERVICIO_ALIAS + ", GROUP_CONCAT(ss.sucursal_id ORDER BY ss.sucursal_id) as sucursal_ids, "
            "GROUP_CONCAT(su.nombre_sucursal ORDER BY su.nombre_sucursal SEPARATOR ', ') as sucursal_nombre "
            "FROM servicios s "
            "LEFT JOIN servicio_sucursal ss ON s.id_servicio = ss.servicio_id AND ss.estado = 1 "
            "LEFT JOIN sucursales su ON ss.sucursal_id = su.id_sucursal "
            "WHERE s.estado = 1 GROUP BY s.id_servicio ORDER BY s.nombre_servicio")

    def _get_active(self):
        return self._get_all()

    def _get_by_id(self, sid):
        return self.fetch_one("transalca",
            "SELECT " + SERVICIO_ALIAS + ", GROUP_CONCAT(ss.sucursal_id ORDER BY ss.sucursal_id) as sucursal_ids, "
            "GROUP_CONCAT(su.nombre_sucursal ORDER BY su.nombre_sucursal SEPARATOR ', ') as sucursal_nombre "
            "FROM servicios s "
            "LEFT JOIN servicio_sucursal ss ON s.id_servicio = ss.servicio_id AND ss.estado = 1 "
            "LEFT JOIN sucursales su ON ss.sucursal_id = su.id_sucursal "
            "WHERE s.id_servicio = %s GROUP BY s.id_servicio", (sid,))

    def _get_by_sucursal(self, suc_id):
        return self.fetch_all("transalca",
            "SELECT " + SERVICIO_ALIAS + ", su.nombre_sucursal as sucursal_nombre FROM servicios s "
            "INNER JOIN servicio_sucursal ss ON s.id_servicio = ss.servicio_id "
            "INNER JOIN sucursales su ON ss.sucursal_id = su.id_sucursal "
            "WHERE ss.sucursal_id = %s AND ss.estado = 1 AND s.estado = 1 ORDER BY s.nombre_servicio", (suc_id,))

    def _sucursal_exists(self, sucursal_id):
        return self.fetch_one("transalca", "SELECT id_sucursal FROM sucursales WHERE id_sucursal = %s AND estado = 1", (sucursal_id,)) is not None

    def _sync_sucursales(self, sid, sucursal_ids):
        ids = []
        for value in sucursal_ids or []:
            try:
                parsed = int(value)
            except (TypeError, ValueError):
                continue
            if parsed not in ids:
                ids.append(parsed)
        self.update("transalca", "DELETE FROM servicio_sucursal WHERE servicio_id = %s", (sid,))
        for sucursal_id in ids:
            self.insert("transalca",
                "INSERT INTO servicio_sucursal (servicio_id, sucursal_id) VALUES (%s, %s)",
                (sid, sucursal_id))

    def _validate(self, data, current_id=None):
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=200, allow_serial=False)
        clean['descripcion'] = optional_text(errors, 'descripcion', data.get('descripcion'), 'La descripcion', max_len=1000)
        clean['precio'] = normalize_decimal(errors, 'precio', data.get('precio'), 'El precio')
        clean['duracion_estimada'] = normalize_int(errors, 'duracion_estimada', data.get('duracion_estimada') or 60, 'La duracion', min_value=1, max_value=1440)
        tipo = (data.get('tipo') or '').strip().lower()
        if not tipo:
            errors['tipo'] = 'El tipo de servicio es obligatorio.'
        elif tipo not in ('alineacion', 'rotacion', 'balanceo', 'cambio_aceite', 'general'):
            errors['tipo'] = SELECT_TAMPER_MESSAGE
        else:
            clean['tipo'] = tipo
        current = self._get_by_id(current_id) if current_id else None
        current_suc_ids = [int(v) for v in (current.get('sucursal_ids') or '').split(',') if v] if current else []
        raw_ids = data.get('sucursal_ids')
        if raw_ids is None:
            raw_ids = [data.get('sucursal_id')] if data.get('sucursal_id') else []
        if isinstance(raw_ids, str):
            raw_ids = [v for v in raw_ids.split(',') if v]
        clean['sucursal_ids'] = []
        for raw_id in raw_ids:
            try:
                sucursal_id = int(raw_id)
            except (TypeError, ValueError):
                errors['sucursal_id'] = SELECT_TAMPER_MESSAGE
            else:
                is_current_suc = sucursal_id in current_suc_ids
                if not is_current_suc and not self._sucursal_exists(sucursal_id):
                    errors['sucursal_id'] = SELECT_TAMPER_MESSAGE
                elif sucursal_id not in clean['sucursal_ids']:
                    clean['sucursal_ids'].append(sucursal_id)
        if not clean['sucursal_ids'] and not errors.get('sucursal_id'):
            errors['sucursal_id'] = 'Debe seleccionar al menos una sucursal.'
        if errors:
            raise ValidationError(errors)
        return clean

    def _apply_fields(self, clean):
        self.nombre = clean['nombre']
        self.descripcion = clean.get('descripcion', '') or ''
        self.tipo = clean.get('tipo', 'general')
        self.precio = clean['precio']

    def _create(self, data):
        clean = self._validate(data)
        self._apply_fields(clean)
        duration = clean.get('duracion_estimada', 60)
        existing = self._get_by_nombre(clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'nombre': 'Ya existe un servicio con ese nombre.'})
            self.update("transalca",
                "UPDATE servicios SET nombre_servicio=%s, descripcion_servicio=%s, tipo_servicio=%s, precio_servicio=%s, duracion_estimada=%s, estado=1 WHERE id_servicio=%s",
                (self._nombre, self._descripcion, self._tipo, self._precio, str(duration).strip(), existing['id']))
            self._sync_sucursales(existing['id'], clean.get('sucursal_ids') or [])
            return existing['id']
        sid = self.insert("transalca",
            "INSERT INTO servicios (nombre_servicio, descripcion_servicio, tipo_servicio, precio_servicio, duracion_estimada) VALUES (%s, %s, %s, %s, %s)",
            (self._nombre, self._descripcion, self._tipo, self._precio, str(duration).strip()))
        self._sync_sucursales(sid, clean.get('sucursal_ids') or [])
        return sid

    def _update_service(self, sid, data):
        clean = self._validate(data, current_id=sid)
        if self._nombre_exists(clean['nombre'], sid):
            raise ValidationError({'nombre': 'Ya existe un servicio con ese nombre.'})
        self._apply_fields(clean)
        duration = clean.get('duracion_estimada', 60)
        result = self.update("transalca",
            "UPDATE servicios SET nombre_servicio = %s, descripcion_servicio = %s, tipo_servicio = %s, precio_servicio = %s, duracion_estimada = %s WHERE id_servicio = %s",
            (self._nombre, self._descripcion, self._tipo, self._precio, str(duration).strip(), sid))
        self._sync_sucursales(sid, clean.get('sucursal_ids') or [])
        return result

    def _soft_delete(self, sid):
        return self.update("transalca", "UPDATE servicios SET estado = 0 WHERE id_servicio = %s", (sid,))

    def _toggle_estado(self, sid):
        return self._soft_delete(sid)

    def _nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca", "SELECT id_servicio FROM servicios WHERE nombre_servicio = %s AND id_servicio != %s AND estado = 1", (nombre, exclude_id))
        else:
            result = self.fetch_one("transalca", "SELECT id_servicio FROM servicios WHERE nombre_servicio = %s AND estado = 1", (nombre,))
        return result is not None

    def _get_by_nombre(self, nombre):
        return self.fetch_one("transalca",
            "SELECT " + SERVICIO_ALIAS + " FROM servicios s WHERE s.nombre_servicio = %s", (nombre,))

    def _reactivar(self, sid):
        return self.update("transalca", "UPDATE servicios SET estado = 1 WHERE id_servicio = %s", (sid,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_id": self._get_by_id,
            "get_by_sucursal": self._get_by_sucursal,
            "sucursal_exists": self._sucursal_exists,
            "create": self._create,
            "update_service": self._update_service,
            "soft_delete": self._soft_delete,
            "toggle_estado": self._toggle_estado,
            "nombre_exists": self._nombre_exists,
            "get_by_nombre": self._get_by_nombre,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
