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
def auth_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


class TestScannerController:
    """Pruebas de integración de rutas API para lectura de QR y gestión de validaciones."""

    def test_scan_qr_unauthorized_fails(self, client):
        response = client.post('/api/scanner/scan', json={"raw": "15"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.scanner_model.ScannerModel._process_scan_for_employee")
    @patch("model.scanner_model.ScannerModel._resolve_qr_from_raw")
    def test_scan_qr_employee_success(
        self, mock_resolve, mock_process_employee, auth_employee_client
    ):
        mock_resolve.return_value = ({"id": 15, "tipo": "pago", "utilidad": "factura"}, None)
        mock_process_employee.return_value = {
            "mode": "factura_validada",
            "message": "Factura valida",
            "order": {"id": 10}
        }

        response = auth_employee_client.post('/api/scanner/scan', json={"raw": "15"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["mode"] == "factura_validada"

    def test_promotions_regular_client_denied(self, auth_client_user):
        response = auth_client_user.get('/api/scanner/promotions')
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"
        assert "solo empleados" in json_data["message"].lower()

    @patch("model.scanner_model.ScannerModel._get_active_promotions")
    def test_promotions_employee_authorized_success(self, mock_get_promos, auth_employee_client):
        mock_get_promos.return_value = [
            {"id": 1, "nombre": "Promo 5to Cambio", "puntos_requeridos": 5}
        ]
        response = auth_employee_client.get('/api/scanner/promotions')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.scanner_model.ScannerModel._create_validation_request")
    @patch("model.scanner_model.ScannerModel._pending_validation_for_order")
    @patch("model.scanner_model.ScannerModel._latest_comprobante")
    @patch("model.scanner_model.ScannerModel._get_order_basic")
    def test_solicitar_validacion_success(
        self, mock_get_order, mock_latest_comp, mock_pending, mock_create_req, auth_client_user
    ):
        mock_get_order.return_value = {"id": 10, "cliente_cedula": "V-12345678"}
        mock_latest_comp.return_value = {"id_comprobante_pago": 100}
        mock_pending.return_value = None
        mock_create_req.return_value = 1

        response = auth_client_user.post('/api/scanner/solicitar-validacion', json={"orden_id": 10})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "solicitud de validacion enviada" in json_data["message"].lower()

    @patch("model.scanner_model.ScannerModel._get_pending_validations")
    def test_get_solicitudes_pendientes_employee_success(
        self, mock_get_pending, auth_employee_client
    ):
        mock_get_pending.return_value = []
        response = auth_employee_client.get('/api/scanner/solicitudes-pendientes')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.notification_model.NotificationModel.ejecutar")
    @patch("model.order_model.OrderModel.ejecutar")
    @patch("model.scanner_model.ScannerModel._set_comprobante_status")
    @patch("model.scanner_model.ScannerModel._set_order_status")
    @patch("model.scanner_model.ScannerModel._order_client_cedula")
    @patch("model.scanner_model.ScannerModel._set_validation_status")
    @patch("model.scanner_model.ScannerModel._get_validation_by_id")
    def test_responder_validacion_aprobar_success(
        self, mock_get_val, mock_set_val_status, mock_order_client, mock_set_order_status,
        mock_set_comp_status, mock_order_model, mock_notif, auth_employee_client
    ):
        mock_get_val.return_value = {"id": 1, "orden_venta_id": 10, "comprobante_pago_id": 100, "tipo": "validar_pago"}
        mock_order_client.return_value = {"cliente_cedula": "V-12345678"}

        response = auth_employee_client.post('/api/scanner/responder-validacion', json={
            "solicitud_id": 1,
            "respuesta": "aprobar"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "aprobada con exito" in json_data["message"].lower()
