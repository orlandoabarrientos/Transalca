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


class TestRoleController:
    """Pruebas de integración de rutas API para roles y permisos."""

    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/roles/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.role_model.RoleModel._get_all")
    def test_get_all_authorized_success(self, mock_get_all, auth_client):
        mock_get_all.return_value = [
            {"id": 1, "nombre": "Administrador", "descripcion": "Acceso total"}
        ]
        response = auth_client.get('/api/roles/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.role_model.RoleModel._get_permissions")
    @patch("model.role_model.RoleModel._get_by_id")
    def test_get_one_role_found(self, mock_get_by_id, mock_get_permissions, auth_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Administrador"}
        mock_get_permissions.return_value = [{"modulo": "usuarios", "leer": 1}]

        response = auth_client.get('/api/roles/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1
        assert len(json_data["data"]["permisos"]) == 1

    @patch("model.role_model.RoleModel._get_by_id")
    def test_get_one_role_not_found(self, mock_get_by_id, auth_client):
        mock_get_by_id.return_value = None
        response = auth_client.get('/api/roles/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    @patch("model.role_model.RoleModel._create")
    def test_create_role_success(self, mock_create, auth_client):
        mock_create.return_value = 2
        response = auth_client.post('/api/roles/', json={
            "nombre": "Cajero",
            "descripcion": "Acceso al módulo de cobranzas"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["id"] == 2

    @patch("model.role_model.RoleModel._soft_delete")
    def test_delete_admin_role_protected(self, mock_soft_delete, auth_client):
        mock_soft_delete.return_value = False
        response = auth_client.delete('/api/roles/1')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "administrador" in json_data["message"].lower()

    @patch("model.role_model.RoleModel._soft_delete")
    def test_delete_custom_role_success(self, mock_soft_delete, auth_client):
        mock_soft_delete.return_value = 0
        response = auth_client.delete('/api/roles/2')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.role_model.RoleModel._get_modules")
    def test_get_modules_success(self, mock_get_modules, auth_client):
        mock_get_modules.return_value = [
            {"modulo": "clientes", "titulo": "Clientes", "grupo": "Ventas"}
        ]
        response = auth_client.get('/api/roles/modules')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1
