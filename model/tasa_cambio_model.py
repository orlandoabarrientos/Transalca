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
            "INSERT INTO tasas_cambio (fecha, tipo, monto, fuente) VALUES (%s, %s, %s, %s)",
            (data['fecha'], 'bcv', float(data['monto']), data['fuente'].strip()))

    def update_tasa(self, tasa_id, data):
        return self.update("transalca",
            "UPDATE tasas_cambio SET monto = %s, fuente = %s WHERE id = %s AND tipo='bcv'",
            (float(data['monto']), data['fuente'].strip(), tasa_id))

    def delete_tasa(self, tasa_id):
        return self.delete("transalca", "DELETE FROM tasas_cambio WHERE id = %s AND tipo='bcv'", (tasa_id,))

    def register_from_scraping(self, monto):
        if self.exists_today():
            return None
        return self.create({
            'fecha': date.today().isoformat(),
            'monto': float(monto),
            'fuente': 'BCV automatico'
        })

    def upsert_from_scraping(self, monto, fecha=None, fuente='BCV automatico'):
        target_date = fecha or date.today().isoformat()
        lock_name = f"bcv_sync_{target_date}"
        lock = self.fetch_one(
            "transalca",
            "SELECT GET_LOCK(%s, 5) AS acquired",
            (lock_name,)
        )
        if not lock or int(lock.get('acquired') or 0) != 1:
            return {'action': 'lock_busy', 'id': None, 'fecha': target_date}
        try:
            existing = self.get_by_date(target_date)
            payload = {
                'monto': float(monto),
                'fuente': fuente.strip()
            }
            if existing:
                self.update_tasa(existing['id'], payload)
                return {'action': 'updated', 'id': existing['id'], 'fecha': target_date}
            created_id = self.create({
                'fecha': target_date,
                'monto': payload['monto'],
                'fuente': payload['fuente']
            })
            return {'action': 'created', 'id': created_id, 'fecha': target_date}
        finally:
            self.fetch_one(
                "transalca",
                "SELECT RELEASE_LOCK(%s) AS released",
                (lock_name,)
            )
