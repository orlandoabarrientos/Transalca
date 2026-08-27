import io
import pytest
from unittest.mock import patch, MagicMock
from app import app as flask_app
from config.validation import ValidationError


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def auth_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


@pytest.fixture
def auth_user_without_cedula(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_tipo'] = 'cliente'
    return client


@pytest.fixture
def auth_other_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_cedula'] = 'V-99999999'
        sess['user_tipo'] = 'cliente'
    return client


@pytest.fixture
def auth_admin_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_cedula'] = 'V-10000000'
        sess['user_tipo'] = 'admin'
    return client


class TestOrderController:
    """Pruebas de integracion de rutas API para carrito de compras y ordenes de venta."""

    # 1. Carrito: Consulta y conteo
    def test_get_cart_unauthorized_fails(self, client):
        response = client.get('/api/orders/cart')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    def test_cart_count_unauthorized_fails(self, client):
        response = client.get('/api/orders/cart/count')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    def test_cart_count_without_cedula_returns_zero(self, auth_user_without_cedula):
        response = auth_user_without_cedula.get('/api/orders/cart/count')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["count"] == 0

    @patch("model.order_model.OrderModel._get_cart_count", return_value=5)
    def test_cart_count_authorized_success(self, mock_count, auth_client_user):
        response = auth_client_user.get('/api/orders/cart/count')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["count"] == 5

    @patch("model.order_model.OrderModel._get_cart")
    def test_get_cart_authorized_success(self, mock_get_cart, auth_client_user):
        mock_get_cart.return_value = [
            {"id": 1, "item_nombre": "Filtro Aceite", "cantidad": 2}
        ]
        response = auth_client_user.get('/api/orders/cart')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    # 2. Agregar al carrito
    def test_add_to_cart_unauthorized_fails(self, client):
        response = client.post('/api/orders/cart/add', json={"tipo": "producto", "item_id": 10, "cantidad": 1})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._add_to_cart", return_value=1)
    def test_add_to_cart_authorized_success(self, mock_add_to_cart, auth_client_user):
        response = auth_client_user.post('/api/orders/cart/add', json={
            "tipo": "producto",
            "item_id": 10,
            "cantidad": 2
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "registrado en el carrito" in json_data["message"].lower()

    @patch("model.order_model.OrderModel._add_to_cart", side_effect=ValidationError({"cantidad": "La cantidad no es valida"}))
    def test_add_to_cart_validation_error(self, mock_add, auth_client_user):
        response = auth_client_user.post('/api/orders/cart/add', json={"tipo": "producto", "item_id": 10, "cantidad": -1})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "cantidad" in json_data["errors"]

    @patch("model.order_model.OrderModel._add_to_cart", side_effect=ValueError("Producto no disponible"))
    def test_add_to_cart_value_error(self, mock_add, auth_client_user):
        response = auth_client_user.post('/api/orders/cart/add', json={"tipo": "producto", "item_id": 999, "cantidad": 1})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "no disponible" in json_data["message"].lower()

    # 3. Modificar cantidad en carrito
    def test_update_cart_unauthorized_fails(self, client):
        response = client.put('/api/orders/cart/1/update', json={"cantidad": 3})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-99999999")
    def test_update_cart_not_owner_forbidden(self, mock_owner, auth_client_user):
        response = auth_client_user.put('/api/orders/cart/1/update', json={"cantidad": 3})
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._update_cart_quantity", return_value=1)
    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-12345678")
    def test_update_cart_success(self, mock_owner, mock_update_cart, auth_client_user):
        response = auth_client_user.put('/api/orders/cart/1/update', json={"cantidad": 3})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.order_model.OrderModel._update_cart_quantity", side_effect=ValidationError({"cantidad": "Cantidad invalida"}))
    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-12345678")
    def test_update_cart_validation_error(self, mock_owner, mock_update, auth_client_user):
        response = auth_client_user.put('/api/orders/cart/1/update', json={"cantidad": -2})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    # 4. Eliminar item y vaciar carrito
    def test_remove_from_cart_unauthorized_fails(self, client):
        response = client.delete('/api/orders/cart/1/remove')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-99999999")
    def test_remove_from_cart_not_owner_forbidden(self, mock_owner, auth_client_user):
        response = auth_client_user.delete('/api/orders/cart/1/remove')
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._remove_from_cart", return_value=1)
    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-12345678")
    def test_remove_from_cart_success(self, mock_owner, mock_remove, auth_client_user):
        response = auth_client_user.delete('/api/orders/cart/1/remove')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    def test_clear_cart_unauthorized_fails(self, client):
        response = client.delete('/api/orders/cart/clear')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._clear_cart", return_value=1)
    def test_clear_cart_success(self, mock_clear, auth_client_user):
        response = auth_client_user.delete('/api/orders/cart/clear')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    # 5. Checkout (POST /checkout)
    def test_checkout_unauthorized_fails(self, client):
        response = client.post('/api/orders/checkout')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._is_valid_payment_method", return_value=False)
    def test_checkout_invalid_payment_method_fails(self, mock_valid_pay, auth_client_user):
        response = auth_client_user.post('/api/orders/checkout', data={"metodo_pago": "invalido"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._is_valid_payment_method", return_value=True)
    def test_checkout_invalid_receipt_extension_fails(self, mock_valid_pay, auth_client_user):
        data = {
            "metodo_pago": "pago_movil",
            "comprobante": (io.BytesIO(b"fake data"), "malicioso.exe")
        }
        response = auth_client_user.post('/api/orders/checkout', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "comprobante" in json_data["message"].lower()

    @patch("model.order_model.OrderModel._is_valid_payment_method", return_value=True)
    @patch("model.order_model.OrderModel._create_sale_order", return_value=50)
    def test_checkout_success_without_receipt(self, mock_create, mock_valid_pay, auth_client_user):
        response = auth_client_user.post('/api/orders/checkout', data={"metodo_pago": "efectivo"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["id"] == 50

    @patch("model.order_model.OrderModel._is_valid_payment_method", return_value=True)
    @patch("model.order_model.OrderModel._create_sale_order", return_value=51)
    def test_checkout_success_with_receipt(self, mock_create, mock_valid_pay, auth_client_user):
        data = {
            "metodo_pago": "pago_movil",
            "comprobante": (io.BytesIO(b"dummy image bytes"), "comprobante.png")
        }
        with patch("os.makedirs"):
            response = auth_client_user.post('/api/orders/checkout', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

            assert response.status_code == 200
            assert json_data["status"] == "success"
            assert json_data["id"] == 51

    @patch("model.order_model.OrderModel._is_valid_payment_method", return_value=True)
    @patch("model.order_model.OrderModel._create_sale_order", return_value=None)
    def test_checkout_empty_cart_fails(self, mock_create, mock_valid_pay, auth_client_user):
        response = auth_client_user.post('/api/orders/checkout', data={"metodo_pago": "pago_movil"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "vacio" in json_data["message"].lower()

    @patch("model.order_model.OrderModel._is_valid_payment_method", return_value=True)
    @patch("model.order_model.OrderModel._create_sale_order", side_effect=ValueError("Las compras a credito solo estan disponibles para empresas."))
    def test_checkout_value_error(self, mock_create, mock_valid_pay, auth_client_user):
        response = auth_client_user.post('/api/orders/checkout', data={"metodo_pago": "credito"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "credito" in json_data["message"].lower()

    # 6. Mis ordenes (GET /my-orders)
    def test_my_orders_unauthorized_fails(self, client):
        response = client.get('/api/orders/my-orders')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._get_client_orders")
    def test_my_orders_success(self, mock_get_client_orders, auth_client_user):
        mock_get_client_orders.return_value = [
            {"id": 100, "total": 150.00, "fecha": "2026-08-22"}
        ]
        response = auth_client_user.get('/api/orders/my-orders')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    # 7. Detalle de orden (GET /<id>)
    def test_get_order_unauthorized_fails(self, client):
        response = client.get('/api/orders/100')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.order_model.OrderModel._get_order_detail")
    def test_get_order_owner_client_success(self, mock_get_order, auth_client_user):
        mock_get_order.return_value = {
            "id": 100, "cliente_cedula": "V-12345678", "total": 150.00
        }
        response = auth_client_user.get('/api/orders/100')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 100

    @patch("model.order_model.OrderModel._get_order_detail")
    def test_get_order_admin_can_view_any_order(self, mock_get_order, auth_admin_user):
        mock_get_order.return_value = {
            "id": 100, "cliente_cedula": "V-12345678", "total": 150.00
        }
        response = auth_admin_user.get('/api/orders/100')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 100

    @patch("model.order_model.OrderModel._get_order_detail")
    def test_get_order_other_client_unauthorized(self, mock_get_order, auth_other_client_user):
        mock_get_order.return_value = {
            "id": 100, "cliente_cedula": "V-12345678", "total": 150.00
        }
        response = auth_other_client_user.get('/api/orders/100')
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"
        assert "no autorizado" in json_data["message"].lower()

    @patch("model.order_model.OrderModel._get_order_detail", return_value=None)
    def test_get_order_not_found(self, mock_get_order, auth_client_user):
        response = auth_client_user.get('/api/orders/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"
