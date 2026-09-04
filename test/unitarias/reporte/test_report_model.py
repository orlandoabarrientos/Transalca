import pytest
from unittest.mock import patch
from model.report_model import ReportModel


class TestReportModelClientName:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para la resolución de nombres de clientes en reportes."""

    # DATA PROVIDER: Formateo de nombre de cliente según tipo persona
    @pytest.mark.parametrize("client_row, expected_name", [
        ({"tipo_cliente": "juridica", "razon_social": "Inversiones Transalca C.A.", "nombre": "Inversiones"}, "Inversiones Transalca C.A."),
        ({"tipo_cliente": "juridica", "razon_social": "", "nombre": "Empresa Demo"}, "Empresa Demo"),
        ({"tipo_cliente": "natural", "nombre": "Juan", "apellido": "Pérez"}, "Juan Pérez"),
        (None, "N/A"),
    ])
    @patch.object(ReportModel, "fetch_one")
    def test_client_name_data_provider(self, mock_fetch_one, client_row, expected_name):
        mock_fetch_one.return_value = client_row
        model = ReportModel()

        result = model._client_name("V-12345678")
        assert result == expected_name


class TestReportModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para generación de reportes e indicadores."""

    @patch.object(ReportModel, "fetch_one")
    def test_get_dashboard_stats(self, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"total": 50},   # productos
            {"total": 8},    # categorias
            {"total": 120},  # clientes
            {"total": 15},   # empleados
            {"total": 3},    # pagos pendientes
            {"total": 4500.50}, # ventas totales
            {"total": 35},   # ordenes
            {"total": 4},    # bajo stock
            {"total": 2},    # promos activas
        ]
        model = ReportModel()
        stats = model.ejecutar("get_dashboard_stats")

        assert stats["total_products"] == 50
        assert stats["total_clients"] == 120
        assert stats["total_sales"] == 4500.50

    @patch.object(ReportModel, "_client_name", return_value="Carlos Mendoza")
    @patch.object(ReportModel, "fetch_all")
    def test_get_recent_orders(self, mock_fetch_all, mock_client_name):
        mock_fetch_all.return_value = [
            {"id": 10, "cliente_cedula": "V-12345678", "total": 150.00, "fecha": "2026-08-22"}
        ]
        model = ReportModel()
        orders = model.ejecutar("get_recent_orders", 5)

        assert len(orders) == 1
        assert orders[0]["cliente_nombre"] == "Carlos Mendoza"

    @patch.object(ReportModel, "fetch_all")
    def test_get_sales_history(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "tipo_cliente": "natural", "nombre": "Pedro", "apellido": "Gómez", "total": 200.00, "estado": "aprobada", "fecha": "2026-08-20"}
        ]
        model = ReportModel()
        sales = model.ejecutar("get_sales_history", "2026-08-01", "2026-08-31", "aprobada")

        assert len(sales) == 1
        assert sales[0]["cliente"] == "Pedro Gómez"

    @patch.object(ReportModel, "fetch_all")
    def test_get_mechanics_performance(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"mecanico_cedula": "V-11111111", "mecanico_nombre": "José Pérez", "asignacion_estado": "completado", "subtotal": 50.00},
            {"mecanico_cedula": "V-11111111", "mecanico_nombre": "José Pérez", "asignacion_estado": "asignado", "subtotal": 30.00},
        ]
        model = ReportModel()
        perf = model.ejecutar("get_mechanics_performance")

        assert len(perf) == 1
        assert perf[0]["mecanico_nombre"] == "José Pérez"
        assert perf[0]["total_asignados"] == 2
        assert perf[0]["total_completados"] == 1
        assert perf[0]["ingreso_generado"] == 50.00

    @patch.object(ReportModel, "fetch_all")
    def test_get_top_products_report(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {
                "codigo": "ACE-10W40",
                "nombre_producto": "Aceite Semi-Sintético 10W40",
                "categoria": "Aceites",
                "marca": "Castrol",
                "precio_actual": 12.50,
                "total_vendido": 150,
                "total_recaudado": 1875.00,
                "total_ordenes": 30,
                "stock_actual": 45
            }
        ]
        model = ReportModel()
        report = model.ejecutar("get_top_products_report", start_date="2026-08-01", end_date="2026-08-31", category="Aceites", limit=5)

        assert len(report) == 1
        assert report[0]["ranking"] == 1
        assert report[0]["codigo"] == "ACE-10W40"
        assert report[0]["total_vendido"] == 150
        assert report[0]["total_recaudado"] == 1875.00

    @patch.object(ReportModel, "fetch_all")
    def test_get_top_products_report_with_filters(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {
                "codigo": "ACE-10W40",
                "nombre_producto": "Aceite Semi-Sintético 10W40",
                "categoria": "Aceites",
                "marca": "Castrol",
                "precio_actual": 12.50,
                "total_vendido": 150,
                "total_recaudado": 1875.00,
                "total_ordenes": 30,
                "stock_actual": 45
            }
        ]
        model = ReportModel()
        report = model.ejecutar(
            "get_top_products_report",
            start_date="2026-08-01",
            end_date="2026-08-31",
            category="Aceites",
            brand="Castrol",
            status="aprobada",
            limit=5,
            search="Aceite",
            stock_status="in_stock",
            order_by="revenue",
            sucursal_id=1
        )

        assert len(report) == 1
        assert report[0]["ranking"] == 1
        assert report[0]["codigo"] == "ACE-10W40"
        assert report[0]["total_vendido"] == 150
        assert report[0]["total_recaudado"] == 1875.00

    @patch.object(ReportModel, "fetch_all")
    def test_get_sales_history_with_client_type(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "tipo_cliente": "juridica", "nombre": "Inversiones", "razon_social": "Inversiones C.A.", "total": 500.00, "estado": "aprobada", "fecha": "2026-08-20"}
        ]
        model = ReportModel()
        sales = model.ejecutar("get_sales_history", client_type="juridica", min_amount=100.0, max_amount=1000.0, search="Inversiones")

        assert len(sales) == 1
        assert sales[0]["cliente"] == "Inversiones C.A."
        assert sales[0]["total"] == 500.00

    def test_ejecutar_invalid_action(self):
        model = ReportModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)


