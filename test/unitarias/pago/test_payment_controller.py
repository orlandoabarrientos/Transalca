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


class TestPaymentController:
    """Pruebas de integración de rutas API para verificación de comprobantes de pago."""

    @patch("model.payment_model.PaymentModel._get_pending")
    def test_get_pending_payments(self, mock_get_pending, auth_employee_client):
        mock_get_pending.return_value = [
            {"id": 1, "orden_venta_id": 10, "estado": "pendiente"}
        ]
        response = auth_employee_client.get('/api/payments/pending')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.payment_model.PaymentModel._get_all")
    def test_get_all_payments(self, mock_get_all, auth_employee_client):
        mock_get_all.return_value = [
            {"id": 1, "orden_venta_id": 10, "estado": "verificado"}
        ]
        response = auth_employee_client.get('/api/payments/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.payment_model.PaymentModel._get_by_id")
    def test_get_one_payment_found(self, mock_get_by_id, auth_employee_client):
        mock_get_by_id.return_value = {"id": 1, "orden_venta_id": 10, "total": 120.00}
        response = auth_employee_client.get('/api/payments/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.payment_model.PaymentModel._get_by_id")
    def test_get_one_payment_not_found(self, mock_get_by_id, auth_employee_client):
        mock_get_by_id.return_value = None
        response = auth_employee_client.get('/api/payments/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    def test_approve_unauthorized_fails(self, client):
        response = client.post('/api/payments/1/approve')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.notification_model.NotificationModel.ejecutar")
    @patch("model.payment_model.PaymentModel._get_order_info_for_email")
    @patch("model.payment_model.PaymentModel._approve")
    @patch("model.payment_model.PaymentModel._get_by_id")
    def test_approve_payment_success(
        self, mock_get_by_id, mock_approve, mock_get_email, mock_notif, auth_employee_client
    ):
        mock_get_by_id.return_value = {"id": 1, "orden_venta_id": 10, "cliente_cedula": "V-12345678"}
        mock_approve.return_value = True
        mock_get_email.return_value = {"order": {"id": 10}}

        response = auth_employee_client.post('/api/payments/1/approve')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "verificado correctamente" in json_data["message"].lower()

    @patch("model.notification_model.NotificationModel.ejecutar")
    @patch("model.payment_model.PaymentModel._reject")
    @patch("model.payment_model.PaymentModel._get_by_id")
    def test_reject_payment_success(
        self, mock_get_by_id, mock_reject, mock_notif, auth_employee_client
    ):
        mock_get_by_id.return_value = {"id": 1, "orden_venta_id": 10, "cliente_cedula": "V-12345678"}
        mock_reject.return_value = True

        response = auth_employee_client.post('/api/payments/1/reject', json={
            "observaciones": "Número de referencia no coincide"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "rechazado correctamente" in json_data["message"].lower()
