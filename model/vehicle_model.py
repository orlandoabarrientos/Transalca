from model.connection import Connection
from config.constants import TIPOS_COMBUSTIBLE, validate_choice
import json


class VehicleModel(Connection):
    def __init__(self):
        super().__init__()

    def _plate(self, value):
        return (str(value or '').strip().upper())

    def get_all(self):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa as id, "
            "COALESCE(GROUP_CONCAT(DISTINCT CONCAT(c.nombre, ' ', c.apellido) SEPARATOR ', '), '-') as cliente_nombre, "
            "'' as cliente_apellido "
            "FROM vehiculos v "
            "LEFT JOIN cliente_vehiculo cv ON v.placa = cv.vehiculo_placa AND cv.estado = 1 "
            "LEFT JOIN clientes c ON cv.cliente_cedula = c.cedula "
            "WHERE v.estado = 1 "
            "GROUP BY v.placa "
            "ORDER BY v.created_at DESC")

    def get_by_id(self, vid):
        placa = self._plate(vid)
        return self.fetch_one("transalca",
            "SELECT v.*, v.placa as id, "
            "COALESCE(GROUP_CONCAT(DISTINCT CONCAT(c.nombre, ' ', c.apellido) SEPARATOR ', '), '-') as cliente_nombre, "
            "'' as cliente_apellido, "
            "COALESCE(GROUP_CONCAT(DISTINCT c.telefono SEPARATOR ', '), '') as cliente_telefono, "
            "COALESCE(GROUP_CONCAT(DISTINCT c.email SEPARATOR ', '), '') as cliente_email, "
            "COALESCE(GROUP_CONCAT(DISTINCT c.cedula SEPARATOR ','), '') as cliente_cedula "
            "FROM vehiculos v "
            "LEFT JOIN cliente_vehiculo cv ON v.placa = cv.vehiculo_placa AND cv.estado = 1 "
            "LEFT JOIN clientes c ON cv.cliente_cedula = c.cedula "
            "WHERE v.placa = %s "
            "GROUP BY v.placa", (placa,))

    def get_by_cliente(self, cliente_cedula):
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa as id "
            "FROM vehiculos v "
            "INNER JOIN cliente_vehiculo cv ON v.placa = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula = %s AND cv.estado = 1 AND v.estado = 1 "
            "ORDER BY cv.created_at DESC", (cliente_cedula,))

    def get_by_placa(self, placa):
        return self.fetch_one("transalca",
            "SELECT v.*, v.placa as id FROM vehiculos v WHERE placa = %s", (self._plate(placa),))

    def create(self, data):
        validate_choice(data.get('tipo_combustible', 'gasolina'), TIPOS_COMBUSTIBLE, 'tipo_combustible')
        placa = self._plate(data.get('placa'))
        cliente_cedula = data.get('cliente_cedula', '').strip()
        
        conn = self.con_transalca()
        conn.begin()
        try:
            existing_vehicle = self.fetch_one("transalca", "SELECT placa, estado FROM vehiculos WHERE placa = %s", (placa,))
            if not existing_vehicle:
                self.insert("transalca",
                    "INSERT INTO vehiculos (marca, modelo, anio, placa, color, "
                    "tipo_vehiculo, tipo_combustible, kilometraje_actual, aceite_usado, "
                    "filtros_info, refrigerante_info, observaciones, titulo_vehiculo, estado) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)",
                    (data['marca'].strip(), data['modelo'].strip(),
                     data.get('anio') or None, placa,
                     (data.get('color') or '').strip(),
                     (data.get('tipo_vehiculo') or '').strip(),
                     data.get('tipo_combustible', 'gasolina'),
                     int(data.get('kilometraje_actual', 0)),
                     (data.get('aceite_usado') or '').strip(),
                     (data.get('filtros_info') or '').strip(),
                     (data.get('refrigerante_info') or '').strip(),
                     (data.get('observaciones') or '').strip(),
                     data.get('titulo_vehiculo') or None))
            elif existing_vehicle['estado'] == 0:
                self.update("transalca", "UPDATE vehiculos SET estado = 1 WHERE placa = %s", (placa,))
                
            if cliente_cedula:
                existing_rel = self.fetch_one("transalca", 
                    "SELECT id, estado FROM cliente_vehiculo WHERE cliente_cedula = %s AND vehiculo_placa = %s", 
                    (cliente_cedula, placa))
                if not existing_rel:
                    self.insert("transalca", 
                        "INSERT INTO cliente_vehiculo (cliente_cedula, vehiculo_placa, estado) VALUES (%s, %s, 1)", 
                        (cliente_cedula, placa))
                elif existing_rel['estado'] == 0:
                    self.update("transalca", "UPDATE cliente_vehiculo SET estado = 1 WHERE id = %s", (existing_rel['id'],))
                    
                # If representative_cedula is provided (for company fleet vehicles), record the operation
                representante_cedula = data.get('representante_cedula', '').strip()
                if representante_cedula:
                    self.insert("transalca",
                        "INSERT INTO empresa_vehiculo_representante (empresa_rif, vehiculo_placa, representante_cedula, tipo_operacion) "
                        "VALUES (%s, %s, %s, 'registro')",
                        (cliente_cedula, placa, representante_cedula))
            conn.commit()
            return placa
        except Exception:
            conn.rollback()
            raise

    def update_vehicle(self, vid, data):
        validate_choice(data.get('tipo_combustible', 'gasolina'), TIPOS_COMBUSTIBLE, 'tipo_combustible')
        old_placa = self._plate(vid)
        return self.update("transalca",
            "UPDATE vehiculos SET marca=%s, modelo=%s, anio=%s, placa=%s, color=%s, "
            "tipo_vehiculo=%s, tipo_combustible=%s, kilometraje_actual=%s, "
            "aceite_usado=%s, filtros_info=%s, refrigerante_info=%s, observaciones=%s "
            "WHERE placa=%s",
            (data['marca'].strip(), data['modelo'].strip(),
             data.get('anio') or None,
             self._plate(data.get('placa')),
             (data.get('color') or '').strip(),
             (data.get('tipo_vehiculo') or '').strip(),
             data.get('tipo_combustible', 'gasolina'),
             int(data.get('kilometraje_actual', 0)),
             (data.get('aceite_usado') or '').strip(),
             (data.get('filtros_info') or '').strip(),
             (data.get('refrigerante_info') or '').strip(),
             (data.get('observaciones') or '').strip(), old_placa))

    def update_kilometraje(self, vid, km):
        km = int(km)
        placa = self._plate(vid)
        vehicle = self.fetch_one("transalca",
            "SELECT placa, kilometraje_actual FROM vehiculos WHERE placa = %s", (placa,))
        if not vehicle:
            return False
        if vehicle and km < vehicle['kilometraje_actual']:
            return False
        self.update("transalca",
            "UPDATE vehiculos SET kilometraje_actual = %s WHERE placa = %s", (km, placa))
        self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_placa, tipo_registro, descripcion, kilometraje, fecha) "
            "VALUES (%s, 'observacion', %s, %s, CURDATE())",
            (vehicle['placa'], f'Kilometraje actualizado a {km} km', km))
        return True

    def update_carnet_image(self, vid, filename):
        return self.update("transalca",
            "UPDATE vehiculos SET titulo_vehiculo = %s WHERE placa = %s", (filename, self._plate(vid)))

    def soft_delete(self, vid):
        return self.update("transalca",
            "UPDATE vehiculos SET estado = 0 WHERE placa = %s", (self._plate(vid),))

    def soft_delete_relationship(self, cliente_cedula, placa):
        return self.update("transalca",
            "UPDATE cliente_vehiculo SET estado = 0 WHERE cliente_cedula = %s AND vehiculo_placa = %s",
            (cliente_cedula, self._plate(placa)))

    def get_clients_by_vehicle(self, placa):
        rows = self.fetch_all("transalca", "SELECT cliente_cedula FROM cliente_vehiculo WHERE vehiculo_placa = %s AND estado = 1", (self._plate(placa),))
        return [r['cliente_cedula'] for r in rows]

    def placa_exists(self, placa, exclude_id=None):
        if not placa:
            return False
        placa = self._plate(placa)
        if exclude_id:
            return self.fetch_one("transalca",
                "SELECT placa FROM vehiculos WHERE placa = %s AND placa != %s AND estado = 1",
                (placa, self._plate(exclude_id))) is not None
        return self.fetch_one("transalca",
            "SELECT placa FROM vehiculos WHERE placa = %s AND estado = 1", (placa,)) is not None

    def get_km_history(self, vid):
        return self.fetch_all("transalca",
            "SELECT * FROM bitacora_vehiculo WHERE vehiculo_placa = %s "
            "AND kilometraje IS NOT NULL ORDER BY fecha DESC, id DESC LIMIT 50", (self._plate(vid),))

    def search(self, query):
        q = f"%{query}%"
        return self.fetch_all("transalca",
            "SELECT v.*, v.placa as id, "
            "COALESCE(GROUP_CONCAT(DISTINCT CONCAT(c.nombre, ' ', c.apellido) SEPARATOR ', '), '-') as cliente_nombre, "
            "'' as cliente_apellido "
            "FROM vehiculos v "
            "LEFT JOIN cliente_vehiculo cv ON v.placa = cv.vehiculo_placa AND cv.estado = 1 "
            "LEFT JOIN clientes c ON cv.cliente_cedula = c.cedula "
            "WHERE v.estado = 1 AND (v.placa LIKE %s OR v.marca LIKE %s OR v.modelo LIKE %s "
            "OR c.nombre LIKE %s OR c.apellido LIKE %s) "
            "GROUP BY v.placa "
            "ORDER BY v.created_at DESC", (q, q, q, q, q))

    def get_cauchos(self, vid):
        v = self.fetch_one("transalca",
            "SELECT cauchos_json FROM vehiculos WHERE placa = %s", (self._plate(vid),))
        if v and v.get('cauchos_json'):
            try:
                return json.loads(v['cauchos_json']) if isinstance(v['cauchos_json'], str) else v['cauchos_json']
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def save_cauchos(self, vid, cauchos_data):
        return self.update("transalca",
            "UPDATE vehiculos SET cauchos_json = %s WHERE placa = %s",
            (json.dumps(cauchos_data, ensure_ascii=False), self._plate(vid)))

    def add_caucho(self, vid, data):
        items = self.get_cauchos(vid)
        next_id = max([int(i.get('id', 0)) for i in items] or [0]) + 1
        item = {
            'id': next_id,
            'marca_caucho': (data.get('marca_caucho') or data.get('marca') or '').strip(),
            'medida': (data.get('medida') or '').strip(),
            'fecha_instalacion': data.get('fecha_instalacion') or None,
            'km_instalacion': int(data.get('km_instalacion') or 0),
            'vida_util_estimada_km': int(data.get('vida_util_estimada_km') or 0),
            'proximo_aviso_km': int(data.get('proximo_aviso_km') or 0),
            'observaciones': (data.get('observaciones') or '').strip()
        }
        items.append(item)
        self.save_cauchos(vid, items)
        return next_id

    def update_caucho(self, cid, data):
        vehicle = self.fetch_one("transalca",
            "SELECT placa, cauchos_json FROM vehiculos WHERE JSON_CONTAINS(cauchos_json, JSON_OBJECT('id', %s))",
            (cid,))
        if not vehicle:
            return 0
        items = self.get_cauchos(vehicle['placa'])
        for item in items:
            if int(item.get('id', 0)) == int(cid):
                item.update({
                    'marca_caucho': (data.get('marca_caucho') or data.get('marca') or item.get('marca_caucho') or '').strip(),
                    'medida': (data.get('medida') or item.get('medida') or '').strip(),
                    'fecha_instalacion': data.get('fecha_instalacion') or item.get('fecha_instalacion'),
                    'km_instalacion': int(data.get('km_instalacion') or item.get('km_instalacion') or 0),
                    'vida_util_estimada_km': int(data.get('vida_util_estimada_km') or item.get('vida_util_estimada_km') or 0),
                    'proximo_aviso_km': int(data.get('proximo_aviso_km') or item.get('proximo_aviso_km') or 0),
                    'observaciones': (data.get('observaciones') or item.get('observaciones') or '').strip()
                })
                return self.save_cauchos(vehicle['placa'], items)
        return 0

    def delete_caucho(self, cid):
        vehicle = self.fetch_one("transalca",
            "SELECT placa, cauchos_json FROM vehiculos WHERE JSON_CONTAINS(cauchos_json, JSON_OBJECT('id', %s))",
            (cid,))
        if not vehicle:
            return 0
        items = [i for i in self.get_cauchos(vehicle['placa']) if int(i.get('id', 0)) != int(cid)]
        return self.save_cauchos(vehicle['placa'], items)

    def get_history(self, vid, limit=50):
        return self.fetch_all("transalca",
            "SELECT * FROM bitacora_vehiculo WHERE vehiculo_placa = %s "
            "ORDER BY fecha DESC, id DESC LIMIT %s", (self._plate(vid), limit))

    def add_history_entry(self, vid, data):
        vehicle = self.fetch_one("transalca",
            "SELECT placa FROM vehiculos WHERE placa = %s", (self._plate(vid),))
        if not vehicle:
            return None
        return self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_placa, tipo_registro, "
            "descripcion, kilometraje, fecha) VALUES (%s,%s,%s,%s,%s)",
            (vehicle['placa'],
             data.get('tipo_registro', 'observacion'),
             data.get('descripcion', ''),
             data.get('kilometraje'),
             data.get('fecha') or None))
