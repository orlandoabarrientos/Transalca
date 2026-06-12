from model.connection import Connection

PROVEEDOR_ALIAS = (
    "p.*, p.rif_proveedor AS rif, p.nombre_proveedor AS nombre, p.telefono_proveedor AS telefono, "
    "p.email_proveedor AS email, p.direccion_proveedor AS direccion"
)


class SupplierModel(Connection):
    def __init__(self):
        super().__init__()
        self._rif = None
        self._nombre = None
        self._telefono = None
        self._email = None
        self._direccion = None

    @property
    def rif(self):
        return self._rif

    @rif.setter
    def rif(self, valor):
        if valor:
            valor = str(valor).strip()
        self._rif = valor

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

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

    @property
    def direccion(self):
        return self._direccion

    @direccion.setter
    def direccion(self, valor):
        if valor:
            valor = str(valor).strip()
        self._direccion = valor

    def _get_all(self):
        return self.fetch_all("transalca",
            "SELECT " + PROVEEDOR_ALIAS + ", "
            "(SELECT COUNT(*) FROM ordenes_compra WHERE proveedor_rif = p.rif_proveedor) as total_ordenes "
            "FROM proveedores p WHERE p.estado = 1 ORDER BY p.nombre_proveedor")

    def _get_active(self):
        return self.fetch_all("transalca",
            "SELECT " + PROVEEDOR_ALIAS + " FROM proveedores p WHERE p.estado = 1 ORDER BY p.nombre_proveedor")

    def _get_by_rif(self, rif):
        return self.fetch_one("transalca",
            "SELECT " + PROVEEDOR_ALIAS + " FROM proveedores p WHERE p.rif_proveedor = %s", (rif,))

    def _create(self, data):
        self.rif = data['rif']
        self.nombre = data['nombre']
        self.telefono = data.get('telefono', '')
        self.email = data.get('email', '')
        self.direccion = data.get('direccion', '')
        return self.insert("transalca",
            "INSERT INTO proveedores (rif_proveedor, rif_prefijo, nombre_proveedor, telefono_proveedor, email_proveedor, direccion_proveedor) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (self._rif, data.get('rif_prefijo'), self._nombre,
             self._telefono, self._email, self._direccion))

    def _update_supplier(self, old_rif, data):
        self.rif = data['rif']
        self.nombre = data['nombre']
        self.telefono = data.get('telefono', '')
        self.email = data.get('email', '')
        self.direccion = data.get('direccion', '')
        return self.update("transalca",
            "UPDATE proveedores SET rif_proveedor = %s, rif_prefijo = %s, nombre_proveedor = %s, "
            "telefono_proveedor = %s, email_proveedor = %s, direccion_proveedor = %s WHERE rif_proveedor = %s",
            (self._rif, data.get('rif_prefijo'), self._nombre,
             self._telefono, self._email, self._direccion, old_rif))

    def _soft_delete(self, rif):
        return self.update("transalca",
            "UPDATE proveedores SET estado = 0 WHERE rif_proveedor = %s", (rif,))

    def _toggle_estado(self, rif):
        return self._soft_delete(rif)

    def _rif_exists(self, rif, exclude_rif=None):
        if exclude_rif:
            result = self.fetch_one("transalca",
                "SELECT rif_proveedor FROM proveedores WHERE rif_proveedor = %s AND rif_proveedor != %s AND estado = 1", (rif, exclude_rif))
        else:
            result = self.fetch_one("transalca",
                "SELECT rif_proveedor FROM proveedores WHERE rif_proveedor = %s AND estado = 1", (rif,))
        return result is not None

    def _reactivar(self, rif):
        return self.update("transalca", "UPDATE proveedores SET estado = 1 WHERE rif = %s", (rif,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_rif": self._get_by_rif,
            "create": self._create,
            "update_supplier": self._update_supplier,
            "soft_delete": self._soft_delete,
            "toggle_estado": self._toggle_estado,
            "rif_exists": self._rif_exists,
            "reactivar": self._reactivar,
            "email_exists_globally": self.email_exists_globally,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
