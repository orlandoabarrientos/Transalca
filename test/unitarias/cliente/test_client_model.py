import pytest
from unittest.mock import MagicMock, patch
from model.client_model import ClientModel
from config.validation import ValidationError


class TestClientModelProperties:
    """Pruebas unitarias para getters y setters del modelo de cliente."""

    def test_property_setters_strip_whitespace(self):
        model = ClientModel()
        model.cedula = "  V-12345678  "
        model.nombre = "  Ana  "
        model.apellido = "  López  "
        model.email = "  cliente@ejemplo.com  "
        model.telefono = "  04121234567  "
        model.direccion = "  Av. Principal  "

        assert model.cedula == "V-12345678"
        assert model.nombre == "Ana"
        assert model.apellido == "López"
        assert model.email == "cliente@ejemplo.com"
        assert model.telefono == "04121234567"
        assert model.direccion == "Av. Principal"

    def test_full_name_static_method(self):
        assert ClientModel._full_name({"nombre": "Juan", "apellido": "Pérez"}) == "Juan Pérez"
        assert ClientModel._full_name({"nombre": "Empresa C.A.", "apellido": ""}) == "Empresa C.A."


class TestClientModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de cliente."""

    # DATA PROVIDER: Pruebas con diferentes formatos de cédula válidos
    @pytest.mark.parametrize("input_cedula, expected_cedula, expected_prefijo", [
        ("V-12345678", "V-12345678", "V"),
        ("E-87654321", "E-87654321", "E"),
        ("J-12345678", "J-12345678", "J"),
        ("v 12345678", "V-12345678", "V"),
        ("V12345678", "V-12345678", "V"),
    ])
    def test_validate_valid_cedulas_data_provider(self, input_cedula, expected_cedula, expected_prefijo):
        model = ClientModel()
        data = {
            "cedula": input_cedula,
            "nombre": "Ana",
            "apellido": "López",
            "telefono": "04141234567",
            "email": "ana@ejemplo.com"
        }
        clean = model._validate(data)
        assert clean["cedula"] == expected_cedula
        assert clean["cedula_prefijo"] == expected_prefijo

    # DATA PROVIDER: Pruebas con formatos de cédulas inválidos
    @pytest.mark.parametrize("invalid_cedula", [
        "XYZ-99999",
        "123",            # Cédula muy corta
        "V-ABCDEFGH",     # Letras en parte numérica
        "",               # Cédula vacía
    ])
    def test_validate_invalid_cedulas_data_provider(self, invalid_cedula):
        model = ClientModel()
        data = {
            "cedula": invalid_cedula,
            "nombre": "Ana",
            "telefono": "04141234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data, require_cedula=True)
        assert "cedula" in exc_info.value.errors

    # DATA PROVIDER: Validaciones de campos de teléfono y correo
    @pytest.mark.parametrize("telefono, email, expected_error_field", [
        ("123", "ana@ejemplo.com", "telefono"),             # Teléfono inválido
        ("04141234567", "correo_invalido", "email"),         # Correo inválido
        ("04141234567", "sin_arroba.com", "email"),          # Correo sin @
    ])
    def test_validate_contact_fields_data_provider(self, telefono, email, expected_error_field):
        model = ClientModel()
        data = {
            "cedula": "V-12345678",
            "nombre": "Ana",
            "telefono": telefono,
            "email": email
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert expected_error_field in exc_info.value.errors


class TestClientModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones CRUD de cliente."""

    @patch.object(ClientModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"cedula": "V-12345678", "nombre": "Ana López", "telefono": "04141234567", "estado": 1}
        ]
        model = ClientModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["cedula"] == "V-12345678"
        mock_fetch_all.assert_called_once()

    @patch.object(ClientModel, "fetch_one")
    def test_get_by_cedula(self, mock_fetch_one):
        mock_fetch_one.return_value = {"cedula": "V-12345678", "nombre": "Ana López"}
        model = ClientModel()
        result = model.ejecutar("get_by_cedula", "V-12345678")

        assert result["cedula"] == "V-12345678"
        mock_fetch_one.assert_called_once()

    @patch.object(ClientModel, "_get_by_cedula")
    def test_create_duplicate_active_client_raises_error(self, mock_get_by_cedula):
        mock_get_by_cedula.return_value = {"cedula": "V-12345678", "estado": 1}

        model = ClientModel()
        data = {
            "cedula": "V-12345678",
            "nombre": "Ana",
            "telefono": "04141234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", data)

        assert "cedula" in exc_info.value.errors

    @patch.object(ClientModel, "update")
    @patch.object(ClientModel, "_get_by_cedula")
    def test_soft_delete(self, mock_get_by_cedula, mock_update):
        mock_get_by_cedula.return_value = {"cedula": "V-12345678", "estado": 0}
        mock_update.return_value = 1

        model = ClientModel()
        result = model.ejecutar("soft_delete", "V-12345678")

        assert result == 0
        mock_update.assert_called_once()

    @patch.object(ClientModel, "fetch_one")
    def test_get_stats(self, mock_fetch_one):
        mock_fetch_one.side_effect = [{"total": 10}, {"total": 8}]
        model = ClientModel()
        stats = model.ejecutar("get_stats", "persona")

        assert stats["total"] == 10
        assert stats["activos"] == 8

    def test_ejecutar_invalid_action(self):
        model = ClientModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
