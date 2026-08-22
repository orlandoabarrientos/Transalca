import pytest
from unittest.mock import MagicMock, patch
from model.company_model import CompanyModel
from config.validation import ValidationError


class TestCompanyModelProperties:
    """Pruebas unitarias para getters y setters del modelo de empresa."""

    def test_property_setters_strip_whitespace(self):
        model = CompanyModel()
        model.rif = "  J-123456789  "
        model.razon_social = "  Corporación Transalca C.A.  "
        model.telefono = "  02511234567  "
        model.email = "  contacto@transalca.com  "
        model.direccion = "  Zona Industrial II  "
        model.limite_credito = 5000.50
        model.dias_credito = 30

        assert model.rif == "J-123456789"
        assert model.razon_social == "Corporación Transalca C.A."
        assert model.telefono == "02511234567"
        assert model.email == "contacto@transalca.com"
        assert model.direccion == "Zona Industrial II"
        assert model.limite_credito == 5000.50
        assert model.dias_credito == 30

    def test_property_setters_none(self):
        model = CompanyModel()
        model.rif = None
        model.razon_social = None
        model.limite_credito = None
        model.dias_credito = None

        assert model.rif is None
        assert model.razon_social is None
        assert model.limite_credito == 0.0
        assert model.dias_credito == 0


class TestCompanyModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de empresa."""

    # DATA PROVIDER: Pruebas con formatos de RIF válidos
    @pytest.mark.parametrize("input_rif, expected_rif, expected_prefijo", [
        ("J-123456789", "J-12345678-9", "J"),
        ("G-987654321", "G-98765432-1", "G"),
        ("V-123456789", "V-12345678-9", "V"),
        ("j 123456789", "J-12345678-9", "J"),
        ("J123456789", "J-12345678-9", "J"),
    ])
    def test_validate_valid_rif_data_provider(self, input_rif, expected_rif, expected_prefijo):
        model = CompanyModel()
        data = {
            "rif": input_rif,
            "razon_social": "Inversiones Demo C.A.",
            "telefono": "04121234567",
            "email": "demo@empresa.com",
            "limite_credito": 1000,
            "dias_credito": 15
        }
        clean = model._validate(data, require_rif=True)
        assert clean["rif"] == expected_rif
        assert clean["rif_prefijo"] == expected_prefijo

    # DATA PROVIDER: Pruebas con formatos de RIF inválidos
    @pytest.mark.parametrize("invalid_rif", [
        "XYZ-12345",
        "123",             # RIF demasiado corto
        "J-ABCDEFGHI",     # Caracteres alfabéticos en número
        "",                # Vacío
    ])
    def test_validate_invalid_rif_data_provider(self, invalid_rif):
        model = CompanyModel()
        data = {
            "rif": invalid_rif,
            "razon_social": "Inversiones Demo C.A.",
            "telefono": "04121234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data, require_rif=True)
        assert "rif" in exc_info.value.errors

    # DATA PROVIDER: Validaciones de límite y días de crédito inválidos
    @pytest.mark.parametrize("limite_credito, dias_credito, expected_error_field", [
        (-500, 15, "limite_credito"),     # Límite negativo
        (1000, -10, "dias_credito"),      # Días de crédito negativos
        (1000, 400, "dias_credito"),      # Días de crédito mayores a 365
    ])
    def test_validate_credit_fields_data_provider(self, limite_credito, dias_credito, expected_error_field):
        model = CompanyModel()
        data = {
            "rif": "J-123456789",
            "razon_social": "Inversiones Demo C.A.",
            "telefono": "04121234567",
            "limite_credito": limite_credito,
            "dias_credito": dias_credito
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data, require_rif=True)
        assert expected_error_field in exc_info.value.errors


class TestCompanyModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones CRUD de empresa."""

    @patch.object(CompanyModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"rif": "J-123456789", "razon_social": "Transalca C.A.", "estado": 1}
        ]
        model = CompanyModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["rif"] == "J-123456789"
        mock_fetch_all.assert_called_once()

    @patch.object(CompanyModel, "fetch_one")
    def test_get_by_rif(self, mock_fetch_one):
        mock_fetch_one.return_value = {"rif": "J-123456789", "razon_social": "Transalca C.A."}
        model = CompanyModel()
        result = model.ejecutar("get_by_rif", "J-123456789")

        assert result["rif"] == "J-123456789"
        mock_fetch_one.assert_called_once()

    @patch.object(CompanyModel, "_get_by_rif")
    def test_create_duplicate_active_company_raises_error(self, mock_get_by_rif):
        mock_get_by_rif.return_value = {"rif": "J-123456789", "estado": 1}

        model = CompanyModel()
        data = {
            "rif": "J-123456789",
            "razon_social": "Transalca C.A.",
            "telefono": "04121234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", data)

        assert "rif" in exc_info.value.errors

    @patch.object(CompanyModel, "update")
    def test_soft_delete(self, mock_update):
        mock_update.return_value = 1
        model = CompanyModel()
        result = model.ejecutar("soft_delete", "J-123456789")

        assert result == 1
        mock_update.assert_called_once()

    @patch.object(CompanyModel, "fetch_one")
    def test_get_stats(self, mock_fetch_one):
        mock_fetch_one.side_effect = [{"total": 12}, {"total": 10}]
        model = CompanyModel()
        stats = model.ejecutar("get_stats")

        assert stats["total"] == 12
        assert stats["activos"] == 10

    def test_ejecutar_invalid_action(self):
        model = CompanyModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
