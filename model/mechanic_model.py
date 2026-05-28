from model.connection import Connection


class MechanicModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self):
        rows = self.fetch_all("transalca", "SHOW COLUMNS FROM mecanicos")
        return {r['Field'] for r in rows}

    def get_all(self):
        return self.fetch_all("transalca", "SELECT * FROM mecanicos WHERE estado = 1 ORDER BY nombre, apellido")

    def get_by_cedula(self, cedula):
        return self.fetch_one("transalca", "SELECT * FROM mecanicos WHERE cedula = %s", (cedula,))

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM mecanicos WHERE estado = 1 ORDER BY nombre, apellido")

    def create(self, data):
        values = {
            'cedula': data['cedula'].strip(),
            'cedula_prefijo': data.get('cedula_prefijo'),
            'nombre': data['nombre'].strip(),
            'apellido': data['apellido'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'especialidad': data.get('especialidad', '').strip(),
            'foto_perfil': data.get('foto_perfil', 'default.png')
        }
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        return self.insert("transalca",
            f"INSERT INTO mecanicos ({', '.join(keys)}) VALUES ({', '.join(['%s'] * len(keys))})",
            tuple(values[k] for k in keys))

    def update_mechanic(self, old_cedula, data):
        values = {
            'cedula': data['cedula'].strip(),
            'cedula_prefijo': data.get('cedula_prefijo'),
            'nombre': data['nombre'].strip(),
            'apellido': data['apellido'].strip(),
            'telefono': data.get('telefono', '').strip(),
            'especialidad': data.get('especialidad', '').strip()
        }
        if 'foto_perfil' in data:
            values['foto_perfil'] = data['foto_perfil']
        columns = self._columns()
        keys = [k for k in values if k in columns and values[k] is not None]
        params = [values[k] for k in keys]
        params.append(old_cedula)
        return self.update("transalca",
            f"UPDATE mecanicos SET {', '.join([f'{k}=%s' for k in keys])} WHERE cedula=%s",
            tuple(params))

    def soft_delete(self, cedula):
        return self.update("transalca", "UPDATE mecanicos SET estado = 0 WHERE cedula = %s", (cedula,))

    def toggle_estado(self, cedula):
        item = self.get_by_cedula(cedula)
        if not item:
            return None
        new_estado = 0 if int(item.get('estado') or 0) == 1 else 1
        self.update("transalca", "UPDATE mecanicos SET estado = %s WHERE cedula = %s", (new_estado, cedula))
        return new_estado

    def cedula_exists(self, cedula, exclude_cedula=None):
        if exclude_cedula:
            return self.fetch_one("transalca",
                "SELECT cedula FROM mecanicos WHERE cedula = %s AND cedula != %s", (cedula, exclude_cedula)) is not None
        return self.fetch_one("transalca",
            "SELECT cedula FROM mecanicos WHERE cedula = %s", (cedula,)) is not None

    def get_service_history(self, cedula):
        return self.fetch_all("transalca",
            "SELECT sm.*, s.nombre as servicio_nombre FROM servicio_mecanico sm INNER JOIN servicios s ON sm.servicio_id = s.id WHERE sm.mecanico_cedula = %s ORDER BY sm.fecha DESC",
            (cedula,))
