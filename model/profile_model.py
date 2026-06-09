from model.connection import Connection
from werkzeug.security import generate_password_hash, check_password_hash


class ProfileModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self, db, table):
        queries = {
            'clientes': "SHOW COLUMNS FROM clientes",
        }
        if table not in queries:
            raise ValueError("Tabla no permitida.")
        rows = self.fetch_all(db, queries[table])
        return {r['Field'] for r in rows}

    def get_profile(self, user_id):
        return self.fetch_one("mantenimiento",
            "SELECT id, nombre, apellido, cedula, email, telefono, direccion, tipo, foto_perfil, created_at FROM usuarios WHERE id = %s",
            (user_id,))

    def update_profile(self, user_id, data):
        updated = self.update("mantenimiento",
            "UPDATE usuarios SET nombre = %s, apellido = %s, telefono = %s, direccion = %s WHERE id = %s",
            (data['nombre'], data['apellido'], data.get('telefono', ''), data.get('direccion', ''), user_id))
        user = self.get_profile(user_id)
        if user and user.get('tipo') == 'cliente':
            columns = self._columns("transalca", "clientes")
            fields = {
                "nombre": data['nombre'],
                "apellido": data['apellido'],
                "telefono": data.get('telefono', ''),
                "direccion": data.get('direccion', ''),
                "email": user.get('email', '')
            }
            keys = [k for k in fields if k in columns]
            params = [fields[k] for k in keys]
            if keys:
                params.append(user['cedula'])
                self.update("transalca",
                    self.build_update_by_key_sql("clientes", keys, "cedula", {"clientes"}, columns),
                    tuple(params))
        return updated

    def update_email(self, user_id, email):
        user = self.get_profile(user_id)
        exclude = {"usuario_id": user_id}
        if user and user.get('tipo') == 'cliente':
            exclude["cliente_cedula"] = user.get('cedula')
        if self.email_exists_globally(email, exclude):
            return False
        self.update("mantenimiento",
            "UPDATE usuarios SET email = %s WHERE id = %s", (email, user_id))
        if user and user.get('tipo') == 'cliente':
            self.update("transalca", "UPDATE clientes SET email=%s WHERE cedula=%s", (email, user['cedula']))
        return True

    def change_password(self, user_id, old_password, new_password):
        user = self.fetch_one("mantenimiento",
            "SELECT password_hash FROM usuarios WHERE id = %s", (user_id,))
        if not user or not check_password_hash(user['password_hash'], old_password):
            return False
        password_hash = generate_password_hash(new_password)
        self.update("mantenimiento",
            "UPDATE usuarios SET password_hash = %s WHERE id = %s", (password_hash, user_id))
        return True

    def update_photo(self, user_id, filename):
        return self.update("mantenimiento",
            "UPDATE usuarios SET foto_perfil = %s WHERE id = %s", (filename, user_id))
