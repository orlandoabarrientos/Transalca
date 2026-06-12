from model.connection import Connection


class ServiceMechanicModel(Connection):
    def __init__(self):
        super().__init__()

    def _get_all(self):
        assignments = self.fetch_all("transalca",
            "SELECT sm.id_servicio_mecanico AS id, sm.servicio_id, sm.mecanico_cedula, sm.orden_venta_id, "
            "DATE_FORMAT(sm.fecha_servicio, '%%Y-%%m-%%dT%%H:%%i') as fecha, "
            "sm.estado_servicio AS estado, sm.observaciones_servicio AS observaciones, "
            "s.nombre_servicio as servicio_nombre, s.precio_servicio AS precio, "
            "m.nombre_mecanico as mecanico_nombre_base, m.apellido_mecanico as mecanico_apellido_base, "
            "COALESCE(sm.cliente_cedula, ov.cliente_cedula) as cliente_cedula, "
            "COALESCE(sm.vehiculo_placa, bv.vehiculo_placa) as vehiculo_placa, "
            "cm.porcentaje_comision "
            "FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "LEFT JOIN ordenes_venta ov ON sm.orden_venta_id = ov.id_orden_venta "
            "LEFT JOIN bitacora_vehiculo bv ON sm.id_servicio_mecanico = bv.servicio_mecanico_id "
            "LEFT JOIN comisiones_mecanico cm ON cm.servicio_mecanico_id = sm.id_servicio_mecanico "
            "ORDER BY sm.fecha_servicio DESC")
        for a in assignments:
            nombre = (a.get('mecanico_nombre_base') or '').strip()
            apellido = (a.get('mecanico_apellido_base') or '').strip()
            full_name = f"{nombre} {apellido}".strip()
            a['mecanico_nombre'] = full_name if full_name else 'Sin asignar'
            a.pop('mecanico_nombre_base', None)
            a.pop('mecanico_apellido_base', None)
        return assignments

    def _get_by_id(self, aid):
        item = self.fetch_one("transalca",
            "SELECT sm.id_servicio_mecanico AS id, sm.servicio_id, sm.mecanico_cedula, sm.orden_venta_id, "
            "DATE_FORMAT(sm.fecha_servicio, '%%Y-%%m-%%dT%%H:%%i') as fecha, "
            "sm.estado_servicio AS estado, sm.observaciones_servicio AS observaciones, "
            "s.nombre_servicio as servicio_nombre, s.precio_servicio AS precio, "
            "COALESCE(sm.cliente_cedula, ov.cliente_cedula) as cliente_cedula, "
            "COALESCE(sm.vehiculo_placa, bv.vehiculo_placa) as vehiculo_placa, "
            "c.nombre_cliente as cliente_nombre, '' as cliente_apellido, "
            "v.marca_vehiculo as vehiculo_marca, v.modelo_vehiculo as vehiculo_modelo, "
            "m.nombre_mecanico as mecanico_nombre_base, m.apellido_mecanico as mecanico_apellido_base, "
            "cm.porcentaje_comision "
            "FROM servicio_mecanico sm "
            "INNER JOIN servicios s ON sm.servicio_id = s.id_servicio "
            "LEFT JOIN ordenes_venta ov ON sm.orden_venta_id = ov.id_orden_venta "
            "LEFT JOIN bitacora_vehiculo bv ON sm.id_servicio_mecanico = bv.servicio_mecanico_id "
            "LEFT JOIN cliente c ON COALESCE(sm.cliente_cedula, ov.cliente_cedula) = c.identificador_cliente "
            "LEFT JOIN vehiculos v ON COALESCE(sm.vehiculo_placa, bv.vehiculo_placa) = v.placa_vehiculo "
            "LEFT JOIN mecanicos m ON sm.mecanico_cedula = m.cedula_mecanico "
            "LEFT JOIN comisiones_mecanico cm ON cm.servicio_mecanico_id = sm.id_servicio_mecanico "
            "WHERE sm.id_servicio_mecanico = %s", (aid,))
        if item:
            nombre = (item.get('mecanico_nombre_base') or '').strip()
            apellido = (item.get('mecanico_apellido_base') or '').strip()
            full_name = f"{nombre} {apellido}".strip()
            item['mecanico_nombre'] = full_name if full_name else None
            item.pop('mecanico_nombre_base', None)
            item.pop('mecanico_apellido_base', None)
        return item

    def _service_exists(self, servicio_id):
        return self.fetch_one("transalca", "SELECT id_servicio FROM servicios WHERE id_servicio = %s AND estado = 1", (servicio_id,)) is not None

    def _mechanic_exists(self, cedula):
        if not cedula:
            return True
        return self.fetch_one("transalca", "SELECT cedula_mecanico FROM mecanicos WHERE cedula_mecanico = %s AND estado = 1", (cedula,)) is not None

    def _order_exists(self, orden_venta_id):
        if not orden_venta_id:
            return True
        return self.fetch_one("transalca", "SELECT id_orden_venta FROM ordenes_venta WHERE id_orden_venta = %s", (orden_venta_id,)) is not None

    def _assign(self, data):
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip() or None
        estado = data.get('estado')
        if not mecanico_cedula and (not estado or estado == 'asignado'):
            estado = 'sin_asignar'
        if mecanico_cedula and (not estado or estado == 'sin_asignar'):
            estado = 'asignado'
        return self.insert("transalca",
            "INSERT INTO servicio_mecanico (servicio_id, mecanico_cedula, orden_venta_id, observaciones_servicio, cliente_cedula, vehiculo_placa, estado_servicio, fecha_servicio) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
            (data['servicio_id'], mecanico_cedula, data.get('orden_venta_id') or None, data.get('observaciones', '').strip(),
             data.get('cliente_cedula') or None, data.get('vehiculo_placa') or None, estado or 'sin_asignar'))

    def _update_mechanic(self, aid, mecanico_cedula):
        mecanico_cedula = (mecanico_cedula or '').strip()
        value = mecanico_cedula or None
        if value:
            return self.update("transalca",
                "UPDATE servicio_mecanico SET mecanico_cedula = %s, "
                "estado_servicio = CASE WHEN estado_servicio = 'sin_asignar' THEN 'asignado' ELSE estado_servicio END "
                "WHERE id_servicio_mecanico = %s", (value, aid))
        return self.update("transalca",
            "UPDATE servicio_mecanico SET mecanico_cedula = NULL, "
            "estado_servicio = CASE WHEN estado_servicio IN ('asignado','pendiente') THEN 'sin_asignar' ELSE estado_servicio END "
            "WHERE id_servicio_mecanico = %s", (aid,))

    def _update_status(self, aid, estado):
        return self.update("transalca",
            "UPDATE servicio_mecanico SET estado_servicio = %s WHERE id_servicio_mecanico = %s", (estado, aid))

    def _update_assignment(self, aid, data):
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip() or None
        estado = data.get('estado')
        if not mecanico_cedula and estado in (None, '', 'asignado'):
            estado = 'sin_asignar'
        return self.update("transalca",
            "UPDATE servicio_mecanico SET servicio_id = %s, mecanico_cedula = %s, orden_venta_id = %s, observaciones_servicio = %s, cliente_cedula = %s, vehiculo_placa = %s, estado_servicio = %s WHERE id_servicio_mecanico = %s",
            (data['servicio_id'], mecanico_cedula, data.get('orden_venta_id') or None, data.get('observaciones', '').strip(),
             data.get('cliente_cedula') or None, data.get('vehiculo_placa') or None, estado or 'sin_asignar', aid))

    def _delete_assignment(self, aid):
        return self.delete("transalca", "DELETE FROM servicio_mecanico WHERE id_servicio_mecanico = %s", (aid,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "service_exists": self._service_exists,
            "mechanic_exists": self._mechanic_exists,
            "order_exists": self._order_exists,
            "assign": self._assign,
            "update_mechanic": self._update_mechanic,
            "update_status": self._update_status,
            "update_assignment": self._update_assignment,
            "delete_assignment": self._delete_assignment,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
