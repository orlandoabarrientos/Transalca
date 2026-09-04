import pytest
from unittest.mock import patch
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def auth_employee_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_cedula'] = 'V-10000000'
        sess['user_tipo'] = 'admin'
    return client


class TestReportController:
    """Pruebas de integración de rutas API para consulta y exportación de reportes."""

    @patch("model.report_model.ReportModel._get_dashboard_stats")
    def test_dashboard_stats_success(self, mock_get_stats, auth_employee_client):
        mock_get_stats.return_value = {"total_products": 50, "total_sales": 4500.50}
        response = auth_employee_client.get('/api/reports/dashboard')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["total_products"] == 50

    @patch("model.report_model.ReportModel._get_recent_orders")
    def test_recent_orders_success(self, mock_get_recent, auth_employee_client):
        mock_get_recent.return_value = [{"id": 1, "total": 100.00}]
        response = auth_employee_client.get('/api/reports/recent-orders?limit=5')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    def test_query_unauthorized_fails(self, client):
        response = client.get('/api/reports/query?type=sales')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.report_model.ReportModel._get_sales_history")
    def test_query_sales_authorized_success(self, mock_get_sales, auth_employee_client):
        mock_get_sales.return_value = [{"id": 1, "total": 200.00, "estado": "aprobada"}]
        response = auth_employee_client.get('/api/reports/query?type=sales')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    def test_query_invalid_type_fails(self, auth_employee_client):
        response = auth_employee_client.get('/api/reports/query?type=invalido')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    @patch("model.report_model.ReportModel._get_sales_history")
    def test_export_csv_success(self, mock_get_sales, auth_employee_client):
        mock_get_sales.return_value = [
            {"id": 1, "cliente": "Juan Pérez", "fecha": "2026-08-22", "total": 150.00, "estado": "aprobada"}
        ]
        response = auth_employee_client.get('/api/reports/export?type=sales&format=csv')

        assert response.status_code == 200
        assert response.mimetype == "text/csv"
        assert b"Juan P" in response.data

    @patch("model.report_model.ReportModel._get_top_products_report")
    def test_query_top_products_authorized_success(self, mock_get_top, auth_employee_client):
        mock_get_top.return_value = [
            {"ranking": 1, "codigo": "FIL-001", "nombre_producto": "Filtro de Aceite", "total_vendido": 80, "total_recaudado": 640.00}
        ]
        response = auth_employee_client.get('/api/reports/query?type=top_products&category=Filtros&limit=10&sucursal_id=1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"][0]["codigo"] == "FIL-001"
        assert json_data["data"][0]["total_vendido"] == 80
        mock_get_top.assert_called_once()
        assert mock_get_top.call_args.kwargs.get('sucursal_id') == '1'

    @patch("model.report_model.ReportModel._get_top_products_report")
    def test_export_top_products_excel_success(self, mock_get_top, auth_employee_client):
        mock_get_top.return_value = [
            {
                "ranking": 1,
                "codigo": "FIL-001",
                "nombre_producto": "Filtro de Aceite",
                "categoria": "Filtros",
                "marca": "Wix",
                "total_vendido": 80,
                "total_recaudado": 640.00,
                "total_ordenes": 25,
                "stock_actual": 12
            }
        ]
        response = auth_employee_client.get('/api/reports/export?type=top_products&format=excel')

        assert response.status_code == 200
        assert response.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(response.data) > 0

    @patch("model.report_model.ReportModel._get_top_products_report")
    def test_export_top_products_pdf_success(self, mock_get_top, auth_employee_client):
        mock_get_top.return_value = [
            {
                "ranking": 1,
                "codigo": "LUB-000032",
                "nombre_producto": "10W30 SEMI SINTETICO MOBIL ULTRA HIGH PERFORMANCE MOTOR OIL",
                "categoria": "Lubricantes",
                "marca": "MOBIL",
                "total_vendido": 80,
                "total_recaudado": 640.00,
                "total_ordenes": 25,
                "stock_actual": 12
            }
        ]
        response = auth_employee_client.get('/api/reports/export?type=top_products&format=pdf')

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert len(response.data) > 0

    @patch("model.report_model.ReportModel._get_inventory_kardex")
    def test_export_inventory_pdf_success(self, mock_get_inv, auth_employee_client):
        mock_get_inv.return_value = [
            {
                "id": 1,
                "producto": "Aceite Sintetico 10W30 Mobil Delvac Legend Extra",
                "codigo": "LUB-001",
                "categoria": "Lubricantes",
                "marca": "Mobil",
                "motivo": "Venta en tienda orden #12",
                "tipo": "salida",
                "cantidad": 5,
                "fecha": "2026-09-03 10:00:00"
            }
        ]
        response = auth_employee_client.get('/api/reports/export?type=inventory&format=pdf')

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert len(response.data) > 0

    @patch("model.report_model.ReportModel._get_bitacora_audit")
    def test_export_bitacora_pdf_success(self, mock_get_bitacora, auth_employee_client):
        mock_get_bitacora.return_value = [
            {
                "id": 1,
                "fecha": "2026-09-03 12:00:00",
                "usuario": "admin",
                "modulo": "PRODUCTOS",
                "accion": "CREAR",
                "descripcion": "Creación de producto LUB-001 con stock inicial 100",
                "ip": "127.0.0.1"
            }
        ]
        response = auth_employee_client.get('/api/reports/export?type=bitacora&format=pdf')

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert len(response.data) > 0

