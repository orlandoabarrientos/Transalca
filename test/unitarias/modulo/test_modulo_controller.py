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
def auth_admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_cedula'] = 'V-10000000'
        sess['user_tipo'] = 'admin'
        sess['roles'] = ['Administrador']
    return client


class TestModuloController:
    """Pruebas de integración de rutas API para administración de módulos del sistema."""

    def test_sidebar_unauthorized_fails(self, client):
        response = client.get('/api/modulos/sidebar')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.modulo_model.ModuloModel._get_sidebar_modules")
    def test_sidebar_authorized_success(self, mock_get_sidebar, auth_admin_client):
        mock_get_sidebar.return_value = [
            {"nombre": "clientes", "titulo": "Clientes", "ruta": "/admin/clientes", "publico": 0}
        ]
        response = auth_admin_client.get('/api/modulos/sidebar')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.modulo_model.ModuloModel._get_permission_modules")
    def test_permissions_list_authorized_success(self, mock_get_permission_modules, auth_admin_client):
        mock_get_permission_modules.return_value = [
            {"modulo": "clientes", "titulo": "Clientes", "grupo": "Ventas"}
        ]
        response = auth_admin_client.get('/api/modulos/permissions-list')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.modulo_model.ModuloModel._nombre_exists")
    def test_check_unique_name(self, mock_nombre_exists, auth_admin_client):
        mock_nombre_exists.return_value = False
        response = auth_admin_client.get('/api/modulos/check-unique?field=nombre&value=modulo_prueba')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is True

    @patch("model.modulo_model.ModuloModel._get_all")
    def test_get_all_modules_admin(self, mock_get_all, auth_admin_client):
        mock_get_all.return_value = [
            {"id": 1, "nombre": "clientes", "titulo": "Clientes"}
        ]
        response = auth_admin_client.get('/api/modulos/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.modulo_model.ModuloModel._create")
    def test_create_module_admin_success(self, mock_create, auth_admin_client):
        mock_create.return_value = 1
        response = auth_admin_client.post('/api/modulos/', json={
            "nombre": "ordenes_compra",
            "titulo": "Órdenes de Compra",
            "ruta": "/admin/ordenes-compra",
            "grupo": "Compras"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "registrado correctamente" in json_data["message"].lower()

    @patch("model.modulo_model.ModuloModel._soft_delete")
    def test_delete_module_admin_success(self, mock_soft_delete, auth_admin_client):
        mock_soft_delete.return_value = 0
        response = auth_admin_client.delete('/api/modulos/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
