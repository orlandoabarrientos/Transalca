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


class TestUserController:
    """Pruebas de integración de rutas API para usuarios."""

    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/users/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.user_model.UserModel._get_all")
    def test_get_all_authorized_success(self, mock_get_all, auth_client):
        mock_get_all.return_value = [
            {"id": 1, "nombre": "María", "apellido": "Delgado", "email": "maria@ejemplo.com"}
        ]
        response = auth_client.get('/api/users/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.user_model.UserModel._get_user_roles")
    @patch("model.user_model.UserModel._get_by_id")
    def test_get_one_user_found(self, mock_get_by_id, mock_get_user_roles, auth_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "María", "apellido": "Delgado"}
        mock_get_user_roles.return_value = [{"id": 1, "nombre": "Administrador"}]

        response = auth_client.get('/api/users/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1
        assert len(json_data["data"]["roles"]) == 1

    @patch("model.user_model.UserModel._get_by_id")
    def test_get_one_user_not_found(self, mock_get_by_id, auth_client):
        mock_get_by_id.return_value = None
        response = auth_client.get('/api/users/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    @patch("model.user_model.UserModel._search")
    def test_search_users(self, mock_search, auth_client):
        mock_search.return_value = [{"id": 1, "nombre": "María"}]
        response = auth_client.get('/api/users/search?q=maria')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.user_model.UserModel._soft_delete")
    def test_delete_user_last_admin_protection(self, mock_soft_delete, auth_client):
        mock_soft_delete.return_value = False
        response = auth_client.delete('/api/users/1')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "ultimo administrador" in json_data["message"].lower()

    @patch("model.user_model.UserModel._soft_delete")
    def test_delete_user_success(self, mock_soft_delete, auth_client):
        mock_soft_delete.return_value = True
        response = auth_client.delete('/api/users/2')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
