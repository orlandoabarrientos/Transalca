import re

from model.connection import Connection
from config.validation import ValidationError, normalize_email, normalize_phone, optional_text, require_text

SUCURSAL_ALIAS = (
    "s.*, s.id_sucursal AS id, s.nombre_sucursal AS nombre, s.direccion_sucursal AS direccion, "
    "s.telefono_sucursal AS telefono, s.email_sucursal AS email"
)

DIRECCION_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s.,\-]+$")


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

    def _validate(self, data):
        errors = {}
        direccion_raw = data.get('direccion')
        if direccion_raw is not None and str(direccion_raw) != '' and not str(direccion_raw).strip():
            errors['direccion'] = 'La direccion no puede contener solo espacios en blanco.'
        clean = {
            'nombre': require_text(errors, 'nombre', data.get('nombre'), 'El nombre', min_len=3, max_len=200, allow_serial=False),
            'direccion': optional_text(errors, 'direccion', data.get('direccion'), 'La direccion', max_len=40),
            'telefono': normalize_phone(errors, data.get('telefono'), required=False),
            'email': normalize_email(errors, data.get('email'), required=False),
        }
        if clean['direccion'] and 'direccion' not in errors and not DIRECCION_RE.match(clean['direccion']):
            errors['direccion'] = 'La direccion solo puede contener letras, numeros, espacios, puntos, comas y guiones.'
        if errors:
            raise ValidationError(errors)
        return clean

    def _create(self, data):
        clean = self._validate(data)
        self.nombre = clean['nombre']
        self.direccion = clean.get('direccion', '') or ''
        self.telefono = clean.get('telefono', '') or ''
        self.email = clean.get('email', '') or ''
        existing = self._get_by_nombre(self._nombre)
        if existing:
            if existing['estado'] == 1:
                raise ValidationError({'nombre': 'Ya existe una sucursal con ese nombre.'})
            if clean.get('email') and self.email_exists_globally(clean['email'], {"sucursal_id": existing['id']}):
                raise ValidationError({'email': 'Este correo ya esta registrado.'})
            self.update("transalca",
                "UPDATE sucursales SET direccion_sucursal=%s, telefono_sucursal=%s, email_sucursal=%s, estado=1 WHERE id_sucursal=%s",
                (self._direccion, self._telefono, self._email, existing['id']))
            return existing['id']
        if clean.get('email') and self.email_exists_globally(clean['email']):
            raise ValidationError({'email': 'Este correo ya esta registrado.'})
        return self.insert("transalca",
            "INSERT INTO sucursales (nombre_sucursal, direccion_sucursal, telefono_sucursal, email_sucursal) VALUES (%s, %s, %s, %s)",
            (self._nombre, self._direccion, self._telefono, self._email))

    def _update_sucursal(self, sucursal_id, data):
        clean = self._validate(data)
        if self._nombre_exists(clean['nombre'], sucursal_id):
            raise ValidationError({'nombre': 'Ya existe una sucursal con ese nombre.'})
        if clean.get('email') and self.email_exists_globally(clean['email'], {"sucursal_id": sucursal_id}):
            raise ValidationError({'email': 'Este correo ya esta registrado.'})
        self.nombre = clean['nombre']
        self.direccion = clean.get('direccion', '') or ''
        self.telefono = clean.get('telefono', '') or ''
        self.email = clean.get('email', '') or ''
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
        return self.update("transalca", "UPDATE sucursales SET estado = 1 WHERE id_sucursal = %s", (sucursal_id,))

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
