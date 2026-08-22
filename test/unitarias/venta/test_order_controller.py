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
def auth_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


@pytest.fixture
def auth_other_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 3
        sess['user_cedula'] = 'V-99999999'
        sess['user_tipo'] = 'cliente'
    return client


class TestOrderController:
    """Pruebas de integración de rutas API para carrito de compras y órdenes de venta."""

    def test_get_cart_unauthorized_fails(self, client):
        response = client.get('/api/orders/cart')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

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

    @patch("model.order_model.OrderModel._add_to_cart")
    def test_add_to_cart_authorized_success(self, mock_add_to_cart, auth_client_user):
        mock_add_to_cart.return_value = 1
        response = auth_client_user.post('/api/orders/cart/add', json={
            "tipo": "producto",
            "item_id": 10,
            "cantidad": 2
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "registrado en el carrito" in json_data["message"].lower()

    @patch("model.order_model.OrderModel._update_cart_quantity")
    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-12345678")
    def test_update_cart_success(self, mock_owner, mock_update_cart, auth_client_user):
        mock_update_cart.return_value = 1
        response = auth_client_user.put('/api/orders/cart/1/update', json={"cantidad": 3})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.order_model.OrderModel._remove_from_cart")
    @patch("model.order_model.OrderModel._cart_item_owner", return_value="V-12345678")
    def test_remove_from_cart_success(self, mock_owner, mock_remove, auth_client_user):
        mock_remove.return_value = 1
        response = auth_client_user.delete('/api/orders/cart/1/remove')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.order_model.OrderModel._clear_cart")
    def test_clear_cart_success(self, mock_clear, auth_client_user):
        mock_clear.return_value = 1
        response = auth_client_user.delete('/api/orders/cart/clear')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

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
