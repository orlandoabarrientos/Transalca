from model.connection import Connection
from datetime import datetime, timedelta
import math


class PricingModel(Connection):
    def __init__(self):
        super().__init__()

    def _columns(self, table):
        rows = self.fetch_all("transalca", f"SHOW COLUMNS FROM {table}")
        return {r['Field'] for r in rows}

    def get_rates(self, limit=30):
        return self.fetch_all("transalca",
            "SELECT * FROM tasas_cambio ORDER BY fecha DESC, id DESC LIMIT %s", (limit,))

    def get_rate_by_type(self, tipo, fecha=None):
        if not fecha:
            fecha = datetime.now().date().isoformat()
        return self.fetch_one("transalca",
            "SELECT * FROM tasas_cambio WHERE tipo=%s AND fecha=%s "
            "ORDER BY id DESC LIMIT 1", (tipo, fecha))

    def get_latest_rate(self, tipo='bcv'):
        return self.fetch_one("transalca",
            "SELECT * FROM tasas_cambio WHERE tipo=%s "
            "ORDER BY fecha DESC, id DESC LIMIT 1", (tipo,))

    def save_rate(self, tipo, monto, fuente):
        fecha = datetime.now().date().isoformat()
        existing = self.get_rate_by_type(tipo, fecha)
        if existing:
            return self.update("transalca",
                "UPDATE tasas_cambio SET monto=%s, fuente=%s WHERE id=%s",
                (float(monto), fuente, existing['id']))
        return self.insert("transalca",
            "INSERT INTO tasas_cambio (fecha, tipo, monto, fuente) VALUES (%s,%s,%s,%s)",
            (fecha, tipo, float(monto), fuente))

    def get_setting(self, clave):
        row = self.fetch_one("transalca",
            "SELECT valor FROM configuracion WHERE clave=%s", (clave,))
        return row['valor'] if row else None

    def get_all_settings(self):
        keys = (
            'margen_seguridad_pct', 'hora_congelamiento', 'banda_variacion_pct',
            'tasa_referencia_activa', 'redondeo_bs', 'vencimiento_cotizacion_hrs',
            'auto_update_enabled', 'update_schedule'
        )
        rows = self.fetch_all("transalca",
            "SELECT clave, valor FROM configuracion ORDER BY clave")
        return {r['clave']: r['valor'] for r in rows if r['clave'] in keys}

    def update_setting(self, clave, valor):
        existing = self.fetch_one("transalca",
            "SELECT clave FROM configuracion WHERE clave=%s", (clave,))
        if existing:
            return self.update("transalca",
                "UPDATE configuracion SET valor=%s WHERE clave=%s", (valor, clave))
        return self.insert("transalca",
            "INSERT INTO configuracion (clave, valor) VALUES (%s,%s)", (clave, valor))

    def get_active_rate(self):
        settings = self.get_all_settings()
        tipo = settings.get('tasa_referencia_activa', 'bcv')
        hora_congelamiento = settings.get('hora_congelamiento', '16:00')
        now = datetime.now()

        try:
            h, m = hora_congelamiento.split(':')
            freeze_time = now.replace(hour=int(h), minute=int(m), second=0)
            if now > freeze_time:
                rate = self.get_rate_by_type(tipo, now.date().isoformat())
                if rate:
                    return {'id': rate.get('id'), 'monto': float(rate['monto']), 'tipo': tipo,
                            'frozen': True, 'fecha': rate['fecha']}
        except (ValueError, TypeError):
            pass

        rate = self.get_latest_rate(tipo)
        if not rate:
            rate = self.fetch_one("transalca",
                "SELECT * FROM tasas_cambio ORDER BY fecha DESC, id DESC LIMIT 1")
        if not rate:
            return None

        return {'id': rate.get('id'), 'monto': float(rate['monto']), 'tipo': tipo,
                'frozen': False, 'fecha': rate['fecha']}

    def calculate_price_bs(self, precio_usd):
        rate_info = self.get_active_rate()
        if not rate_info:
            return None

        settings = self.get_all_settings()
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

    def should_update_rate(self, new_rate, tipo='bcv'):
        settings = self.get_all_settings()
        banda = float(settings.get('banda_variacion_pct', 2.0))
        current = self.get_latest_rate(tipo)
        if not current:
            return True
        current_monto = float(current['monto'])
        if current_monto == 0:
            return True
        variation = abs(new_rate - current_monto) / current_monto * 100
        return variation >= banda

    def create_quote(self, cliente_cedula, items):
        rate_info = self.get_active_rate()
        if not rate_info:
            return None

        settings = self.get_all_settings()
        vencimiento_hrs = int(settings.get('vencimiento_cotizacion_hrs', 24))
        margen = float(settings.get('margen_seguridad_pct', 3.0))
        redondeo = float(settings.get('redondeo_bs', 0.50))
        tasa = rate_info['monto'] * (1 + margen / 100)
        vigente_hasta = datetime.now() + timedelta(hours=vencimiento_hrs)

        total_usd = sum(float(i['precio_usd']) * int(i.get('cantidad', 1)) for i in items)
        total_bs_raw = total_usd * tasa
        if redondeo > 0:
            total_bs = math.ceil(total_bs_raw / redondeo) * redondeo
        else:
            total_bs = round(total_bs_raw, 2)

        quote_columns = self._columns("cotizaciones")
        if "tasa_cambio_id" in quote_columns:
            quote_id = self.insert("transalca",
                "INSERT INTO cotizaciones (cliente_cedula, tasa_cambio_id, tasa_usada, tipo_tasa, "
                "total_usd, total_bs, vigente_hasta) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (cliente_cedula, rate_info.get('id'), round(tasa, 4), rate_info['tipo'],
                 total_usd, total_bs, vigente_hasta))
        else:
            quote_id = self.insert("transalca",
                "INSERT INTO cotizaciones (cliente_cedula, tasa_usada, tipo_tasa, "
                "total_usd, total_bs, vigente_hasta) VALUES (%s,%s,%s,%s,%s,%s)",
                (cliente_cedula, round(tasa, 4), rate_info['tipo'],
                 total_usd, total_bs, vigente_hasta))

        for item in items:
            p_usd = float(item['precio_usd'])
            p_bs_raw = p_usd * tasa
            p_bs = math.ceil(p_bs_raw / redondeo) * redondeo if redondeo > 0 else round(p_bs_raw, 2)
            self.insert("transalca",
                "INSERT INTO cotizacion_items (cotizacion_id, producto_codigo, servicio_id, "
                "tipo, cantidad, precio_usd, precio_bs) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (quote_id, item.get('producto_codigo') or 'SIN_PRODUCTO', item.get('servicio_id') or 0,
                 item.get('tipo', 'producto'), int(item.get('cantidad', 1)), p_usd, p_bs))
        return quote_id

    def get_quote(self, qid):
        q = self.fetch_one("transalca", "SELECT * FROM cotizaciones WHERE id=%s", (qid,))
        if q:
            q['items'] = self.fetch_all("transalca",
                "SELECT * FROM cotizacion_items WHERE cotizacion_id=%s", (qid,))
            if q['estado'] == 'vigente' and datetime.now() > q['vigente_hasta']:
                self.update("transalca",
                    "UPDATE cotizaciones SET estado='vencida' WHERE id=%s", (qid,))
                q['estado'] = 'vencida'
        return q

    def get_client_quotes(self, cliente_cedula):
        return self.fetch_all("transalca",
            "SELECT * FROM cotizaciones WHERE cliente_cedula=%s "
            "ORDER BY created_at DESC", (cliente_cedula,))
