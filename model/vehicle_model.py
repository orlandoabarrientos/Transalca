from model.connection import Connection
from config.constants import TIPOS_COMBUSTIBLE, validate_choice
import json

VEHICULO_ALIAS = (
    "v.*, v.placa_vehiculo as id, v.placa_vehiculo as placa, v.marca_vehiculo as marca, "
    "v.modelo_vehiculo as modelo, v.anio_vehiculo as anio, v.color_vehiculo as color, "
    "v.observaciones_vehiculo as observaciones, v.cauchos_vehiculo as cauchos_json"
)

BITACORA_ALIAS = (
    "bv.*, bv.id_bitacora_vehiculo AS id, bv.fecha_bitacora as fecha, bv.descripcion_bitacora as descripcion, "
    "bv.observaciones_bitacora as observaciones, bv.cauchos_usados as cauchos_info"
)


class VehicleModel(Connection):
    def __init__(self):
        super().__init__()
        self._placa = None
        self._marca = None
        self._modelo = None

    @property
    def placa(self):
        return self._placa

    @placa.setter
    def placa(self, valor):
        self._placa = self._plate(valor)

    @property
    def marca(self):
        return self._marca

    @marca.setter
    def marca(self, valor):
        if valor:
            valor = str(valor).strip()
        self._marca = valor

    @property
    def modelo(self):
        return self._modelo

    @modelo.setter
    def modelo(self, valor):
        if valor:
            valor = str(valor).strip()
        self._modelo = valor

    def _plate(self, value):
        return (str(value or '').strip().upper())

    def _get_all(self):
        return self.fetch_all("transalca",
            "SELECT " + VEHICULO_ALIAS + ", "
            "COALESCE(GROUP_CONCAT(DISTINCT c.nombre_cliente SEPARATOR ', '), '-') as cliente_nombre, "
            "'' as cliente_apellido "
            "FROM vehiculos v "
            "LEFT JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa AND cv.estado = 1 "
            "LEFT JOIN cliente c ON cv.cliente_cedula = c.identificador_cliente "
            "WHERE v.estado = 1 "
            "GROUP BY v.placa_vehiculo "
            "ORDER BY v.created_at DESC")

    def _get_by_id(self, vid):
        placa = self._plate(vid)
        return self.fetch_one("transalca",
            "SELECT " + VEHICULO_ALIAS + ", "
            "COALESCE(GROUP_CONCAT(DISTINCT c.nombre_cliente SEPARATOR ', '), '-') as cliente_nombre, "
            "'' as cliente_apellido, "
            "COALESCE(GROUP_CONCAT(DISTINCT c.telefono_cliente SEPARATOR ', '), '') as cliente_telefono, "
            "COALESCE(GROUP_CONCAT(DISTINCT c.correo_cliente SEPARATOR ', '), '') as cliente_email, "
            "COALESCE(GROUP_CONCAT(DISTINCT c.identificador_cliente SEPARATOR ','), '') as cliente_cedula "
            "FROM vehiculos v "
            "LEFT JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa AND cv.estado = 1 "
            "LEFT JOIN cliente c ON cv.cliente_cedula = c.identificador_cliente "
            "WHERE v.placa_vehiculo = %s "
            "GROUP BY v.placa_vehiculo", (placa,))

    def _get_by_cliente(self, cliente_cedula):
        return self.fetch_all("transalca",
            "SELECT " + VEHICULO_ALIAS + " "
            "FROM vehiculos v "
            "INNER JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa "
            "WHERE cv.cliente_cedula = %s AND cv.estado = 1 AND v.estado = 1 "
            "ORDER BY cv.created_at DESC", (cliente_cedula,))

    def _get_by_placa(self, placa):
        return self.fetch_one("transalca",
            "SELECT " + VEHICULO_ALIAS + " FROM vehiculos v WHERE v.placa_vehiculo = %s", (self._plate(placa),))

    def _create(self, data):
        validate_choice(data.get('tipo_combustible', 'gasolina'), TIPOS_COMBUSTIBLE, 'tipo_combustible')
        self.marca = data['marca']
        self.modelo = data['modelo']
        self.placa = data.get('placa')
        placa = self._placa
        cliente_cedula = data.get('cliente_cedula', '').strip()

        conn = self.con_transalca()
        conn.begin()
        try:
            existing_vehicle = self.fetch_one("transalca", "SELECT placa_vehiculo, estado FROM vehiculos WHERE placa_vehiculo = %s", (placa,))
            if not existing_vehicle:
                self.insert("transalca",
                    "INSERT INTO vehiculos (marca_vehiculo, modelo_vehiculo, anio_vehiculo, placa_vehiculo, color_vehiculo, "
                    "tipo_vehiculo, tipo_combustible, kilometraje_actual, aceite_info, "
                    "filtros_info, refrigerante_info, observaciones_vehiculo, titulo_vehiculo, estado) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)",
                    (self._marca, self._modelo,
                     data.get('anio') or None, placa,
                     (data.get('color') or '').strip(),
                     (data.get('tipo_vehiculo') or '').strip(),
                     data.get('tipo_combustible', 'gasolina'),
                     int(data.get('kilometraje_actual', 0)),
                     (data.get('aceite_info') or data.get('aceite_usado') or '').strip(),
                     (data.get('filtros_info') or '').strip(),
                     (data.get('refrigerante_info') or '').strip(),
                     (data.get('observaciones') or '').strip(),
                     data.get('titulo_vehiculo') or None))
            elif existing_vehicle['estado'] == 0:
                self.update("transalca", "UPDATE vehiculos SET estado = 1 WHERE placa_vehiculo = %s", (placa,))

            if cliente_cedula:
                existing_rel = self.fetch_one("transalca",
                    "SELECT id_cliente_vehiculo AS id, estado FROM cliente_vehiculo WHERE cliente_cedula = %s AND vehiculo_placa = %s",
                    (cliente_cedula, placa))
                if not existing_rel:
                    self.insert("transalca",
                        "INSERT INTO cliente_vehiculo (cliente_cedula, vehiculo_placa, estado) VALUES (%s, %s, 1)",
                        (cliente_cedula, placa))
                elif existing_rel['estado'] == 0:
                    self.update("transalca", "UPDATE cliente_vehiculo SET estado = 1 WHERE id_cliente_vehiculo = %s", (existing_rel['id'],))

                representante_cedula = data.get('representante_cedula', '').strip()
                if representante_cedula:
                    rep_rel = self.fetch_one("transalca",
                        "SELECT id_empresa_representante AS id FROM representante WHERE empresa_rif = %s AND representante_cedula = %s",
                        (cliente_cedula, representante_cedula))
                    if rep_rel:
                        self.insert("transalca",
                            "INSERT INTO empresa_vehiculo_representante (empresa_representante_id, vehiculo_placa, tipo_operacion) "
                            "VALUES (%s, %s, 'registro')",
                            (rep_rel['id'], placa))
            conn.commit()
            return placa
        except Exception:
            conn.rollback()
            raise

    def _update_vehicle(self, vid, data):
        validate_choice(data.get('tipo_combustible', 'gasolina'), TIPOS_COMBUSTIBLE, 'tipo_combustible')
        self.marca = data['marca']
        self.modelo = data['modelo']
        self.placa = data.get('placa')
        old_placa = self._plate(vid)
        return self.update("transalca",
            "UPDATE vehiculos SET marca_vehiculo=%s, modelo_vehiculo=%s, anio_vehiculo=%s, placa_vehiculo=%s, color_vehiculo=%s, "
            "tipo_vehiculo=%s, tipo_combustible=%s, kilometraje_actual=%s, "
            "aceite_info=%s, filtros_info=%s, refrigerante_info=%s, observaciones_vehiculo=%s "
            "WHERE placa_vehiculo=%s",
            (self._marca, self._modelo,
             data.get('anio') or None,
             self._placa,
             (data.get('color') or '').strip(),
             (data.get('tipo_vehiculo') or '').strip(),
             data.get('tipo_combustible', 'gasolina'),
             int(data.get('kilometraje_actual', 0)),
             (data.get('aceite_info') or data.get('aceite_usado') or '').strip(),
             (data.get('filtros_info') or '').strip(),
             (data.get('refrigerante_info') or '').strip(),
             (data.get('observaciones') or '').strip(), old_placa))

    def _update_kilometraje(self, vid, km):
        km = int(km)
        placa = self._plate(vid)
        vehicle = self.fetch_one("transalca",
            "SELECT placa_vehiculo, kilometraje_actual FROM vehiculos WHERE placa_vehiculo = %s", (placa,))
        if not vehicle:
            return False
        if vehicle and km < vehicle['kilometraje_actual']:
            return False
        self.update("transalca",
            "UPDATE vehiculos SET kilometraje_actual = %s WHERE placa_vehiculo = %s", (km, placa))
        self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_placa, descripcion_bitacora, kilometraje, fecha_bitacora) "
            "VALUES (%s, %s, %s, CURDATE())",
            (vehicle['placa_vehiculo'], f'Kilometraje actualizado a {km} km', km))
        return True

    def _update_carnet_image(self, vid, filename):
        return self.update("transalca",
            "UPDATE vehiculos SET titulo_vehiculo = %s WHERE placa_vehiculo = %s", (filename, self._plate(vid)))

    def _soft_delete(self, vid):
        return self.update("transalca",
            "UPDATE vehiculos SET estado = 0 WHERE placa_vehiculo = %s", (self._plate(vid),))

    def _soft_delete_relationship(self, cliente_cedula, placa):
        return self.update("transalca",
            "UPDATE cliente_vehiculo SET estado = 0 WHERE cliente_cedula = %s AND vehiculo_placa = %s",
            (cliente_cedula, self._plate(placa)))

    def _get_clients_by_vehicle(self, placa):
        rows = self.fetch_all("transalca", "SELECT cliente_cedula FROM cliente_vehiculo WHERE vehiculo_placa = %s AND estado = 1", (self._plate(placa),))
        return [r['cliente_cedula'] for r in rows]

    def _placa_exists(self, placa, exclude_id=None):
        if not placa:
            return False
        placa = self._plate(placa)
        if exclude_id:
            return self.fetch_one("transalca",
                "SELECT placa_vehiculo FROM vehiculos WHERE placa_vehiculo = %s AND placa_vehiculo != %s AND estado = 1",
                (placa, self._plate(exclude_id))) is not None
        return self.fetch_one("transalca",
            "SELECT placa_vehiculo FROM vehiculos WHERE placa_vehiculo = %s AND estado = 1", (placa,)) is not None

    def _get_km_history(self, vid):
        return self.fetch_all("transalca",
            "SELECT " + BITACORA_ALIAS + " FROM bitacora_vehiculo bv WHERE bv.vehiculo_placa = %s "
            "AND bv.kilometraje IS NOT NULL ORDER BY bv.fecha_bitacora DESC, bv.id_bitacora_vehiculo DESC LIMIT 50", (self._plate(vid),))

    def _search(self, query):
        q = f"%{query}%"
        return self.fetch_all("transalca",
            "SELECT " + VEHICULO_ALIAS + ", "
            "COALESCE(GROUP_CONCAT(DISTINCT c.nombre_cliente SEPARATOR ', '), '-') as cliente_nombre, "
            "'' as cliente_apellido "
            "FROM vehiculos v "
            "LEFT JOIN cliente_vehiculo cv ON v.placa_vehiculo = cv.vehiculo_placa AND cv.estado = 1 "
            "LEFT JOIN cliente c ON cv.cliente_cedula = c.identificador_cliente "
            "WHERE v.estado = 1 AND (v.placa_vehiculo LIKE %s OR v.marca_vehiculo LIKE %s OR v.modelo_vehiculo LIKE %s "
            "OR c.nombre_cliente LIKE %s) "
            "GROUP BY v.placa_vehiculo "
            "ORDER BY v.created_at DESC", (q, q, q, q))

    def _get_cauchos(self, vid):
        v = self.fetch_one("transalca",
            "SELECT cauchos_vehiculo FROM vehiculos WHERE placa_vehiculo = %s", (self._plate(vid),))
        if v and v.get('cauchos_vehiculo'):
            try:
                return json.loads(v['cauchos_vehiculo']) if isinstance(v['cauchos_vehiculo'], str) else v['cauchos_vehiculo']
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def _save_cauchos(self, vid, cauchos_data):
        return self.update("transalca",
            "UPDATE vehiculos SET cauchos_vehiculo = %s WHERE placa_vehiculo = %s",
            (json.dumps(cauchos_data, ensure_ascii=False), self._plate(vid)))

    def _add_caucho(self, vid, data):
        items = self._get_cauchos(vid)
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
        self._save_cauchos(vid, items)
        return next_id

    def _update_caucho(self, cid, data):
        vehicle = self.fetch_one("transalca",
            "SELECT placa_vehiculo, cauchos_vehiculo FROM vehiculos WHERE JSON_CONTAINS(cauchos_vehiculo, JSON_OBJECT('id', %s))",
            (cid,))
        if not vehicle:
            return 0
        items = self._get_cauchos(vehicle['placa_vehiculo'])
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
                return self._save_cauchos(vehicle['placa_vehiculo'], items)
        return 0

    def _delete_caucho(self, cid):
        vehicle = self.fetch_one("transalca",
            "SELECT placa_vehiculo, cauchos_vehiculo FROM vehiculos WHERE JSON_CONTAINS(cauchos_vehiculo, JSON_OBJECT('id', %s))",
            (cid,))
        if not vehicle:
            return 0
        items = [i for i in self._get_cauchos(vehicle['placa_vehiculo']) if int(i.get('id', 0)) != int(cid)]
        return self._save_cauchos(vehicle['placa_vehiculo'], items)

    def _get_history(self, vid, limit=50):
        return self.fetch_all("transalca",
            "SELECT " + BITACORA_ALIAS + " FROM bitacora_vehiculo bv WHERE bv.vehiculo_placa = %s "
            "ORDER BY bv.fecha_bitacora DESC, bv.id_bitacora_vehiculo DESC LIMIT %s", (self._plate(vid), limit))

    def _add_history_entry(self, vid, data):
        vehicle = self.fetch_one("transalca",
            "SELECT placa_vehiculo FROM vehiculos WHERE placa_vehiculo = %s", (self._plate(vid),))
        if not vehicle:
            return None
        return self.insert("transalca",
            "INSERT INTO bitacora_vehiculo (vehiculo_placa, "
            "descripcion_bitacora, kilometraje, fecha_bitacora) VALUES (%s,%s,%s,COALESCE(%s, NOW()))",
            (vehicle['placa_vehiculo'],
             data.get('descripcion', ''),
             data.get('kilometraje'),
             data.get('fecha') or None))

    def _reactivar(self, placa):
        return self.update("transalca", "UPDATE vehiculos SET estado = 1 WHERE placa_vehiculo = %s", (placa,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "get_by_cliente": self._get_by_cliente,
            "get_by_placa": self._get_by_placa,
            "create": self._create,
            "update_vehicle": self._update_vehicle,
            "update_kilometraje": self._update_kilometraje,
            "update_carnet_image": self._update_carnet_image,
            "soft_delete": self._soft_delete,
            "soft_delete_relationship": self._soft_delete_relationship,
            "get_clients_by_vehicle": self._get_clients_by_vehicle,
            "placa_exists": self._placa_exists,
            "get_km_history": self._get_km_history,
            "search": self._search,
            "get_cauchos": self._get_cauchos,
            "save_cauchos": self._save_cauchos,
            "add_caucho": self._add_caucho,
            "update_caucho": self._update_caucho,
            "delete_caucho": self._delete_caucho,
            "get_history": self._get_history,
            "add_history_entry": self._add_history_entry,
            "reactivar": self._reactivar,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
