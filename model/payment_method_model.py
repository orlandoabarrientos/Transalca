from model.connection import Connection
from config.validation import ValidationError, require_text

METODO_PAGO_ALIAS = "mp.*, mp.id_metodo_pago AS id, mp.nombre_metodo_pago AS nombre, mp.datos_metodo_pago AS datos_pago"


class PaymentMethodModel(Connection):
    def __init__(self):
        super().__init__()
        self._nombre = None
        self._moneda = None
        self._permite_credito = None
        self._datos_pago = None

    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, valor):
        if valor:
            valor = str(valor).strip()
        self._nombre = valor

    @property
    def moneda(self):
        return self._moneda

    @moneda.setter
    def moneda(self, valor):
        if valor:
            valor = str(valor).strip().lower()
        self._moneda = valor

    @property
    def permite_credito(self):
        return self._permite_credito

    @permite_credito.setter
    def permite_credito(self, valor):
        self._permite_credito = int(valor or 0)

    @property
    def datos_pago(self):
        return self._datos_pago

    @datos_pago.setter
    def datos_pago(self, valor):
        if valor:
            valor = str(valor).strip()
        self._datos_pago = valor

    def _get_all(self):
        return self.fetch_all("transalca",
            "SELECT " + METODO_PAGO_ALIAS + " "
            "FROM metodos_pago mp "
            "WHERE mp.estado = 1 ORDER BY mp.created_at DESC")

    def _get_active(self):
        return self.fetch_all("transalca",
            "SELECT id_metodo_pago AS id, nombre_metodo_pago AS nombre, permite_credito, moneda, datos_metodo_pago AS datos_pago "
            "FROM metodos_pago WHERE estado = 1 ORDER BY nombre_metodo_pago")

    def _get_by_id(self, method_id):
        return self.fetch_one("transalca",
            "SELECT " + METODO_PAGO_ALIAS + " FROM metodos_pago mp WHERE mp.id_metodo_pago = %s", (method_id,))

    def _name_exists(self, nombre, exclude_id=None):
        value = (nombre or '').strip()
        if not value:
            return False
        if exclude_id:
            return self.fetch_one("transalca",
                "SELECT id_metodo_pago FROM metodos_pago WHERE LOWER(nombre_metodo_pago) = LOWER(%s) AND id_metodo_pago != %s AND estado = 1",
                (value, exclude_id)) is not None
        return self.fetch_one("transalca",
            "SELECT id_metodo_pago FROM metodos_pago WHERE LOWER(nombre_metodo_pago) = LOWER(%s) AND estado = 1",
            (value,)) is not None

    def _get_by_name(self, name):
        value = (name or '').strip()
        if not value:
            return None
        return self.fetch_one("transalca",
            "SELECT " + METODO_PAGO_ALIAS + " FROM metodos_pago mp WHERE LOWER(mp.nombre_metodo_pago) = LOWER(%s)", (value,))

    def _validate(self, data):
        errors = {}
        clean = {}
        clean['nombre'] = require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=100, allow_serial=True)
        clean['datos_pago'] = require_text(errors, 'datos_pago', data.get('datos_pago'), 'Los datos de pago', min_len=3, max_len=80, allow_serial=True)
        clean['permite_credito'] = 1 if data.get('permite_credito') in (1, '1', True, 'true', 'on') else 0
        clean['moneda'] = (data.get('moneda') or 'usd').strip().lower()
        if clean['moneda'] not in ('usd', 'bs'):
            errors['moneda'] = 'La moneda debe ser usd o bs.'
        if errors:
            raise ValidationError(errors)
        return clean

    def _create(self, data):
        clean = self._validate(data)
        self.nombre = clean['nombre']
        self.permite_credito = clean['permite_credito']
        self.moneda = clean['moneda']
        self.datos_pago = clean['datos_pago']
        existing = self._get_by_name(clean['nombre'])
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'nombre': 'Este método de pago ya está registrado.'})
            self.update("transalca",
                "UPDATE metodos_pago SET nombre_metodo_pago=%s, permite_credito=%s, moneda=%s, datos_metodo_pago=%s, estado=1 WHERE id_metodo_pago=%s",
                (self._nombre, self._permite_credito, self._moneda, self._datos_pago, existing['id']))
            return existing['id']
        return self.insert("transalca",
            "INSERT INTO metodos_pago (nombre_metodo_pago, permite_credito, moneda, datos_metodo_pago) VALUES (%s,%s,%s,%s)",
            (self._nombre, self._permite_credito, self._moneda, self._datos_pago))

    def _update_method(self, method_id, data):
        clean = self._validate(data)
        if self._name_exists(clean['nombre'], method_id):
            raise ValidationError({'nombre': 'Este método de pago ya está registrado.'})
        self.nombre = clean['nombre']
        self.permite_credito = clean['permite_credito']
        self.moneda = clean['moneda']
        self.datos_pago = clean['datos_pago']
        return self.update("transalca",
            "UPDATE metodos_pago SET nombre_metodo_pago=%s, permite_credito=%s, moneda=%s, datos_metodo_pago=%s WHERE id_metodo_pago=%s",
            (self._nombre, self._permite_credito, self._moneda, self._datos_pago, method_id))

    def _soft_delete(self, method_id):
        return self.update("transalca",
            "UPDATE metodos_pago SET estado=0 WHERE id_metodo_pago=%s", (method_id,))

    def _reactivar(self, method_id):
        return self.update("transalca", "UPDATE metodos_pago SET estado = 1 WHERE id_metodo_pago = %s", (method_id,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_active": self._get_active,
            "get_by_id": self._get_by_id,
            "name_exists": self._name_exists,
            "get_by_name": self._get_by_name,
            "create": self._create,
            "update_method": self._update_method,
            "soft_delete": self._soft_delete,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
