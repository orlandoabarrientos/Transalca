import pytest
from unittest.mock import patch
from model.sucursal_model import SucursalModel
from config.validation import ValidationError


class TestSucursalModelProperties:
    """Pruebas unitarias para getters y setters del modelo de sucursal."""

    def test_property_setters_strip_whitespace(self):
        model = SucursalModel()
        model.nombre = "  Sucursal Barquisimeto Este  "
        model.direccion = "  Av. Lara con Av. Los Leones  "
        model.telefono = "  04145551234  "
        model.email = "  barquisimeto@transalca.com  "

        assert model.nombre == "Sucursal Barquisimeto Este"
        assert model.direccion == "Av. Lara con Av. Los Leones"
        assert model.telefono == "04145551234"
        assert model.email == "barquisimeto@transalca.com"

    def test_property_setters_none(self):
        model = SucursalModel()
        model.nombre = None
        model.direccion = None

        assert model.nombre is None
        assert model.direccion is None


class TestSucursalModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de sucursal."""

    # DATA PROVIDER: Pruebas con nombres de sucursal válidos
    @pytest.mark.parametrize("valid_nombre", [
        "Sucursal Centro",
        "Sucursal Barquisimeto Este",
        "Sucursal Cabudare",
        "Sucursal Principal No 1",
    ])
    def test_validate_valid_nombre_data_provider(self, valid_nombre):
        model = SucursalModel()
        data = {
            "nombre": valid_nombre,
            "direccion": "Av. Principal 123",
            "telefono": "04121234567",
            "email": "sucursal@transalca.com"
        }
        clean = model._validate(data)
        assert clean["nombre"] == valid_nombre

    # DATA PROVIDER: Pruebas con nombres de sucursal inválidos
    @pytest.mark.parametrize("invalid_nombre", [
        "",         # Nombre vacío
        "AB",       # Menor a 3 caracteres
    ])
    def test_validate_invalid_nombre_data_provider(self, invalid_nombre):
        model = SucursalModel()
        data = {
            "nombre": invalid_nombre,
            "direccion": "Av. Principal 123"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "nombre" in exc_info.value.errors

    # DATA PROVIDER: Pruebas de validación de dirección
    @pytest.mark.parametrize("invalid_direccion", [
        "   ",                      # Solo espacios en blanco
        "Dirección con <script>",    # Caracteres no seguros / HTML tag
    ])
    def test_validate_invalid_direccion_data_provider(self, invalid_direccion):
        model = SucursalModel()
        data = {
            "nombre": "Sucursal Centro",
            "direccion": invalid_direccion
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "direccion" in exc_info.value.errors


class TestSucursalModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones CRUD de sucursal."""

    @patch.object(SucursalModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "Sucursal Centro", "direccion": "Av. Vargas", "estado": 1}
        ]
        model = SucursalModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "Sucursal Centro"
        mock_fetch_all.assert_called_once()

    @patch.object(SucursalModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "nombre": "Sucursal Centro"}
        model = SucursalModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()

    @patch.object(SucursalModel, "_get_by_nombre")
    def test_create_duplicate_active_sucursal_raises_error(self, mock_get_by_nombre):
        mock_get_by_nombre.return_value = {"id": 1, "nombre": "Sucursal Centro", "estado": 1}

        model = SucursalModel()
        data = {
            "nombre": "Sucursal Centro",
            "direccion": "Av. Vargas"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", data)

        assert "nombre" in exc_info.value.errors

    @patch.object(SucursalModel, "update")
    def test_soft_delete(self, mock_update):
        mock_update.return_value = 1
        model = SucursalModel()
        result = model.ejecutar("soft_delete", 1)

        assert result == 1
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = SucursalModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
