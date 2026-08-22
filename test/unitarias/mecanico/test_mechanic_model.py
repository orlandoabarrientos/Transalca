import pytest
from unittest.mock import patch
from model.mechanic_model import MechanicModel
from config.validation import ValidationError


class TestMechanicModelProperties:
    """Pruebas unitarias para getters y setters del modelo de mecánico."""

    def test_property_setters_strip_whitespace(self):
        model = MechanicModel()
        model.cedula = "  V-12345678  "
        model.nombre = "  Carlos  "
        model.apellido = "  Pérez  "
        model.telefono = "  04141234567  "
        model.especialidad = "  Motor y Frenos  "

        assert model.cedula == "V-12345678"
        assert model.nombre == "Carlos"
        assert model.apellido == "Pérez"
        assert model.telefono == "04141234567"
        assert model.especialidad == "Motor y Frenos"

    def test_property_setters_none(self):
        model = MechanicModel()
        model.cedula = None
        model.nombre = None

        assert model.cedula is None
        assert model.nombre is None


class TestMechanicModelValidation:
    """Pruebas unitarias utilizando Data Provider (@pytest.mark.parametrize) para validaciones."""

    # DATA PROVIDER: Probar múltiples formatos de cédulas válidas con sus resultados esperados
    @pytest.mark.parametrize("input_cedula, expected_cedula, expected_prefijo", [
        ("V-12345678", "V-12345678", "V"),
        ("E-87654321", "E-87654321", "E"),
        ("J-12345678", "J-12345678", "J"),
        ("v 12345678", "V-12345678", "V"),
        ("V12345678", "V-12345678", "V"),
    ])
    def test_validate_valid_cedula_data_provider(self, input_cedula, expected_cedula, expected_prefijo):
        model = MechanicModel()
        data = {
            "cedula": input_cedula,
            "nombre": "Carlos",
            "apellido": "Pérez"
        }
        clean = model.ejecutar("validate", data)
        assert clean["cedula"] == expected_cedula
        assert clean["cedula_prefijo"] == expected_prefijo

    # DATA PROVIDER: Probar múltiples formatos de cédulas inválidas
    @pytest.mark.parametrize("invalid_cedula", [
        "XYZ-99999",
        "ABC",
        "123",  # Cédula demasiado corta
        "V-ABCDEFGH",  # Caracteres no numéricos en número
        "",  # Cédula vacía
    ])
    def test_validate_invalid_cedula_data_provider(self, invalid_cedula):
        model = MechanicModel()
        data = {
            "cedula": invalid_cedula,
            "nombre": "Carlos",
            "apellido": "Pérez"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("validate", data)
        assert "cedula" in exc_info.value.errors

    # DATA PROVIDER: Probar nombres y apellidos inválidos
    @pytest.mark.parametrize("nombre, apellido, expected_error_field", [
        ("", "Pérez", "nombre"),
        ("A", "Pérez", "nombre"),  # Nombre muy corto
        ("Carlos123", "Pérez", "nombre"),  # Caracteres numéricos
        ("Carlos", "", "apellido"),
        ("Carlos", "P", "apellido"),  # Apellido muy corto
    ])
    def test_validate_invalid_names_data_provider(self, nombre, apellido, expected_error_field):
        model = MechanicModel()
        data = {
            "cedula": "V-12345678",
            "nombre": nombre,
            "apellido": apellido
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("validate", data)
        assert expected_error_field in exc_info.value.errors


class TestMechanicModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones CRUD."""

    @patch.object(MechanicModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"cedula": "V-12345678", "nombre": "Carlos", "apellido": "Pérez", "estado_operativo": "Disponible"}
        ]
        model = MechanicModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "Carlos"
        mock_fetch_all.assert_called_once()

    @patch.object(MechanicModel, "fetch_one")
    def test_get_by_cedula(self, mock_fetch_one):
        mock_fetch_one.return_value = {"cedula": "V-12345678", "nombre": "Carlos"}
        model = MechanicModel()
        result = model.ejecutar("get_by_cedula", "V-12345678")

        assert result["cedula"] == "V-12345678"
        mock_fetch_one.assert_called_once()

    @patch.object(MechanicModel, "insert")
    @patch.object(MechanicModel, "_get_by_cedula")
    def test_create_new_mechanic(self, mock_get_by_cedula, mock_insert):
        mock_get_by_cedula.return_value = None
        mock_insert.return_value = 1

        model = MechanicModel()
        data = {
            "cedula": "V-87654321",
            "nombre": "Pedro",
            "apellido": "Ramírez",
            "telefono": "04149876543",
            "especialidad": "Transmisiones"
        }
        cedula = model.ejecutar("create", data)

        assert cedula == "V-87654321"
        mock_insert.assert_called_once()

    @patch.object(MechanicModel, "_get_by_cedula")
    def test_create_duplicate_active_mechanic_raises_error(self, mock_get_by_cedula):
        mock_get_by_cedula.return_value = {"cedula": "V-12345678", "estado": 1}

        model = MechanicModel()
        data = {
            "cedula": "V-12345678",
            "nombre": "Pedro",
            "apellido": "Ramírez"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", data)

        assert "cedula" in exc_info.value.errors

    @patch.object(MechanicModel, "update")
    def test_soft_delete(self, mock_update):
        mock_update.return_value = 1
        model = MechanicModel()
        result = model.ejecutar("soft_delete", "V-12345678")

        assert result == 1
        mock_update.assert_called_once()

    @patch.object(MechanicModel, "update")
    @patch.object(MechanicModel, "_get_by_cedula")
    def test_toggle_estado(self, mock_get_by_cedula, mock_update):
        mock_get_by_cedula.return_value = {"cedula": "V-12345678", "estado": 1}
        mock_update.return_value = 1

        model = MechanicModel()
        new_status = model.ejecutar("toggle_estado", "V-12345678")

        assert new_status == 0

    def test_ejecutar_invalid_action(self):
        model = MechanicModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")
        
        assert "Accion no permitida" in str(exc_info.value)
