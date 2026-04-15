from model.connection import Connection


class MechanicModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca", "SELECT * FROM mecanicos ORDER BY nombre, apellido")

    def get_by_cedula(self, cedula):
        return self.fetch_one("transalca", "SELECT * FROM mecanicos WHERE cedula = %s", (cedula,))

    def get_active(self):
        return self.fetch_all("transalca",
            "SELECT * FROM mecanicos WHERE estado = 1 ORDER BY nombre, apellido")

    def create(self, data):
        sql = "INSERT INTO mecanicos (cedula, nombre, apellido, telefono, especialidad, foto_perfil) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (data['cedula'].strip(), data['nombre'].strip(), data['apellido'].strip(),
                  data.get('telefono', '').strip(), data.get('especialidad', '').strip(),
                  data.get('foto_perfil', 'default.png'))
        return self.insert("transalca", sql, params)

    def update_mechanic(self, old_cedula, data):
        sql = "UPDATE mecanicos SET cedula=%s, nombre=%s, apellido=%s, telefono=%s, especialidad=%s"
        params = [data['cedula'].strip(), data['nombre'].strip(), data['apellido'].strip(),
                  data.get('telefono', '').strip(), data.get('especialidad', '').strip()]
        if 'foto_perfil' in data:
            sql += ", foto_perfil=%s"
            params.append(data['foto_perfil'])
        sql += " WHERE cedula=%s"
        params.append(old_cedula)
        return self.update("transalca", sql, tuple(params))

    def soft_delete(self, cedula):
        return self.update("transalca",
            "UPDATE mecanicos SET estado = 0 WHERE cedula = %s", (cedula,))

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
