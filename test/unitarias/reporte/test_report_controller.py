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
