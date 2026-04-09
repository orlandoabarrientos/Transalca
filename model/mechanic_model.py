from model.connection import Connection


class MechanicModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self):
        return self.fetch_all("transalca", "SELECT * FROM mecanicos ORDER BY id DESC")

    def get_by_id(self, mechanic_id):
        return self.fetch_one("transalca", "SELECT * FROM mecanicos WHERE id = %s", (mechanic_id,))

    def create(self, data):
        sql = "INSERT INTO mecanicos (nombre, apellido, cedula, telefono, especialidad, foto_perfil) VALUES (%s, %s, %s, %s, %s, %s)"
        params = (data['nombre'], data['apellido'], data['cedula'], data.get('telefono', ''), data.get('especialidad', ''), data.get('foto_perfil', 'default.png'))
        return self.insert("transalca", sql, params)

    def update_mechanic(self, mechanic_id, data):
        sql = "UPDATE mecanicos SET nombre=%s, apellido=%s, cedula=%s, telefono=%s, especialidad=%s"
        params = [data['nombre'], data['apellido'], data['cedula'], data.get('telefono', ''), data.get('especialidad', '')]
        if 'foto_perfil' in data:
            sql += ", foto_perfil=%s"
            params.append(data['foto_perfil'])
        sql += " WHERE id=%s"
        params.append(mechanic_id)
        return self.update("transalca", sql, tuple(params))

    def soft_delete(self, mechanic_id):
        return self.update("transalca",
            "UPDATE mecanicos SET estado = 0 WHERE id = %s", (mechanic_id,))

    def get_service_history(self, mechanic_id):
        return self.fetch_all("transalca",
            "SELECT sm.*, s.nombre as servicio_nombre FROM servicio_mecanico sm INNER JOIN servicios s ON sm.servicio_id = s.id WHERE sm.mecanico_id = %s ORDER BY sm.fecha DESC",
            (mechanic_id,))

    def get_service_history(self, mechanic_id):
        return self.fetch_all("transalca",
            "SELECT sm.*, s.nombre as servicio_nombre FROM servicio_mecanico sm INNER JOIN servicios s ON sm.servicio_id = s.id WHERE sm.mecanico_id = %s ORDER BY sm.fecha DESC",
            (mechanic_id,))
