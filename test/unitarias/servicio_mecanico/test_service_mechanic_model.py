import pytest
from unittest.mock import patch
from model.service_mechanic_model import ServiceMechanicModel
from config.validation import ValidationError


class TestServiceMechanicModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de servicio mecánico."""

    # DATA PROVIDER: Pruebas con estados válidos de servicio mecánico
    @pytest.mark.parametrize("estado_valido", [
        "sin_asignar",
        "asignado",
        "en_proceso",
        "completado",
        "cancelado",
    ])
    @patch.object(ServiceMechanicModel, "_vehiculo_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_cliente_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_mechanic_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_service_exists", return_value=True)
    def test_validate_valid_estados_data_provider(
        self, mock_serv, mock_mech, mock_cli, mock_veh, estado_valido
    ):
        model = ServiceMechanicModel()
        data = {
            "servicio_id": 1,
            "mecanico_cedula": "V-12345678",
            "cliente_cedula": "V-87654321",
            "vehiculo_placa": "ABC123",
            "estado": estado_valido
        }
        clean = model._validate(data)
        assert clean["estado"] == estado_valido
        assert clean["servicio_id"] == 1

    # DATA PROVIDER: Pruebas con estados inválidos
    @pytest.mark.parametrize("invalid_estado", [
        "estado_fantasma",
        "finalizado_exitosamente",
    ])
    @patch.object(ServiceMechanicModel, "_vehiculo_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_cliente_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_service_exists", return_value=True)
    def test_validate_invalid_estados_data_provider(
        self, mock_serv, mock_cli, mock_veh, invalid_estado
    ):
        model = ServiceMechanicModel()
        data = {
            "servicio_id": 1,
            "cliente_cedula": "V-87654321",
            "vehiculo_placa": "ABC123",
            "estado": invalid_estado
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "estado" in exc_info.value.errors

    # DATA PROVIDER: Validación de porcentaje de comisión en actualización de mecánico
    @pytest.mark.parametrize("porcentaje, is_valid", [
        (10, True),
        (50.5, True),
        (100, True),
        (0, False),         # Debe ser mayor a 0
        (-15, False),       # Negativo
        (105, False),       # Mayor a 100
        ("invalido", False) # No numérico
    ])
    @patch.object(ServiceMechanicModel, "_mechanic_exists", return_value=True)
    def test_validate_mechanic_update_commission_data_provider(
        self, mock_mech_exists, porcentaje, is_valid
    ):
        model = ServiceMechanicModel()
        data = {
            "mecanico_cedula": "V-12345678",
            "porcentaje_comision": porcentaje
        }
        if is_valid:
            cedula, pct = model._validate_mechanic_update(data)
            assert cedula == "V-12345678"
            assert pct == float(porcentaje)
        else:
            with pytest.raises(ValidationError) as exc_info:
                model._validate_mechanic_update(data)
            assert "porcentaje_comision" in exc_info.value.errors

    @patch.object(ServiceMechanicModel, "_vehiculo_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_cliente_exists", return_value=True)
    @patch.object(ServiceMechanicModel, "_service_exists", return_value=True)
    def test_validate_en_proceso_without_mechanic_fails(
        self, mock_serv, mock_cli, mock_veh
    ):
        model = ServiceMechanicModel()
        data = {
            "servicio_id": 1,
            "cliente_cedula": "V-87654321",
            "vehiculo_placa": "ABC123",
            "estado": "en_proceso"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "mecanico_cedula" in exc_info.value.errors


class TestServiceMechanicModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para servicio mecánico."""

    @patch.object(ServiceMechanicModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {
                "id": 1,
                "servicio_id": 1,
                "servicio_nombre": "Alineación",
                "mecanico_nombre_base": "Carlos",
                "mecanico_apellido_base": "Gómez",
                "estado": "asignado"
            }
        ]
        model = ServiceMechanicModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["mecanico_nombre"] == "Carlos Gómez"
        mock_fetch_all.assert_called_once()

    @patch.object(ServiceMechanicModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {
            "id": 1,
            "servicio_id": 1,
            "mecanico_nombre_base": "Carlos",
            "mecanico_apellido_base": "Gómez"
        }
        model = ServiceMechanicModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        assert result["mecanico_nombre"] == "Carlos Gómez"

    @patch.object(ServiceMechanicModel, "insert")
    @patch.object(ServiceMechanicModel, "_validate")
    def test_assign(self, mock_validate, mock_insert):
        mock_validate.return_value = {
            "servicio_id": 1,
            "mecanico_cedula": "V-12345678",
            "orden_venta_id": None,
            "observaciones": "Revisión rápida",
            "cliente_cedula": "V-87654321",
            "vehiculo_placa": "ABC123",
            "estado": "asignado"
        }
        mock_insert.return_value = 10

        model = ServiceMechanicModel()
        data = {
            "servicio_id": 1,
            "mecanico_cedula": "V-12345678",
            "cliente_cedula": "V-87654321",
            "vehiculo_placa": "ABC123"
        }
        aid = model.ejecutar("assign", data)

        assert aid == 10
        mock_insert.assert_called_once()

    @patch.object(ServiceMechanicModel, "delete")
    def test_delete_assignment(self, mock_delete):
        mock_delete.return_value = 1
        model = ServiceMechanicModel()
        result = model.ejecutar("delete_assignment", 1)

        assert result == 1
        mock_delete.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = ServiceMechanicModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
