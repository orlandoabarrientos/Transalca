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
def auth_admin(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_cedula'] = 'V-10000000'
        sess['user_tipo'] = 'admin'
    return client


class TestInventoryController:
    """Pruebas de integracion de rutas API para gestion y registro de stock/inventario."""

    # 1. Obtener inventario general, por sucursal y paginado
    @patch("model.inventory_model.InventoryModel._get_all")
    def test_get_all_success(self, mock_get_all, auth_admin):
        mock_get_all.return_value = [
            {"producto_codigo": "PROD001", "producto_nombre": "Filtro", "stock": 20}
        ]
        response = auth_admin.get('/api/inventory/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.inventory_model.InventoryModel._get_by_sucursal")
    def test_get_by_sucursal_success(self, mock_by_sucursal, auth_admin):
        mock_by_sucursal.return_value = [
            {"producto_codigo": "PROD001", "sucursal_id": 1, "stock": 15}
        ]
        response = auth_admin.get('/api/inventory/?sucursal_id=1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_by_sucursal.assert_called_once_with(1)

    def test_get_with_invalid_sucursal_fails(self, auth_admin):
        response = auth_admin.get('/api/inventory/?sucursal_id=invalido')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    @patch("model.inventory_model.InventoryModel._get_paginated")
    def test_get_paginated(self, mock_paginated, auth_admin):
        mock_paginated.return_value = {
            "data": [{"producto_codigo": "PROD001", "stock": 10}],
            "total": 1,
            "page": 1,
            "per_page": 30,
            "pages": 1
        }
        response = auth_admin.get('/api/inventory/?page=1&per_page=30&q=Filtro')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["total"] == 1

    # 2. Stock bajo (alertas)
    @patch("model.inventory_model.InventoryModel._get_low_stock")
    def test_low_stock(self, mock_low_stock, auth_admin):
        mock_low_stock.return_value = [
            {"producto_codigo": "PROD001", "stock": 2, "stock_minimo": 5}
        ]
        response = auth_admin.get('/api/inventory/low-stock')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    # 3. Actualizacion manual de stock (PUT /update-stock)
    def test_update_stock_unauthorized_fails(self, client):
        response = client.put('/api/inventory/update-stock', json={"producto_codigo": "PROD001", "stock": 10})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.inventory_model.InventoryModel._update_stock", return_value=1)
    def test_update_stock_authorized_success(self, mock_update, auth_admin):
        response = auth_admin.put('/api/inventory/update-stock', json={
            "producto_codigo": "PROD001",
            "sucursal_id": 1,
            "stock": 25
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "actualizado" in json_data["message"].lower()

    @patch("model.inventory_model.InventoryModel._update_stock", side_effect=ValidationError({"stock": "El stock no puede ser negativo"}))
    def test_update_stock_validation_error(self, mock_update, auth_admin):
        response = auth_admin.put('/api/inventory/update-stock', json={
            "producto_codigo": "PROD001",
            "stock": -5
        })
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "stock" in json_data["errors"]

    # 4. Ordenes de venta en inventario
    @patch("model.inventory_model.InventoryModel._get_sales_orders")
    def test_get_sales_orders(self, mock_get_orders, auth_admin):
        mock_get_orders.return_value = [
            {"id": 1, "total": 150.0, "cliente_nombre": "Carlos Mendoza"}
        ]
        response = auth_admin.get('/api/inventory/sales-orders')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.inventory_model.InventoryModel._get_sales_order_detail")
    def test_get_sales_order_detail_found(self, mock_detail, auth_admin):
        mock_detail.return_value = {
            "id": 1, "total": 150.0, "detalles": [{"item_nombre": "Aceite", "cantidad": 2}]
        }
        response = auth_admin.get('/api/inventory/sales-orders/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.inventory_model.InventoryModel._get_sales_order_detail", return_value=None)
    def test_get_sales_order_detail_not_found(self, mock_detail, auth_admin):
        response = auth_admin.get('/api/inventory/sales-orders/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"
