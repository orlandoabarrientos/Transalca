import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app
from config.validation import ValidationError
from datetime import datetime


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def auth_employee(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 10
        sess['user_cedula'] = 'V-20000000'
        sess['user_tipo'] = 'empleado'
    return client


@pytest.fixture
def auth_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 20
        sess['user_cedula'] = 'V-30000000'
        sess['user_tipo'] = 'cliente'
    return client


class TestPurchaseOrderController:
    """Pruebas de integracion de rutas API para ordenes de compra."""

    # 1. Seguridad: Acceso no autenticado y denegacion a clientes
    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/purchase-orders/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    def test_get_all_client_role_denied(self, auth_client_user):
        response = auth_client_user.get('/api/purchase-orders/')
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"

    # 2. Listado de ordenes de compra y estadisticas
    @patch("model.purchase_order_model.PurchaseOrderModel._get_all")
    def test_get_all_authorized_success(self, mock_get_all, auth_employee):
        mock_get_all.return_value = [
            {"id": 1, "proveedor_nombre": "Distribuidora Repuestos", "total": 1200.0, "estado": "pendiente"}
        ]
        response = auth_employee.get('/api/purchase-orders/?q=Repuestos&estado=pendiente')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1
        mock_get_all.assert_called_once_with("Repuestos", "pendiente")

    @patch("model.purchase_order_model.PurchaseOrderModel._get_stats")
    def test_stats_success(self, mock_stats, auth_employee):
        mock_stats.return_value = {
            "total": 10, "pendientes": 4, "comprados": 6, "total_invertido": 15000.00
        }
        response = auth_employee.get('/api/purchase-orders/stats')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["total"] == 10

    # 3. Registro de orden de compra (POST /)
    @patch("model.purchase_order_model.PurchaseOrderModel._create")
    def test_create_order_success(self, mock_create, auth_employee):
        mock_create.return_value = {"ok": True, "id": 5, "message": "Orden de compra registrada correctamente."}
        response = auth_employee.post('/api/purchase-orders/', json={
            "proveedor_rif": "J-12345678-0",
            "sucursal_id": 1,
            "items": [{"producto_codigo": "PROD001", "cantidad": 10, "precio_unitario": 20.0}]
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 5

    @patch("model.purchase_order_model.PurchaseOrderModel._create")
    def test_create_order_business_failure(self, mock_create, auth_employee):
        mock_create.return_value = {"ok": False, "message": "La sucursal destino no existe o esta inactiva."}
        response = auth_employee.post('/api/purchase-orders/', json={"sucursal_id": 999})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "no existe" in json_data["message"]

    @patch("model.purchase_order_model.PurchaseOrderModel._create", side_effect=ValidationError({"proveedor_rif": "El proveedor es obligatorio."}))
    def test_create_order_validation_error(self, mock_create, auth_employee):
        response = auth_employee.post('/api/purchase-orders/', json={})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "proveedor_rif" in json_data["errors"]

    # 4. Detalle de orden por ID
    @patch("model.purchase_order_model.PurchaseOrderModel._get_by_id")
    def test_get_one_order_found(self, mock_get_by_id, auth_employee):
        mock_get_by_id.return_value = {
            "id": 1, "proveedor_nombre": "Proveedor A", "total": 500.0, "detalles": []
        }
        response = auth_employee.get('/api/purchase-orders/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.purchase_order_model.PurchaseOrderModel._get_by_id", return_value=None)
    def test_get_one_order_not_found(self, mock_get_by_id, auth_employee):
        response = auth_employee.get('/api/purchase-orders/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    # 5. Marcar como comprada (POST /<id>/buy)
    @patch("model.purchase_order_model.PurchaseOrderModel._mark_as_bought")
    def test_mark_as_bought_success(self, mock_buy, auth_employee):
        mock_buy.return_value = {"ok": True, "message": "Orden de compra marcada como comprada. Stock actualizado."}
        response = auth_employee.post('/api/purchase-orders/1/buy')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.purchase_order_model.PurchaseOrderModel._mark_as_bought")
    def test_mark_as_bought_already_bought_fails(self, mock_buy, auth_employee):
        mock_buy.return_value = {"ok": False, "message": "Esta orden de compra ya ha sido procesada como comprada."}
        response = auth_employee.post('/api/purchase-orders/1/buy')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    # 6. Generacion de PDF (GET /<id>/pdf)
    @patch("model.purchase_order_model.PurchaseOrderModel._get_by_id")
    def test_get_pdf_success(self, mock_get_by_id, auth_employee):
        mock_get_by_id.return_value = {
            "id": 1,
            "fecha": datetime(2026, 8, 20, 10, 30),
            "estado": "pendiente",
            "proveedor_nombre": "Repuestos CA",
            "proveedor_rif": "J-12345678-0",
            "proveedor_telefono": "04141234567",
            "proveedor_email": "prov@ejemplo.com",
            "sucursal_nombre": "Central",
            "sucursal_direccion": "Av Principal",
            "observaciones": "Entrega urgente",
            "total": 100.00,
            "detalles": [
                {"producto_codigo": "PROD001", "producto_nombre": "Filtro", "cantidad": 2, "precio_unitario": 50.0, "subtotal": 100.0}
            ]
        }
        response = auth_employee.get('/api/purchase-orders/1/pdf')

        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert b"%PDF" in response.data

    @patch("model.purchase_order_model.PurchaseOrderModel._get_by_id", return_value=None)
    def test_get_pdf_order_not_found(self, mock_get_by_id, auth_employee):
        response = auth_employee.get('/api/purchase-orders/999/pdf')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"
