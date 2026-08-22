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
def auth_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_cedula'] = 'V-10000000'
        sess['user_tipo'] = 'admin'
    return client


class TestSucursalController:
    """Pruebas de integración de rutas API para sucursales."""

    @patch("model.sucursal_model.SucursalModel._get_all")
    def test_get_all_sucursales(self, mock_get_all, auth_client):
        mock_get_all.return_value = [
            {"id": 1, "nombre": "Sucursal Centro", "direccion": "Av. Vargas"}
        ]
        response = auth_client.get('/api/sucursales/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.sucursal_model.SucursalModel._get_active")
    def test_get_active_sucursales(self, mock_get_active, client):
        mock_get_active.return_value = [
            {"id": 1, "nombre": "Sucursal Centro"}
        ]
        response = client.get('/api/sucursales/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.sucursal_model.SucursalModel._get_by_id")
    def test_get_one_sucursal_found(self, mock_get_by_id, auth_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Sucursal Centro"}
        response = auth_client.get('/api/sucursales/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.sucursal_model.SucursalModel._get_by_id")
    def test_get_one_sucursal_not_found(self, mock_get_by_id, auth_client):
        mock_get_by_id.return_value = None
        response = auth_client.get('/api/sucursales/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    def test_create_unauthorized_fails(self, client):
        response = client.post('/api/sucursales/', json={
            "nombre": "Sucursal Centro",
            "direccion": "Av. Vargas"
        })
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.sucursal_model.SucursalModel._create")
    def test_create_authorized_success(self, mock_create, auth_client):
        mock_create.return_value = 1
        response = auth_client.post('/api/sucursales/', json={
            "nombre": "Sucursal Centro",
            "direccion": "Av. Vargas"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["id"] == 1

    @patch("model.sucursal_model.SucursalModel._soft_delete")
    def test_delete_sucursal_success(self, mock_soft_delete, auth_client):
        mock_soft_delete.return_value = 1
        response = auth_client.delete('/api/sucursales/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
