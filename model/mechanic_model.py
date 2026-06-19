from model.connection import Connection
from config.validation import ValidationError, normalize_cedula, normalize_phone, optional_text, require_text


MECANICO_LIST_SQL = (
    "SELECT m.cedula_mecanico AS cedula, m.cedula_prefijo, m.nombre_mecanico AS nombre, "
    "m.apellido_mecanico AS apellido, m.telefono_mecanico AS telefono, "
    "m.especialidad_mecanico AS especialidad, m.foto_perfil_mecanico AS foto_perfil, "
    "m.usuario_id, m.estado, m.created_at, "
    "CASE WHEN EXISTS (SELECT 1 FROM servicio_mecanico sm WHERE sm.mecanico_cedula = m.cedula_mecanico "
    "AND sm.estado_servicio IN ('asignado', 'en_proceso')) THEN 'Ocupado' ELSE 'Disponible' END AS estado_operativo, "
    "(SELECT COUNT(*) FROM servicio_mecanico WHERE mecanico_cedula = m.cedula_mecanico) as total_servicios "
    "FROM mecanicos m WHERE m.estado = 1 ORDER BY m.nombre_mecanico, m.apellido_mecanico"
)
MECANICO_BY_CEDULA_SQL = (
    "SELECT m.cedula_mecanico AS cedula, m.cedula_prefijo, m.nombre_mecanico AS nombre, "
    "m.apellido_mecanico AS apellido, m.telefono_mecanico AS telefono, "
    "m.especialidad_mecanico AS especialidad, m.foto_perfil_mecanico AS foto_perfil, "
    "m.usuario_id, m.estado, m.created_at, "
    "CASE WHEN EXISTS (SELECT 1 FROM servicio_mecanico sm WHERE sm.mecanico_cedula = m.cedula_mecanico "
    "AND sm.estado_servicio IN ('asignado', 'en_proceso')) THEN 'Ocupado' ELSE 'Disponible' END AS estado_operativo "
    "FROM mecanicos m WHERE m.cedula_mecanico = %s"
)
MECANICO_ACTIVE_SQL = (
    "SELECT m.cedula_mecanico AS cedula, m.cedula_prefijo, m.nombre_mecanico AS nombre, "
    "m.apellido_mecanico AS apellido, m.telefono_mecanico AS telefono, "
    "m.especialidad_mecanico AS especialidad, m.foto_perfil_mecanico AS foto_perfil, "
    "m.usuario_id, m.estado, m.created_at, "
    "CASE WHEN EXISTS (SELECT 1 FROM servicio_mecanico sm WHERE sm.mecanico_cedula = m.cedula_mecanico "
    "AND sm.estado_servicio IN ('asignado', 'en_proceso')) THEN 'Ocupado' ELSE 'Disponible' END AS estado_operativo "
    "FROM mecanicos m WHERE m.estado = 1 ORDER BY m.nombre_mecanico, m.apellido_mecanico"
)


class MechanicModel(Connection):
    COLUMN_MAP = {
        'cedula': 'cedula_mecanico',
        'nombre': 'nombre_mecanico',
        'apellido': 'apellido_mecanico',
        'telefono': 'telefono_mecanico',
        'especialidad': 'especialidad_mecanico',
        'foto_perfil': 'foto_perfil_mecanico',
    }

    def __init__(self):
        super().__init__()
        self._cedula = None
        self._nombre = None
        self._apellido = None
        self._telefono = None
        self._especialidad = None

    @property
    def cedula(self):
        return self._cedula

    @cedula.setter
    def cedula(self, valor):
        if valor:
            valor = str(valor).strip()
        self._cedula = valor

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def apellido(self):
        return self._apellido

    @apellido.setter
    def apellido(self, valor):
        if valor:
            valor = str(valor).strip()
        self._apellido = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor:
            valor = str(valor).strip()
        self._telefono = valor

    @property
    def especialidad(self):
        return self._especialidad

    @especialidad.setter
    def especialidad(self, valor):
        if valor:
            valor = str(valor).strip()
        self._especialidad = valor

    def _get_all(self):
        return self.fetch_all("transalca", MECANICO_LIST_SQL)

    def _get_by_cedula(self, cedula):
        return self.fetch_one("transalca", MECANICO_BY_CEDULA_SQL, (cedula,))

    def _get_active(self):
        return self.fetch_all("transalca", MECANICO_ACTIVE_SQL)

    def _validate(self, data):
        errors = {}
        cedula, cedula_prefijo, _ = normalize_cedula(errors, data)
        clean = {
            'cedula': cedula,
            'cedula_prefijo': cedula_prefijo,
            'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=2, max_len=60, person=True),
            'apellido': require_text(errors, 'apellido', data.get('apellido'), 'El apellido', min_len=2, max_len=60, person=True),
            'telefono': normalize_phone(errors, data.get('telefono'), required=False),
            'especialidad': optional_text(errors, 'especialidad', data.get('especialidad'), 'La especialidad', max_len=120, allow_serial=False),
        }
        if errors:
            raise ValidationError(errors)
        return clean

    def _create(self, data):
        clean = self._validate(data)
        data = {**data, **clean}
        self.cedula = clean['cedula']
        self.nombre = clean['nombre']
        self.apellido = clean['apellido']
        self.telefono = clean.get('telefono', '') or ''
        self.especialidad = clean.get('especialidad', '') or ''
        existing = self._get_by_cedula(self._cedula)
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'cedula': 'Esta cedula ya esta registrada.'})
            if data.get('foto_perfil'):
                self.update("transalca",
                    "UPDATE mecanicos SET cedula_prefijo=%s, nombre_mecanico=%s, apellido_mecanico=%s, telefono_mecanico=%s, especialidad_mecanico=%s, foto_perfil_mecanico=%s, estado=1 WHERE cedula_mecanico=%s",
                    (clean.get('cedula_prefijo'), self._nombre, self._apellido, self._telefono, self._especialidad, data['foto_perfil'], existing['cedula']))
            else:
                self.update("transalca",
                    "UPDATE mecanicos SET cedula_prefijo=%s, nombre_mecanico=%s, apellido_mecanico=%s, telefono_mecanico=%s, especialidad_mecanico=%s, estado=1 WHERE cedula_mecanico=%s",
                    (clean.get('cedula_prefijo'), self._nombre, self._apellido, self._telefono, self._especialidad, existing['cedula']))
            return existing['cedula']
        self.insert("transalca",
            "INSERT INTO mecanicos (cedula_mecanico, cedula_prefijo, nombre_mecanico, apellido_mecanico, "
            "telefono_mecanico, especialidad_mecanico, foto_perfil_mecanico) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (self._cedula, clean.get('cedula_prefijo'), self._nombre, self._apellido,
             self._telefono, self._especialidad,
             data.get('foto_perfil', 'default.png')))
        return self._cedula

    def _update_mechanic(self, old_cedula, data):
        clean = self._validate(data)
        old_cedula = (old_cedula or '').strip()
        if not old_cedula:
            raise ValidationError({'old_cedula': 'Identificador requerido.'})
        if clean['cedula'] != old_cedula and self._cedula_exists(clean['cedula']):
            raise ValidationError({'cedula': 'Esta cedula ya esta registrada.'})
        self.cedula = clean['cedula']
        self.nombre = clean['nombre']
        self.apellido = clean['apellido']
        self.telefono = clean.get('telefono', '') or ''
        self.especialidad = clean.get('especialidad', '') or ''
        data = {**data, **clean}
        if 'foto_perfil' in data and data['foto_perfil'] is not None:
            return self.update("transalca",
                "UPDATE mecanicos SET cedula_mecanico=%s, cedula_prefijo=%s, nombre_mecanico=%s, apellido_mecanico=%s, telefono_mecanico=%s, especialidad_mecanico=%s, foto_perfil_mecanico=%s WHERE cedula_mecanico=%s",
                (self._cedula, data.get('cedula_prefijo'), self._nombre, self._apellido, self._telefono, self._especialidad, data['foto_perfil'], old_cedula))
        return self.update("transalca",
            "UPDATE mecanicos SET cedula_mecanico=%s, cedula_prefijo=%s, nombre_mecanico=%s, apellido_mecanico=%s, telefono_mecanico=%s, especialidad_mecanico=%s WHERE cedula_mecanico=%s",
            (self._cedula, data.get('cedula_prefijo'), self._nombre, self._apellido, self._telefono, self._especialidad, old_cedula))

    def _soft_delete(self, cedula):
        return self.update("transalca", "UPDATE mecanicos SET estado = 0 WHERE cedula_mecanico = %s", (cedula,))

    def _toggle_estado(self, cedula):
        item = self._get_by_cedula(cedula)
        if not item:
            return None
        new_estado = 0 if int(item.get('estado') or 0) == 1 else 1
        self.update("transalca", "UPDATE mecanicos SET estado = %s WHERE cedula_mecanico = %s", (new_estado, cedula))
        return new_estado

    def _cedula_exists(self, cedula, exclude_cedula=None):
        if exclude_cedula:
            return self.fetch_one("transalca",
                "SELECT cedula_mecanico FROM mecanicos WHERE cedula_mecanico = %s AND cedula_mecanico != %s AND estado = 1",
                (cedula, exclude_cedula)) is not None
        return self.fetch_one("transalca",
            "SELECT cedula_mecanico FROM mecanicos WHERE cedula_mecanico = %s AND estado = 1", (cedula,)) is not None

    def _get_service_history(self, cedula):
        return self.fetch_all("transalca",
            "SELECT sm.*, sm.id_servicio_mecanico AS id, sm.estado_servicio AS estado, sm.fecha_servicio AS fecha, "
            "sm.observaciones_servicio AS observaciones, s.nombre_servicio as servicio_nombre "
            "FROM servicio_mecanico sm INNER JOIN servicios s ON sm.servicio_id = s.id_servicio "
            "WHERE sm.mecanico_cedula = %s ORDER BY sm.fecha_servicio DESC",
            (cedula,))

    def _reactivar(self, cedula):
        return self.update("transalca", "UPDATE mecanicos SET estado = 1 WHERE cedula_mecanico = %s", (cedula,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_cedula": self._get_by_cedula,
            "get_active": self._get_active,
            "validate": self._validate,
            "create": self._create,
            "update_mechanic": self._update_mechanic,
            "soft_delete": self._soft_delete,
            "toggle_estado": self._toggle_estado,
            "cedula_exists": self._cedula_exists,
            "get_service_history": self._get_service_history,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
