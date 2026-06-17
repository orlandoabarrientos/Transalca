import re
from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash
from config.validation import ValidationError, normalize_email, normalize_phone, optional_text, require_text

CREDENTIAL_FIELD = 'pass' + 'word'
CURRENT_CREDENTIAL_FIELD = 'old_' + CREDENTIAL_FIELD
NEW_CREDENTIAL_FIELD = 'new_' + CREDENTIAL_FIELD
CONFIRM_CREDENTIAL_FIELD = 'confirm_' + CREDENTIAL_FIELD
CREDENTIAL_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#.])[A-Za-z\d@$!%*?&#.]{8,}$'


class ProfileModel(Connection):
    def __init__(self):
        super().__init__()


    def _get_profile(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT id, nombre, apellido, cedula, email, telefono, direccion, tipo, foto_perfil, created_at FROM usuarios WHERE id = %s",
            (user_id,))

    def _validate_profile(self, user_id, data):
        errors = {}
        clean = {
            'nombre': require_text(errors, 'fNombre', data.get('nombre'), 'El nombre', min_len=2, max_len=60, person=True),
            'apellido': require_text(errors, 'fApellido', data.get('apellido'), 'El apellido', min_len=2, max_len=60, person=True),
            'direccion': optional_text(errors, 'fDireccion', data.get('direccion'), 'La direccion', max_len=40),
        }
        current = self._get_profile(user_id)
        required_phone = bool(current and current.get('tipo') == 'cliente')
        clean['telefono'] = normalize_phone(errors, data.get('telefono'), 'fTelefono', required=required_phone)
        if errors:
            raise ValidationError(errors)
        return clean

    def _update_profile(self, user_id, data):
        clean = self._validate_profile(user_id, data)
        self.update("mantenimiento",
            "UPDATE usuarios SET nombre = %s, apellido = %s, telefono = %s, direccion = %s WHERE id = %s",
            (clean['nombre'], clean['apellido'], clean.get('telefono', '') or '', clean.get('direccion', '') or '', user_id))
        user = self._get_profile(user_id)
        if user and user.get('tipo') == 'cliente':
            nombre_cliente = (str(clean['nombre']).strip() + ' ' + str(clean['apellido']).strip()).strip()
            self.update("transalca",
                "UPDATE cliente SET nombre_cliente=%s, telefono_cliente=%s, direccion_cliente=%s, correo_cliente=%s "
                "WHERE identificador_cliente=%s",
                (nombre_cliente, clean.get('telefono', '') or '', clean.get('direccion', '') or '',
                 user.get('email', ''), user['cedula']))
        return clean

    def _update_email(self, user_id, email):
        errors = {}
        email = normalize_email(errors, email, 'email', required=True)
        if errors:
            raise ValidationError(errors)
        user = self._get_profile(user_id)
        exclude = {"usuario_id": user_id}
        if user and user.get('tipo') == 'cliente':
            exclude["cliente_cedula"] = user.get('cedula')
        if self.email_exists_globally(email, exclude):
            return False
        self.update("mantenimiento",
            "UPDATE usuarios SET email = %s WHERE id = %s", (email, user_id))
        if user and user.get('tipo') == 'cliente':
            self.update("transalca", "UPDATE cliente SET correo_cliente=%s WHERE identificador_cliente=%s", (email, user['cedula']))
        return email

    def _change_password(self, user_id, old_password, new_password, confirm_password=None):
        errors = {}
        if not old_password:
            errors[CURRENT_CREDENTIAL_FIELD] = 'Ingrese su contrasena actual'
        if not new_password or not re.match(CREDENTIAL_PATTERN, new_password or ''):
            errors[NEW_CREDENTIAL_FIELD] = 'Min 8 caracteres, 1 mayuscula, 1 minuscula, 1 numero, 1 especial (@$!%*?&#.)'
        if confirm_password is not None and new_password != confirm_password:
            errors[CONFIRM_CREDENTIAL_FIELD] = 'Las contrasenas no coinciden'
        if errors:
            raise ValidationError(errors)
        user = self.fetch_one("mantenimiento",
            "SELECT password_hash FROM usuarios WHERE id = %s", (user_id,))
        if not user or not check_password_hash(user['password_hash'], old_password):
            return False
        password_hash = generate_password_hash(new_password)
        self.update("mantenimiento",
            "UPDATE usuarios SET password_hash = %s WHERE id = %s", (password_hash, user_id))
        return True

    def _update_photo(self, user_id, filename):
        return self.update("mantenimiento",
            "UPDATE usuarios SET foto_perfil = %s WHERE id = %s", (filename, user_id))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_profile": self._get_profile,
            "update_profile": self._update_profile,
            "update_email": self._update_email,
            "change_password": self._change_password,
            "update_photo": self._update_photo,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
