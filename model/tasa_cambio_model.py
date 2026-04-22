from model.connection import Connection
from datetime import date


class TasaCambioModel(Connection):
    def __init__(self):
        super().__init__()

    def get_all(self, limit=30):
        return self.fetch_all("transalca",
            "SELECT * FROM tasas_cambio ORDER BY fecha DESC, id DESC LIMIT %s", (limit,))

    def get_by_date(self, fecha):
        return self.fetch_one("transalca",
            "SELECT * FROM tasas_cambio WHERE fecha = %s ORDER BY id DESC LIMIT 1", (fecha,))

    def get_today(self):
        return self.get_by_date(date.today().isoformat())

    def get_latest(self):
        return self.fetch_one("transalca",
            "SELECT * FROM tasas_cambio ORDER BY fecha DESC, id DESC LIMIT 1")

    def exists_today(self):
        return self.get_today() is not None

    def create(self, data):
        return self.insert("transalca",
            "INSERT INTO tasas_cambio (fecha, monto, fuente) VALUES (%s, %s, %s)",
            (data['fecha'], float(data['monto']), data['fuente'].strip()))

    def update_tasa(self, tasa_id, data):
        return self.update("transalca",
            "UPDATE tasas_cambio SET monto = %s, fuente = %s WHERE id = %s",
            (float(data['monto']), data['fuente'].strip(), tasa_id))

    def delete_tasa(self, tasa_id):
        return self.delete("transalca", "DELETE FROM tasas_cambio WHERE id = %s", (tasa_id,))

    def register_from_scraping(self, monto):
        if self.exists_today():
            return None
        return self.insert("transalca",
            "INSERT INTO tasas_cambio (fecha, monto, fuente) VALUES (%s, %s, %s)",
            (date.today().isoformat(), float(monto), 'BCV (automático)'))
