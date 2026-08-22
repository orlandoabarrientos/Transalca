import pytest
from unittest.mock import patch
from datetime import datetime
from model.stats_model import StatsModel


class TestStatsModelQueries:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para generación de gráficas y estadísticas."""

    # DATA PROVIDER: Pruebas de línea de tiempo de ingresos según días consultados
    @pytest.mark.parametrize("days_param", [7, 30, 90])
    @patch.object(StatsModel, "fetch_all")
    def test_get_revenue_timeline_data_provider(self, mock_fetch_all, days_param):
        mock_fetch_all.return_value = [
            {"fecha_corta": datetime(2026, 8, 20), "total": 1500.00},
            {"fecha_corta": datetime(2026, 8, 21), "total": 2300.50},
        ]
        model = StatsModel()

        result = model._get_revenue_timeline(days=days_param)

        assert len(result["labels"]) == 2
        assert result["labels"][0] == "2026-08-20"
        assert result["data"][0] == 1500.00
        mock_fetch_all.assert_called_once()

    # DATA PROVIDER: Pruebas de productos más vendidos según límite de resultados
    @pytest.mark.parametrize("limit_param", [3, 5, 10])
    @patch.object(StatsModel, "fetch_all")
    def test_get_top_performing_products_data_provider(self, mock_fetch_all, limit_param):
        mock_fetch_all.return_value = [
            {"nombre": "Aceite 20W50 Mineral Sella", "total_vendido": 45},
            {"nombre": "Filtro Aceite PH3593A", "total_vendido": 30},
        ]
        model = StatsModel()

        result = model._get_top_performing_products(limit=limit_param)

        assert len(result["labels"]) == 2
        assert result["labels"][0] == "Aceite 20W50 Mi" # Recortado a 15 caracteres
        assert result["data"][0] == 45


class TestStatsModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para distribuciones estadísticas de servicios y pagos."""

    @patch.object(StatsModel, "fetch_all")
    def test_get_order_status_distribution(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"estado": "aprobada", "cantidad": 15},
            {"estado": "pendiente", "cantidad": 5},
        ]
        model = StatsModel()
        result = model.ejecutar("get_order_status_distribution")

        assert result["labels"] == ["Aprobada", "Pendiente"]
        assert result["data"] == [15, 5]

    @patch.object(StatsModel, "fetch_all")
    def test_get_payments_distribution(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"metodo": "Pago Móvil", "cantidad": 25},
            {"metodo": "Zelle", "cantidad": 10},
        ]
        model = StatsModel()
        result = model.ejecutar("get_payments_distribution")

        assert result["labels"] == ["Pago móvil", "Zelle"]
        assert result["data"] == [25, 10]

    @patch.object(StatsModel, "fetch_all")
    def test_get_top_services(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"nombre": "Cambio de Aceite de Motor", "total_solicitados": 40, "ingreso": 600.00}
        ]
        model = StatsModel()
        result = model.ejecutar("get_top_services", 5)

        assert result["labels"][0] == "Cambio de Aceite de "
        assert result["data"][0] == 40
        assert result["ingresos"][0] == 600.00

    def test_ejecutar_invalid_action(self):
        model = StatsModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
