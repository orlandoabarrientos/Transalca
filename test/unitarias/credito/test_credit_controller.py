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


@pytest.fixture
def auth_regular_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


class TestCreditController:
    """Pruebas de integración de rutas API para gestión de créditos."""

    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/credit/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    def test_get_all_regular_client_denied(self, auth_regular_client):
        response = auth_regular_client.get('/api/credit/')
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"

    @patch("model.credit_model.CreditModel._get_all")
    def test_get_all_employee_authorized_success(self, mock_get_all, auth_employee_client):
        mock_get_all.return_value = [
            {"id": 1, "cliente_cedula": "J-12345678-9", "credito_estado": "activo"}
        ]
        response = auth_employee_client.get('/api/credit/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.credit_model.CreditModel._get_stats")
    def test_get_stats_employee_success(self, mock_get_stats, auth_employee_client):
        mock_get_stats.return_value = {"total": 10, "pendientes": 4, "saldo": 1500.00}
        response = auth_employee_client.get('/api/credit/stats')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["total"] == 10

    @patch("model.credit_model.CreditModel._get_payments")
    def test_get_payments_employee_success(self, mock_get_payments, auth_employee_client):
        mock_get_payments.return_value = [
            {"id_pago_credito": 1, "monto_pago": 50.00, "fecha_pago": "2026-08-20"}
        ]
        response = auth_employee_client.get('/api/credit/1/payments')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.credit_model.CreditModel._update_status")
    def test_update_status_success(self, mock_update_status, auth_employee_client):
        mock_update_status.return_value = 1
        response = auth_employee_client.put('/api/credit/1/status', json={"estado": "activo"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.credit_model.CreditModel._mark_paid")
    def test_mark_paid_success(self, mock_mark_paid, auth_employee_client):
        mock_mark_paid.return_value = {"ok": True, "message": "Crédito pagado correctamente."}
        response = auth_employee_client.put('/api/credit/1/paid')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.credit_model.CreditModel._create_credit")
    def test_create_credit_success(self, mock_create_credit, auth_employee_client):
        mock_create_credit.return_value = {
            "ok": True,
            "id": 1,
            "message": "Crédito registrado correctamente."
        }
        response = auth_employee_client.post('/api/credit/', json={
            "cliente_cedula": "J-12345678-9",
            "total": 500.00,
            "fecha_inicio": "2026-08-20",
            "fecha_fin": "2026-09-20"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1
