from model.connection import Connection

SUCURSAL_ALIAS = (
    "s.*, s.id_sucursal AS id, s.nombre_sucursal AS nombre, s.direccion_sucursal AS direccion, "
    "s.telefono_sucursal AS telefono, s.email_sucursal AS email"
)


class SucursalModel(Connection):
    def __init__(self):
        super().__init__()
        self._nombre = None
        self._direccion = None
        self._telefono = None
        self._email = None

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._direccion = valor

    @property
    def telefono(self):
        return self._telefono

    @telefono.setter
    def telefono(self, valor):
        if valor:
            valor = str(valor).strip()
        self._telefono = valor

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        if valor:
            valor = str(valor).strip()
        self._email = valor

    def _get_all(self):
        return self.fetch_all("transalca",
            "SELECT " + SUCURSAL_ALIAS + " FROM sucursales s WHERE s.estado = 1 ORDER BY s.nombre_sucursal")

    def _get_active(self):
        return self._get_all()

    def _get_by_id(self, sucursal_id):
        return self.fetch_one("transalca",
            "SELECT " + SUCURSAL_ALIAS + " FROM sucursales s WHERE s.id_sucursal = %s", (sucursal_id,))

    def _create(self, data):
        self.nombre = data['nombre']
        self.direccion = data.get('direccion', '')
        self.telefono = data.get('telefono', '')
        self.email = data.get('email', '')
        return self.insert("transalca",
            "INSERT INTO sucursales (nombre_sucursal, direccion_sucursal, telefono_sucursal, email_sucursal) VALUES (%s, %s, %s, %s)",
            (self._nombre, self._direccion, self._telefono, self._email))

    def _update_sucursal(self, sucursal_id, data):
        self.nombre = data['nombre']
        self.direccion = data.get('direccion', '')
        self.telefono = data.get('telefono', '')
        self.email = data.get('email', '')
        return self.update("transalca",
            "UPDATE sucursales SET nombre_sucursal = %s, direccion_sucursal = %s, telefono_sucursal = %s, email_sucursal = %s WHERE id_sucursal = %s",
            (self._nombre, self._direccion, self._telefono, self._email, sucursal_id))

    def _toggle_estado(self, sucursal_id):
        return self.update("transalca",
            "UPDATE sucursales SET estado = 0 WHERE id_sucursal = %s", (sucursal_id,))

    def _soft_delete(self, sucursal_id):
        return self._toggle_estado(sucursal_id)

    def _nombre_exists(self, nombre, exclude_id=None):
        if exclude_id:
            result = self.fetch_one("transalca",
                "SELECT id_sucursal FROM sucursales WHERE nombre_sucursal = %s AND id_sucursal != %s AND estado = 1", (nombre, exclude_id))
        else:
            result = self.fetch_one("transalca",
                "SELECT id_sucursal FROM sucursales WHERE nombre_sucursal = %s AND estado = 1", (nombre,))
        return result is not None

    def _get_by_nombre(self, nombre):
        return self.fetch_one("transalca",
            "SELECT " + SUCURSAL_ALIAS + " FROM sucursales s WHERE s.nombre_sucursal = %s", (nombre,))

    def _reactivar(self, sucursal_id):
        return self.update("transalca", "UPDATE sucursales SET estado = 1 WHERE id = %s", (sucursal_id,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_id": self._get_by_id,
            "create": self._create,
            "update_sucursal": self._update_sucursal,
            "toggle_estado": self._toggle_estado,
            "soft_delete": self._soft_delete,
            "nombre_exists": self._nombre_exists,
            "get_by_nombre": self._get_by_nombre,
            "reactivar": self._reactivar,
            "email_exists_globally": self.email_exists_globally,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
