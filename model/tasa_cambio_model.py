import re

from model.connection import Connection
from config.validation import ValidationError
from datetime import date


class TasaCambioModel(Connection):
    def __init__(self):
        super().__init__()
        self._fecha = None
        self._monto = None
        self._fuente = None

    @property
    def fecha(self):
        return self._fecha

    @fecha.setter
    def fecha(self, valor):
        if valor:
            valor = str(valor).strip()
        self._fecha = valor

    @property
    def monto(self):
        return self._monto

    @monto.setter
    def monto(self, valor):
        self._monto = float(valor)

    @property
    def fuente(self):
        return self._fuente

    @fuente.setter
    def fuente(self, valor):
        if valor:
            valor = str(valor).strip()
        self._fuente = valor

    def _get_all(self, limit=30):
        return self.fetch_all("transalca",
            "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t ORDER BY t.fecha_tasa_cambio DESC, t.id_tasa_cambio DESC LIMIT %s", (limit,))

    def _get_by_date(self, fecha):
        return self.fetch_one("transalca",
            "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t WHERE t.fecha_tasa_cambio = %s ORDER BY t.id_tasa_cambio DESC LIMIT 1", (fecha,))

    def _get_today(self):
        return self._get_by_date(date.today().isoformat())

    def _get_latest(self):
        return self.fetch_one("transalca",
            "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t ORDER BY t.fecha_tasa_cambio DESC, t.id_tasa_cambio DESC LIMIT 1")

    def _exists_today(self):
        return self._get_today() is not None

    def _validate(self, data, require_fecha=True):
        errors = {}
        clean = {}
        fecha = (str(data.get('fecha')).strip() if data.get('fecha') is not None else '')
        if require_fecha or 'fecha' in data:
            if not fecha:
                errors['fecha'] = 'Fecha requerida'
            elif not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fecha):
                errors['fecha'] = 'Fecha invalida'
        clean['fecha'] = fecha
        try:
            monto = float(data.get('monto', 0))
            if monto <= 0:
                errors['monto'] = 'El monto debe ser mayor a 0'
            clean['monto'] = monto
        except (ValueError, TypeError):
            errors['monto'] = 'Monto invalido'
        fuente = (str(data.get('fuente') or '').strip())
        if len(fuente) < 2:
            errors['fuente'] = 'Fuente requerida'
        clean['fuente'] = fuente
        if errors:
            raise ValidationError(errors)
        return clean

    def _create(self, data):
        clean = self._validate(data, require_fecha=True)
        self.fecha = clean['fecha']
        self.monto = clean['monto']
        self.fuente = clean['fuente']
        return self.insert("transalca",
            "INSERT INTO tasas_cambio (fecha_tasa_cambio, tipo_tasa_cambio, monto, fuente) VALUES (%s, %s, %s, %s)",
            (self._fecha, 'bcv', self._monto, self._fuente))

    def _update_tasa(self, tasa_id, data):
        clean = self._validate(data, require_fecha=False)
        self.monto = clean['monto']
        self.fuente = clean['fuente']
        if 'fecha' in data and data.get('fecha'):
            self.fecha = clean['fecha']
            return self.update("transalca",
                "UPDATE tasas_cambio SET monto = %s, fuente = %s, fecha_tasa_cambio = %s WHERE id_tasa_cambio = %s AND tipo_tasa_cambio='bcv'",
                (self._monto, self._fuente, self._fecha, tasa_id))
        return self.update("transalca",
            "UPDATE tasas_cambio SET monto = %s, fuente = %s WHERE id_tasa_cambio = %s AND tipo_tasa_cambio='bcv'",
            (self._monto, self._fuente, tasa_id))

    def _delete_tasa(self, tasa_id):
        return self.delete("transalca", "DELETE FROM tasas_cambio WHERE id_tasa_cambio = %s AND tipo_tasa_cambio='bcv'", (tasa_id,))

    def _register_from_scraping(self, monto):
        if self._exists_today():
            return None
        return self._create({
            'fecha': date.today().isoformat(),
            'monto': float(monto),
            'fuente': 'BCV automatico'
        })

    def _upsert_from_scraping(self, monto, fecha=None, fuente='BCV automatico'):
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
            existing = self._get_by_date(target_date)
            payload = {
                'monto': float(monto),
                'fuente': fuente.strip()
            }
            if existing:
                self._update_tasa(existing['id'], payload)
                return {'action': 'updated', 'id': existing['id'], 'fecha': target_date}
            created_id = self._create({
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

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_date": self._get_by_date,
            "get_today": self._get_today,
            "get_latest": self._get_latest,
            "exists_today": self._exists_today,
            "create": self._create,
            "update_tasa": self._update_tasa,
            "delete_tasa": self._delete_tasa,
            "register_from_scraping": self._register_from_scraping,
            "upsert_from_scraping": self._upsert_from_scraping,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
