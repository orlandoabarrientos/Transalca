from model.connection import Connection


# Estado operativo (Ocupado/Disponible) calculado por codigo segun servicios activos,
# no se almacena en la tabla.
OCUPADO_SQL = (
    "CASE WHEN EXISTS (SELECT 1 FROM servicio_mecanico sm WHERE sm.mecanico_cedula = m.cedula_mecanico "
    "AND sm.estado_servicio IN ('asignado', 'en_proceso')) THEN 'Ocupado' ELSE 'Disponible' END"
)

MECANICO_SELECT = (
    "SELECT m.cedula_mecanico AS cedula, m.cedula_prefijo, m.nombre_mecanico AS nombre, "
    "m.apellido_mecanico AS apellido, m.telefono_mecanico AS telefono, "
    "m.especialidad_mecanico AS especialidad, m.foto_perfil_mecanico AS foto_perfil, "
    "m.usuario_id, m.estado, m.created_at, " + OCUPADO_SQL + " AS estado_operativo "
    "FROM mecanicos m"
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
        return self.fetch_all("transalca",
            MECANICO_SELECT.replace(
                "FROM mecanicos m",
                ", (SELECT COUNT(*) FROM servicio_mecanico WHERE mecanico_cedula = m.cedula_mecanico) as total_servicios "
                "FROM mecanicos m")
            + " WHERE m.estado = 1 ORDER BY m.nombre_mecanico, m.apellido_mecanico")

    def _get_by_cedula(self, cedula):
        return self.fetch_one("transalca",
            MECANICO_SELECT + " WHERE m.cedula_mecanico = %s", (cedula,))

    def _get_active(self):
        return self.fetch_all("transalca",
            MECANICO_SELECT + " WHERE m.estado = 1 ORDER BY m.nombre_mecanico, m.apellido_mecanico")

    def _create(self, data):
        self.cedula = data['cedula']
        self.nombre = data['nombre']
        self.apellido = data['apellido']
        self.telefono = data.get('telefono', '')
        self.especialidad = data.get('especialidad', '')
        return self.insert("transalca",
            "INSERT INTO mecanicos (cedula_mecanico, cedula_prefijo, nombre_mecanico, apellido_mecanico, "
            "telefono_mecanico, especialidad_mecanico, foto_perfil_mecanico) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (self._cedula, data.get('cedula_prefijo'), self._nombre, self._apellido,
             self._telefono, self._especialidad,
             data.get('foto_perfil', 'default.png')))

    def _update_mechanic(self, old_cedula, data):
        self.cedula = data['cedula']
        self.nombre = data['nombre']
        self.apellido = data['apellido']
        self.telefono = data.get('telefono', '')
        self.especialidad = data.get('especialidad', '')
        sets = ["cedula_mecanico=%s", "cedula_prefijo=%s", "nombre_mecanico=%s", "apellido_mecanico=%s",
                "telefono_mecanico=%s", "especialidad_mecanico=%s"]
        params = [self._cedula, data.get('cedula_prefijo'), self._nombre,
                  self._apellido, self._telefono, self._especialidad]
        if 'foto_perfil' in data and data['foto_perfil'] is not None:
            sets.append("foto_perfil_mecanico=%s")
            params.append(data['foto_perfil'])
        params.append(old_cedula)
        return self.update("transalca",
            "UPDATE mecanicos SET " + ", ".join(sets) + " WHERE cedula_mecanico=%s",
            tuple(params))

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
        return self.update("transalca", "UPDATE mecanicos SET estado = 1 WHERE cedula = %s", (cedula,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_cedula": self._get_by_cedula,
            "get_active": self._get_active,
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
