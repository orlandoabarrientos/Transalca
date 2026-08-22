import pytest
from unittest.mock import patch
from model.service_model import ServiceModel
from config.validation import ValidationError


class TestServiceModelProperties:
    """Pruebas unitarias para getters y setters del modelo de servicio."""

    def test_property_setters_strip_whitespace(self):
        model = ServiceModel()
        model.nombre = "  Alineación y Balanceo  "
        model.descripcion = "  Servicio completo de suspensión  "
        model.tipo = "  alineacion  "
        model.precio = 25.50

        assert model.nombre == "Alineación y Balanceo"
        assert model.descripcion == "Servicio completo de suspensión"
        assert model.tipo == "alineacion"
        assert model.precio == 25.50

    def test_property_setters_none(self):
        model = ServiceModel()
        model.nombre = None
        model.descripcion = None
        model.tipo = None

        assert model.nombre is None
        assert model.descripcion is None
        assert model.tipo is None


class TestServiceModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de servicio."""

    # DATA PROVIDER: Pruebas con tipos de servicio válidos
    @pytest.mark.parametrize("tipo_valido", [
        "alineacion",
        "rotacion",
        "balanceo",
        "cambio_aceite",
        "general",
    ])
    @patch.object(ServiceModel, "_sucursal_exists", return_value=True)
    def test_validate_valid_tipos_data_provider(self, mock_suc_exists, tipo_valido):
        model = ServiceModel()
        data = {
            "nombre": "Alineación Computarizada",
            "descripcion": "Alineación de tren delantero",
            "precio": 30.00,
            "tipo": tipo_valido,
            "sucursal_ids": [1]
        }
        clean = model._validate(data)
        assert clean["tipo"] == tipo_valido
        assert clean["precio"] == 30.00

    # DATA PROVIDER: Pruebas con tipos de servicio inválidos
    @pytest.mark.parametrize("invalid_tipo", [
        "inventado",
        "mantenimiento_super_express",
        "",
    ])
    def test_validate_invalid_tipos_data_provider(self, invalid_tipo):
        model = ServiceModel()
        data = {
            "nombre": "Servicio Test",
            "precio": 30.00,
            "tipo": invalid_tipo,
            "sucursal_ids": [1]
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "tipo" in exc_info.value.errors

    # DATA PROVIDER: Validaciones de precios inválidos
    @pytest.mark.parametrize("invalid_precio", [
        -10.00,        # Precio negativo
        "abc",         # No numérico
    ])
    def test_validate_invalid_precios_data_provider(self, invalid_precio):
        model = ServiceModel()
        data = {
            "nombre": "Servicio Test",
            "precio": invalid_precio,
            "tipo": "general",
            "sucursal_ids": [1]
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "precio" in exc_info.value.errors

    # DATA PROVIDER: Validaciones de sucursal vacía o no seleccionada
    @pytest.mark.parametrize("empty_sucursal_ids", [
        [],
        None,
        "",
    ])
    def test_validate_missing_sucursal_data_provider(self, empty_sucursal_ids):
        model = ServiceModel()
        data = {
            "nombre": "Servicio Test",
            "precio": 30.00,
            "tipo": "general",
            "sucursal_ids": empty_sucursal_ids
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "sucursal_id" in exc_info.value.errors


class TestServiceModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones CRUD de servicio."""

    @patch.object(ServiceModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "Cambio de Aceite", "precio": 20.00, "estado": 1}
        ]
        model = ServiceModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "Cambio de Aceite"
        mock_fetch_all.assert_called_once()

    @patch.object(ServiceModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "nombre": "Cambio de Aceite", "precio": 20.00}
        model = ServiceModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()

    @patch.object(ServiceModel, "_get_by_nombre")
    @patch.object(ServiceModel, "_validate")
    def test_create_duplicate_active_service_raises_error(self, mock_validate, mock_get_by_nombre):
        mock_validate.return_value = {
            "nombre": "Cambio de Aceite",
            "descripcion": "",
            "tipo": "cambio_aceite",
            "precio": 20.00,
            "duracion_estimada": 60,
            "sucursal_ids": [1]
        }
        mock_get_by_nombre.return_value = {"id": 1, "nombre": "Cambio de Aceite", "estado": 1}

        model = ServiceModel()
        data = {
            "nombre": "Cambio de Aceite",
            "precio": 20.00,
            "tipo": "cambio_aceite",
            "sucursal_ids": [1]
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", data)

        assert "nombre" in exc_info.value.errors

    @patch.object(ServiceModel, "update")
    def test_soft_delete(self, mock_update):
        mock_update.return_value = 1
        model = ServiceModel()
        result = model.ejecutar("soft_delete", 1)

        assert result == 1
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = ServiceModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
