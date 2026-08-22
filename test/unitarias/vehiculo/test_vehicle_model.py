import pytest
from unittest.mock import patch, MagicMock
from model.vehicle_model import VehicleModel
from config.validation import ValidationError


class TestVehicleModelProperties:
    """Pruebas unitarias para getters y setters del modelo de vehículo."""

    def test_property_setters_strip_and_uppercase_plate(self):
        model = VehicleModel()
        model.placa = "  ab123cd  "
        model.marca = "  Toyota  "
        model.modelo = "  Corolla  "

        assert model.placa == "AB123CD"
        assert model.marca == "Toyota"
        assert model.modelo == "Corolla"

    def test_property_setters_none(self):
        model = VehicleModel()
        model.placa = None
        model.marca = None
        model.modelo = None

        assert model.placa == ""
        assert model.marca is None
        assert model.modelo is None


class TestVehicleModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de vehículo."""

    # DATA PROVIDER: Normalización de placas en mayúsculas sin espacios
    @pytest.mark.parametrize("raw_placa, expected_placa", [
        ("abc-1234", "ABC-1234"),
        ("  x789yy  ", "X789YY"),
        ("A12B34", "A12B34"),
    ])
    def test_plate_normalization_data_provider(self, raw_placa, expected_placa):
        model = VehicleModel()
        assert model._plate(raw_placa) == expected_placa

    # DATA PROVIDER: Datos válidos de vehículo
    @pytest.mark.parametrize("marca, modelo, anio, placa, combustible, km", [
        ("Toyota", "Yaris", 2022, "ABC-1234", "gasolina", 45000),
        ("Chevrolet", "Aveo", 2011, "X789YY", "gasoil", 120000),
        ("Ford", "Explorer", 2018, "AA123BB", "otro", 85000),
    ])
    def test_validate_valid_vehicle_data_provider(self, marca, modelo, anio, placa, combustible, km):
        model = VehicleModel()
        data = {
            "marca": marca,
            "modelo": modelo,
            "anio": anio,
            "placa": placa,
            "tipo_combustible": combustible,
            "kilometraje_actual": km
        }
        clean = model._validate(data)
        assert clean["marca"] == marca
        assert clean["modelo"] == modelo
        assert clean["placa"] == placa.upper()
        assert clean["tipo_combustible"] == combustible

    # DATA PROVIDER: Placas con formato inválido
    @pytest.mark.parametrize("invalid_placa", [
        "AB*12",         # Caracter especial no permitido
        "123",           # Menor a 5 caracteres
        "PLACA CON ESPACIOS", # Espacios en blanco
    ])
    def test_validate_invalid_plate_data_provider(self, invalid_placa):
        model = VehicleModel()
        data = {
            "marca": "Toyota",
            "modelo": "Corolla",
            "placa": invalid_placa
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "placa" in exc_info.value.errors


class TestVehicleModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para gestión de vehículos."""

    @patch.object(VehicleModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": "ABC-1234", "placa": "ABC-1234", "marca": "Toyota", "modelo": "Corolla"}
        ]
        model = VehicleModel()
        vehicles = model.ejecutar("get_all")

        assert len(vehicles) == 1
        assert vehicles[0]["placa"] == "ABC-1234"
        mock_fetch_all.assert_called_once()

    @patch.object(VehicleModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": "ABC-1234", "placa": "ABC-1234", "marca": "Toyota"}
        model = VehicleModel()
        v = model.ejecutar("get_by_id", "abc-1234")

        assert v["placa"] == "ABC-1234"
        mock_fetch_one.assert_called_once()

    @patch.object(VehicleModel, "insert")
    @patch.object(VehicleModel, "update")
    @patch.object(VehicleModel, "fetch_one")
    def test_update_kilometraje_success(self, mock_fetch_one, mock_update, mock_insert):
        mock_fetch_one.return_value = {"placa_vehiculo": "ABC-1234", "kilometraje_actual": 50000}
        mock_update.return_value = 1
        mock_insert.return_value = 1

        model = VehicleModel()
        result = model.ejecutar("update_kilometraje", "ABC-1234", 55000)

        assert result is True
        mock_update.assert_called_once()

    @patch.object(VehicleModel, "fetch_one")
    def test_update_kilometraje_lower_than_current_fails(self, mock_fetch_one):
        mock_fetch_one.return_value = {"placa_vehiculo": "ABC-1234", "kilometraje_actual": 50000}

        model = VehicleModel()
        result = model.ejecutar("update_kilometraje", "ABC-1234", 40000)

        assert result is False

    @patch.object(VehicleModel, "update")
    def test_soft_delete(self, mock_update):
        mock_update.return_value = 1
        model = VehicleModel()
        result = model.ejecutar("soft_delete", "ABC-1234")

        assert result == 1
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = VehicleModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
