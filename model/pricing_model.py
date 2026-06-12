from model.connection import Connection
from datetime import datetime, timedelta
import math


class PricingModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self, table):
        rows = self.fetch_all("transalca", f"SHOW COLUMNS FROM {table}")
        return {r['Field'] for r in rows}

    def _get_rates(self, limit=30):
        return self.fetch_all("transalca",
            "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t ORDER BY t.fecha_tasa_cambio DESC, t.id_tasa_cambio DESC LIMIT %s", (limit,))

    def _get_rate_by_type(self, tipo, fecha=None):
        if not fecha:
            fecha = datetime.now().date().isoformat()
        return self.fetch_one("transalca",
            "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t WHERE t.tipo_tasa_cambio=%s AND t.fecha_tasa_cambio=%s "
            "ORDER BY t.id_tasa_cambio DESC LIMIT 1", (tipo, fecha))

    def _get_latest_rate(self, tipo='bcv'):
        return self.fetch_one("transalca",
            "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t WHERE t.tipo_tasa_cambio=%s "
            "ORDER BY t.fecha_tasa_cambio DESC, t.id_tasa_cambio DESC LIMIT 1", (tipo,))

    def _save_rate(self, tipo, monto, fuente):
        fecha = datetime.now().date().isoformat()
        existing = self._get_rate_by_type(tipo, fecha)
        if existing:
            return self.update("transalca",
                "UPDATE tasas_cambio SET monto=%s, fuente=%s WHERE id_tasa_cambio=%s",
                (float(monto), fuente, existing['id']))
        return self.insert("transalca",
            "INSERT INTO tasas_cambio (fecha_tasa_cambio, tipo_tasa_cambio, monto, fuente) VALUES (%s,%s,%s,%s)",
            (fecha, tipo, float(monto), fuente))

    def _get_setting(self, clave):
        row = self.fetch_one("transalca",
            "SELECT valor FROM configuracion WHERE clave=%s", (clave,))
        return row['valor'] if row else None

    def _get_all_settings(self):
        keys = (
            'margen_seguridad_pct', 'hora_congelamiento', 'banda_variacion_pct',
            'tasa_referencia_activa', 'redondeo_bs',
            'auto_update_enabled', 'update_schedule'
        )
        rows = self.fetch_all("transalca",
            "SELECT clave, valor FROM configuracion ORDER BY clave")
        return {r['clave']: r['valor'] for r in rows if r['clave'] in keys}

    def _update_setting(self, clave, valor):
        existing = self.fetch_one("transalca",
            "SELECT clave FROM configuracion WHERE clave=%s", (clave,))
        if existing:
            return self.update("transalca",
                "UPDATE configuracion SET valor=%s WHERE clave=%s", (valor, clave))
        return self.insert("transalca",
            "INSERT INTO configuracion (clave, valor) VALUES (%s,%s)", (clave, valor))

    def _get_active_rate(self):
        settings = self._get_all_settings()
        tipo = settings.get('tasa_referencia_activa', 'bcv')
        hora_congelamiento = settings.get('hora_congelamiento', '16:00')
        now = datetime.now()

        try:
            h, m = hora_congelamiento.split(':')
            freeze_time = now.replace(hour=int(h), minute=int(m), second=0)
            if now > freeze_time:
                rate = self._get_rate_by_type(tipo, now.date().isoformat())
                if rate:
                    return {'id': rate.get('id'), 'monto': float(rate['monto']), 'tipo': tipo,
                            'frozen': True, 'fecha': rate['fecha']}
        except (ValueError, TypeError):
            pass

        rate = self._get_latest_rate(tipo)
        if not rate:
            rate = self.fetch_one("transalca",
                "SELECT t.*, t.id_tasa_cambio AS id, t.fecha_tasa_cambio AS fecha, t.tipo_tasa_cambio AS tipo FROM tasas_cambio t ORDER BY t.fecha_tasa_cambio DESC, t.id_tasa_cambio DESC LIMIT 1")
        if not rate:
            return None

        return {'id': rate.get('id'), 'monto': float(rate['monto']), 'tipo': tipo,
                'frozen': False, 'fecha': rate['fecha']}

    def _calculate_price_bs(self, precio_usd):
        rate_info = self._get_active_rate()
        if not rate_info:
            return None

        settings = self._get_all_settings()
        margen = float(settings.get('margen_seguridad_pct', 3.0))
        redondeo = float(settings.get('redondeo_bs', 0.50))

        tasa = rate_info['monto']
        tasa_con_margen = tasa * (1 + margen / 100)
        precio_bs_raw = float(precio_usd) * tasa_con_margen

        if redondeo > 0:
            precio_bs = math.ceil(precio_bs_raw / redondeo) * redondeo
        else:
            precio_bs = round(precio_bs_raw, 2)

        return {
            'precio_usd': float(precio_usd),
            'precio_bs': precio_bs,
            'tasa_base': tasa,
            'tasa_con_margen': round(tasa_con_margen, 4),
            'margen_pct': margen,
            'tipo_tasa': rate_info['tipo'],
            'tasa_cambio_id': rate_info.get('id'),
            'frozen': rate_info['frozen']
        }

    def _should_update_rate(self, new_rate, tipo='bcv'):
        settings = self._get_all_settings()
        banda = float(settings.get('banda_variacion_pct', 2.0))
        current = self._get_latest_rate(tipo)
        if not current:
            return True
        current_monto = float(current['monto'])
        if current_monto == 0:
            return True
        variation = abs(new_rate - current_monto) / current_monto * 100
        return variation >= banda

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_rates": self._get_rates,
            "get_rate_by_type": self._get_rate_by_type,
            "get_latest_rate": self._get_latest_rate,
            "save_rate": self._save_rate,
            "get_setting": self._get_setting,
            "get_all_settings": self._get_all_settings,
            "update_setting": self._update_setting,
            "get_active_rate": self._get_active_rate,
            "calculate_price_bs": self._calculate_price_bs,
            "should_update_rate": self._should_update_rate,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
