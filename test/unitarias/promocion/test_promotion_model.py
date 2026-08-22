import pytest
from unittest.mock import patch
from model.promotion_model import PromotionModel
from config.validation import ValidationError


class TestPromotionModelProperties:
    """Pruebas unitarias para getters y setters del modelo de promoción."""

    def test_property_setters_strip_whitespace(self):
        model = PromotionModel()
        model.nombre = "  Promo 5to Cambio Gratis  "
        model.descripcion = "  Acumula 5 cambios de aceite y recibe 1 gratis  "
        model.recompensa = "  1 Cambio de Aceite Gratis  "
        model.fecha_inicio = "  2026-01-01  "
        model.fecha_fin = "  2026-12-31  "

        assert model.nombre == "Promo 5to Cambio Gratis"
        assert model.descripcion == "Acumula 5 cambios de aceite y recibe 1 gratis"
        assert model.recompensa == "1 Cambio de Aceite Gratis"
        assert model.fecha_inicio == "2026-01-01"
        assert model.fecha_fin == "2026-12-31"

    def test_property_setters_none(self):
        model = PromotionModel()
        model.nombre = None
        model.descripcion = None
        model.recompensa = None
        model.fecha_inicio = None
        model.fecha_fin = None

        assert model.nombre is None
        assert model.descripcion is None
        assert model.recompensa is None
        assert model.fecha_inicio is None
        assert model.fecha_fin is None


class TestPromotionModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de promoción."""

    # DATA PROVIDER: Pruebas con tipos de promoción válidos
    @pytest.mark.parametrize("tipo_valido", [
        "puntos",
        "descuento",
        "gratis",
        "porcentaje",
        "monto_fijo",
        "2x1",
        "puntos_extra",
    ])
    def test_validate_valid_tipos_data_provider(self, tipo_valido):
        model = PromotionModel()
        data = {
            "nombre": "Promoción Especial",
            "descripcion": "Descripción detallada",
            "tipo": tipo_valido,
            "puntos_requeridos": 5,
            "fecha_inicio": "2026-01-01",
            "fecha_fin": "2026-12-31"
        }
        clean = model._validate(data)
        assert clean["tipo"] == tipo_valido
        assert clean["puntos_requeridos"] == 5

    # DATA PROVIDER: Pruebas de formato de fecha YYYY-MM-DD
    @pytest.mark.parametrize("invalid_fecha, expected_field", [
        ("01-01-2026", "fecha_inicio"),     # Formato DD-MM-YYYY
        ("2026/01/01", "fecha_inicio"),     # Con / en vez de -
        ("fecha_invalida", "fecha_inicio"),  # Texto no fecha
    ])
    def test_validate_invalid_date_format_data_provider(self, invalid_fecha, expected_field):
        model = PromotionModel()
        data = {
            "nombre": "Promoción Especial",
            "tipo": "puntos",
            "fecha_inicio": invalid_fecha
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert expected_field in exc_info.value.errors

    def test_validate_end_date_before_start_date_fails(self):
        model = PromotionModel()
        data = {
            "nombre": "Promoción Especial",
            "tipo": "puntos",
            "fecha_inicio": "2026-12-31",
            "fecha_fin": "2026-01-01"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "fecha_fin" in exc_info.value.errors


class TestPromotionModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de promoción y tarjetas de fidelidad."""

    @patch.object(PromotionModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "5to Cambio Gratis", "tipo": "puntos", "fecha_inicio": None, "fecha_fin": None}
        ]
        model = PromotionModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "5to Cambio Gratis"
        mock_fetch_all.assert_called_once()

    @patch.object(PromotionModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {
            "id": 1,
            "nombre": "5to Cambio Gratis",
            "fecha_inicio": None,
            "fecha_fin": None
        }
        model = PromotionModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()

    @patch.object(PromotionModel, "insert")
    @patch.object(PromotionModel, "update")
    @patch.object(PromotionModel, "fetch_one")
    def test_add_point_to_card(self, mock_fetch_one, mock_update, mock_insert):
        mock_fetch_one.return_value = {
            "id": 10,
            "puntos_acumulados": 2,
            "puntos_requeridos": 3,
            "canjeada": 0
        }
        mock_update.return_value = 1
        mock_insert.return_value = 100

        model = PromotionModel()
        result = model.ejecutar("add_point", 10, "Punto por cambio de aceite")

        assert result["puntos_acumulados"] == 3
        assert result["canjeada"] == 1
        mock_update.assert_called_once()
        mock_insert.assert_called_once()

    @patch.object(PromotionModel, "update")
    @patch.object(PromotionModel, "_get_by_id")
    def test_soft_delete(self, mock_get_by_id, mock_update):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Promo Test"}
        mock_update.return_value = 1

        model = PromotionModel()
        result = model.ejecutar("soft_delete", 1)

        assert result == 0
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = PromotionModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
