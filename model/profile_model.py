from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash


class ProfileModel(Connection):
    def __init__(self):
        super().__init__()


    def _get_profile(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT id, nombre, apellido, cedula, email, telefono, direccion, tipo, foto_perfil, created_at FROM usuarios WHERE id = %s",
            (user_id,))

    def _update_profile(self, user_id, data):
        updated = self.update("mantenimiento",
            "UPDATE usuarios SET nombre = %s, apellido = %s, telefono = %s, direccion = %s WHERE id = %s",
            (data['nombre'], data['apellido'], data.get('telefono', ''), data.get('direccion', ''), user_id))
        user = self._get_profile(user_id)
        if user and user.get('tipo') == 'cliente':
            nombre_cliente = (str(data['nombre']).strip() + ' ' + str(data['apellido']).strip()).strip()
            self.update("transalca",
                "UPDATE cliente SET nombre_cliente=%s, telefono_cliente=%s, direccion_cliente=%s, correo_cliente=%s "
                "WHERE identificador_cliente=%s",
                (nombre_cliente, data.get('telefono', ''), data.get('direccion', ''),
                 user.get('email', ''), user['cedula']))
        return updated

    def _update_email(self, user_id, email):
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
        return True

    def _change_password(self, user_id, old_password, new_password):
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
