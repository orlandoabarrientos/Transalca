import pytest
from unittest.mock import patch
from model.tasa_cambio_model import TasaCambioModel
from config.validation import ValidationError


class TestTasaCambioModelProperties:
    """Pruebas unitarias para getters y setters del modelo de tasa de cambio."""

    def test_property_setters_strip_and_convert(self):
        model = TasaCambioModel()
        model.fecha = "  2026-08-22  "
        model.monto = "36.50"
        model.fuente = "  BCV Oficial  "

        assert model.fecha == "2026-08-22"
        assert model.monto == 36.50
        assert model.fuente == "BCV Oficial"

    def test_property_setters_none(self):
        model = TasaCambioModel()
        model.fecha = None
        model.fuente = None

        assert model.fecha is None
        assert model.fuente is None


class TestTasaCambioModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de tasa de cambio."""

    # DATA PROVIDER: Pruebas con datos válidos de tasa de cambio
    @pytest.mark.parametrize("monto_valido, fecha_valida, fuente_valida", [
        (36.50, "2026-08-22", "BCV Oficial"),
        ("40.00", "2026-01-01", "Paralelo"),
        (1, "2026-12-31", "Banco Central"),
    ])
    def test_validate_valid_tasa_data_provider(self, monto_valido, fecha_valida, fuente_valida):
        model = TasaCambioModel()
        data = {
            "monto": monto_valido,
            "fecha": fecha_valida,
            "fuente": fuente_valida
        }
        clean = model._validate(data, require_fecha=True)
        assert clean["monto"] == float(monto_valido)
        assert clean["fecha"] == fecha_valida
        assert clean["fuente"] == fuente_valida.strip()

    # DATA PROVIDER: Pruebas con montos inválidos
    @pytest.mark.parametrize("invalid_monto", [
        0,              # Cero
        -5.5,           # Negativo
        "no_numerico",  # Texto
    ])
    def test_validate_invalid_monto_data_provider(self, invalid_monto):
        model = TasaCambioModel()
        data = {
            "monto": invalid_monto,
            "fecha": "2026-08-22",
            "fuente": "BCV"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data, require_fecha=True)
        assert "monto" in exc_info.value.errors

    # DATA PROVIDER: Pruebas con fechas inválidas
    @pytest.mark.parametrize("invalid_fecha", [
        "22-08-2026",      # DD-MM-YYYY
        "2026/08/22",      # Con slashes
        "fecha_invalida",  # Texto
        "",                # Vacía cuando es requerida
    ])
    def test_validate_invalid_fecha_data_provider(self, invalid_fecha):
        model = TasaCambioModel()
        data = {
            "monto": 36.5,
            "fecha": invalid_fecha,
            "fuente": "BCV"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data, require_fecha=True)
        assert "fecha" in exc_info.value.errors


class TestTasaCambioModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de tasa de cambio."""

    @patch.object(TasaCambioModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "monto": 36.5, "fecha": "2026-08-22", "tipo": "bcv"}
        ]
        model = TasaCambioModel()
        result = model.ejecutar("get_all", 10)

        assert len(result) == 1
        assert result[0]["monto"] == 36.5
        mock_fetch_all.assert_called_once()

    @patch.object(TasaCambioModel, "fetch_one")
    def test_get_latest(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 5, "monto": 37.10, "fecha": "2026-08-22"}
        model = TasaCambioModel()
        result = model.ejecutar("get_latest")

        assert result["id"] == 5
        assert result["monto"] == 37.10
        mock_fetch_one.assert_called_once()

    @patch.object(TasaCambioModel, "insert")
    def test_create_tasa(self, mock_insert):
        mock_insert.return_value = 10
        model = TasaCambioModel()
        data = {
            "monto": 36.80,
            "fecha": "2026-08-22",
            "fuente": "BCV Manual"
        }
        result = model.ejecutar("create", data)

        assert result == 10
        mock_insert.assert_called_once()

    @patch.object(TasaCambioModel, "delete")
    def test_delete_tasa(self, mock_delete):
        mock_delete.return_value = 1
        model = TasaCambioModel()
        result = model.ejecutar("delete_tasa", 1)

        assert result == 1
        mock_delete.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = TasaCambioModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
