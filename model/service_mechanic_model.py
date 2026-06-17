import re

from model.connection import Connection
from config.constants import ESTADOS_SERVICIO_MECANICO
from config.validation import SELECT_TAMPER_MESSAGE, ValidationError, normalize_int, optional_text, validate_choice

ESTADOS_REQUIEREN_DATOS = {'en_proceso', 'completado'}
OBSERVACIONES_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9\s.,\-]+$")


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

    def _cliente_exists(self, cliente_cedula):
        if not cliente_cedula:
            return False
        if self.fetch_one("transalca", "SELECT id_cliente FROM cliente WHERE identificador_cliente = %s", (cliente_cedula,)):
            return True
        return self.fetch_one("mantenimiento", "SELECT id FROM usuarios WHERE cedula = %s", (cliente_cedula,)) is not None

    def _vehiculo_exists(self, vehiculo_placa):
        if not vehiculo_placa:
            return False
        return self.fetch_one("transalca", "SELECT placa_vehiculo FROM vehiculos WHERE placa_vehiculo = %s", (vehiculo_placa,)) is not None

    def _mechanic_busy_elsewhere(self, mecanico_cedula, exclude_id=None):
        mecanico_cedula = (mecanico_cedula or '').strip()
        if not mecanico_cedula:
            return False
        if exclude_id:
            return self.fetch_one("transalca",
                "SELECT 1 FROM servicio_mecanico WHERE mecanico_cedula = %s AND estado_servicio IN ('asignado', 'en_proceso') AND id_servicio_mecanico != %s LIMIT 1",
                (mecanico_cedula, exclude_id)) is not None
        return self.fetch_one("transalca",
            "SELECT 1 FROM servicio_mecanico WHERE mecanico_cedula = %s AND estado_servicio IN ('asignado', 'en_proceso') LIMIT 1",
            (mecanico_cedula,)) is not None

    def _missing_required_data(self, item, estado, mecanico_cedula=None):
        errors = {}
        if estado not in ESTADOS_REQUIEREN_DATOS:
            return errors
        mecanico = mecanico_cedula if mecanico_cedula is not None else (item or {}).get('mecanico_cedula')
        if not mecanico:
            errors['mecanico_cedula'] = 'Debe asignar un mecanico antes de cambiar el estado.'
        if not (item or {}).get('cliente_cedula'):
            errors['cliente_cedula'] = 'Debe asignar un cliente antes de cambiar el estado.'
        if not (item or {}).get('vehiculo_placa'):
            errors['vehiculo_placa'] = 'Debe asignar un vehiculo antes de cambiar el estado.'
        return errors

    def _validate(self, data, current_id=None):
        errors = {}
        servicio_id = normalize_int(errors, 'servicio_id', data.get('servicio_id'), 'El servicio')
        orden_venta_id = None
        if data.get('orden_venta_id') not in (None, ''):
            orden_venta_id = normalize_int(errors, 'orden_venta_id', data.get('orden_venta_id'), 'La orden')
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip() or None
        observaciones_raw = data.get('observaciones')
        if observaciones_raw is not None and str(observaciones_raw) != '' and not str(observaciones_raw).strip():
            errors['observaciones'] = 'Las observaciones no pueden contener solo espacios en blanco.'
        observaciones = optional_text(errors, 'observaciones', data.get('observaciones'), 'Las observaciones', max_len=255, allow_serial=True)
        if observaciones and 'observaciones' not in errors and not OBSERVACIONES_RE.match(observaciones):
            errors['observaciones'] = 'Las observaciones solo pueden contener letras, numeros, espacios, puntos, comas y guiones.'
        cliente_cedula = (data.get('cliente_cedula') or '').strip() or None
        if not cliente_cedula:
            errors['cliente_cedula'] = 'Debe seleccionar un cliente.'
        vehiculo_placa = (data.get('vehiculo_placa') or '').strip().upper() or None
        if not vehiculo_placa:
            errors['vehiculo_placa'] = 'Debe seleccionar un vehiculo.'
        estado_default = 'asignado' if mecanico_cedula else 'sin_asignar'
        estado = validate_choice(errors, 'estado', data.get('estado') or estado_default, ESTADOS_SERVICIO_MECANICO)

        current = self._get_by_id(current_id) if current_id else None

        if servicio_id:
            is_current_service = current and current.get('servicio_id') == servicio_id
            if not is_current_service and not self._service_exists(servicio_id):
                errors['servicio_id'] = SELECT_TAMPER_MESSAGE

        if mecanico_cedula:
            is_current_mechanic = current and current.get('mecanico_cedula') == mecanico_cedula
            if not is_current_mechanic and not self._mechanic_exists(mecanico_cedula):
                errors['mecanico_cedula'] = SELECT_TAMPER_MESSAGE

        if cliente_cedula:
            is_current_cliente = current and current.get('cliente_cedula') == cliente_cedula
            if not is_current_cliente and not self._cliente_exists(cliente_cedula):
                errors['cliente_cedula'] = SELECT_TAMPER_MESSAGE

        if vehiculo_placa:
            is_current_vehiculo = current and current.get('vehiculo_placa') == vehiculo_placa
            if not is_current_vehiculo and not self._vehiculo_exists(vehiculo_placa):
                errors['vehiculo_placa'] = SELECT_TAMPER_MESSAGE

        if orden_venta_id and not self._order_exists(orden_venta_id):
            errors['orden_venta_id'] = 'La orden seleccionada no existe.'

        if estado in ESTADOS_REQUIEREN_DATOS and not errors:
            candidate = {
                'mecanico_cedula': mecanico_cedula,
                'cliente_cedula': cliente_cedula or (current or {}).get('cliente_cedula'),
                'vehiculo_placa': vehiculo_placa or (current or {}).get('vehiculo_placa'),
            }
            errors.update(self._missing_required_data(candidate, estado, mecanico_cedula))
        if errors:
            raise ValidationError(errors)
        return {
            'servicio_id': servicio_id,
            'mecanico_cedula': mecanico_cedula,
            'orden_venta_id': orden_venta_id,
            'observaciones': observaciones,
            'cliente_cedula': cliente_cedula,
            'vehiculo_placa': vehiculo_placa,
            'estado': estado
        }

    def _validate_mechanic_update(self, data):
        errors = {}
        mecanico_cedula = (data.get('mecanico_cedula') or '').strip()
        if not mecanico_cedula:
            errors['mecanico_cedula'] = 'Debe seleccionar un mecanico.'
        elif not self._mechanic_exists(mecanico_cedula):
            errors['mecanico_cedula'] = SELECT_TAMPER_MESSAGE
        porcentaje_raw = data.get('porcentaje_comision')
        porcentaje = None
        if porcentaje_raw in (None, ''):
            errors['porcentaje_comision'] = 'El porcentaje de comision es obligatorio.'
        else:
            try:
                porcentaje = float(porcentaje_raw)
            except (TypeError, ValueError):
                errors['porcentaje_comision'] = 'El porcentaje de comision debe ser numerico.'
            else:
                if porcentaje <= 0 or porcentaje > 100:
                    errors['porcentaje_comision'] = 'El porcentaje de comision debe ser mayor a 0 y maximo 100.'
        if errors:
            raise ValidationError(errors)
        return mecanico_cedula, porcentaje

    def _assign(self, data):
        clean = self._validate(data)
        mecanico_cedula = clean['mecanico_cedula']
        estado = clean['estado']
        if not mecanico_cedula and (not estado or estado == 'asignado'):
            estado = 'sin_asignar'
        if mecanico_cedula and (not estado or estado == 'sin_asignar'):
            estado = 'asignado'
        return self.insert("transalca",
            "INSERT INTO servicio_mecanico (servicio_id, mecanico_cedula, orden_venta_id, observaciones_servicio, cliente_cedula, vehiculo_placa, estado_servicio, fecha_servicio) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())",
            (clean['servicio_id'], mecanico_cedula, clean['orden_venta_id'], (clean['observaciones'] or ''),
             clean['cliente_cedula'], clean['vehiculo_placa'], estado or 'sin_asignar'))

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
        errors = {}
        estado = validate_choice(errors, 'estado', estado, ESTADOS_SERVICIO_MECANICO)
        if not errors:
            errors.update(self._missing_required_data(self._get_by_id(aid), estado))
        if errors:
            raise ValidationError(errors)
        return self.update("transalca",
            "UPDATE servicio_mecanico SET estado_servicio = %s WHERE id_servicio_mecanico = %s", (estado, aid))

    def _update_assignment(self, aid, data):
        clean = self._validate(data, current_id=aid)
        mecanico_cedula = clean['mecanico_cedula']
        estado = clean['estado']
        if not mecanico_cedula and estado in (None, '', 'asignado'):
            estado = 'sin_asignar'
        return self.update("transalca",
            "UPDATE servicio_mecanico SET servicio_id = %s, mecanico_cedula = %s, orden_venta_id = %s, observaciones_servicio = %s, cliente_cedula = %s, vehiculo_placa = %s, estado_servicio = %s WHERE id_servicio_mecanico = %s",
            (clean['servicio_id'], mecanico_cedula, clean['orden_venta_id'], (clean['observaciones'] or ''),
             clean['cliente_cedula'], clean['vehiculo_placa'], estado or 'sin_asignar', aid))

    def _delete_assignment(self, aid):
        return self.delete("transalca", "DELETE FROM servicio_mecanico WHERE id_servicio_mecanico = %s", (aid,))

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "get_all": self._get_all,
            "get_by_id": self._get_by_id,
            "service_exists": self._service_exists,
            "mechanic_exists": self._mechanic_exists,
            "mechanic_busy_elsewhere": self._mechanic_busy_elsewhere,
            "order_exists": self._order_exists,
            "validate": self._validate,
            "validate_mechanic_update": self._validate_mechanic_update,
            "assign": self._assign,
            "update_mechanic": self._update_mechanic,
            "update_status": self._update_status,
            "update_assignment": self._update_assignment,
            "delete_assignment": self._delete_assignment,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)
