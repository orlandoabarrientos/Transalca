import pytest
from unittest.mock import patch
from model.supplier_model import SupplierModel
from config.validation import ValidationError


class TestSupplierModelProperties:
    """Pruebas unitarias para getters y setters del modelo de proveedor."""

    def test_property_setters_strip_whitespace(self):
        model = SupplierModel()
        model.rif = "  J-123456789  "
        model.nombre = "  Distribuidora Automotriz C.A.  "
        model.telefono = "  04141234567  "
        model.email = "  contacto@distribuidora.com  "
        model.direccion = "  Av. Las Industrias  "

        assert model.rif == "J-123456789"
        assert model.nombre == "Distribuidora Automotriz C.A."
        assert model.telefono == "04141234567"
        assert model.email == "contacto@distribuidora.com"
        assert model.direccion == "Av. Las Industrias"

    def test_property_setters_none(self):
        model = SupplierModel()
        model.rif = None
        model.nombre = None

        assert model.rif is None
        assert model.nombre is None


class TestSupplierModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de proveedor."""

    # DATA PROVIDER: Pruebas con formatos de RIF válidos
    @pytest.mark.parametrize("input_rif, expected_rif, expected_prefijo", [
        ("J-123456789", "J-12345678-9", "J"),
        ("G-987654321", "G-98765432-1", "G"),
        ("V-123456789", "V-12345678-9", "V"),
        ("j 123456789", "J-12345678-9", "J"),
        ("J123456789", "J-12345678-9", "J"),
    ])
    def test_validate_valid_rif_data_provider(self, input_rif, expected_rif, expected_prefijo):
        model = SupplierModel()
        data = {
            "rif": input_rif,
            "nombre": "Proveedor Repuestos C.A.",
            "telefono": "04121234567",
            "email": "ventas@proveedor.com"
        }
        clean = model._validate(data)
        assert clean["rif"] == expected_rif
        assert clean["rif_prefijo"] == expected_prefijo

    # DATA PROVIDER: Pruebas con formatos de RIF inválidos
    @pytest.mark.parametrize("invalid_rif", [
        "XYZ-99999",
        "123",            # RIF muy corto
        "J-ABCDEFGHI",    # Caracteres no numéricos
        "",               # Vacío
    ])
    def test_validate_invalid_rif_data_provider(self, invalid_rif):
        model = SupplierModel()
        data = {
            "rif": invalid_rif,
            "nombre": "Proveedor Repuestos C.A.",
            "telefono": "04121234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "rif" in exc_info.value.errors

    # DATA PROVIDER: Pruebas de validación de nombre de proveedor
    @pytest.mark.parametrize("invalid_nombre", [
        "",         # Nombre vacío
        "AB",       # Nombre menor a 3 caracteres
    ])
    def test_validate_invalid_name_data_provider(self, invalid_nombre):
        model = SupplierModel()
        data = {
            "rif": "J-123456789",
            "nombre": invalid_nombre,
            "telefono": "04121234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "nombre" in exc_info.value.errors

    def test_validate_whitespace_only_direccion_fails(self):
        model = SupplierModel()
        data = {
            "rif": "J-123456789",
            "nombre": "Proveedor Repuestos C.A.",
            "direccion": "     "
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "direccion" in exc_info.value.errors


class TestSupplierModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones CRUD de proveedor."""

    @patch.object(SupplierModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"rif": "J-12345678-9", "nombre": "Proveedor Repuestos C.A.", "total_ordenes": 5}
        ]
        model = SupplierModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "Proveedor Repuestos C.A."
        mock_fetch_all.assert_called_once()

    @patch.object(SupplierModel, "fetch_one")
    def test_get_by_rif(self, mock_fetch_one):
        mock_fetch_one.return_value = {"rif": "J-12345678-9", "nombre": "Proveedor Repuestos C.A."}
        model = SupplierModel()
        result = model.ejecutar("get_by_rif", "J-12345678-9")

        assert result["rif"] == "J-12345678-9"
        mock_fetch_one.assert_called_once()

    @patch.object(SupplierModel, "_get_by_rif")
    def test_create_duplicate_active_supplier_raises_error(self, mock_get_by_rif):
        mock_get_by_rif.return_value = {"rif": "J-12345678-9", "estado": 1}

        model = SupplierModel()
        data = {
            "rif": "J-123456789",
            "nombre": "Proveedor Repuestos C.A.",
            "telefono": "04121234567"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", data)

        assert "rif" in exc_info.value.errors

    @patch.object(SupplierModel, "update")
    def test_soft_delete(self, mock_update):
        mock_update.return_value = 1
        model = SupplierModel()
        result = model.ejecutar("soft_delete", "J-12345678-9")

        assert result == 1
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = SupplierModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
