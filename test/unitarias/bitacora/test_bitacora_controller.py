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


class TestBitacoraController:
    """Pruebas de integración de rutas API para consulta de eventos de la bitácora del sistema."""

    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/bitacora/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.bitacora_model.BitacoraModel._count_all")
    @patch("model.bitacora_model.BitacoraModel._get_all")
    def test_get_all_authorized_success(self, mock_get_all, mock_count_all, auth_employee_client):
        mock_get_all.return_value = [
            {"id": 1, "accion": "LOGIN", "modulo": "auth", "usuario_id": 1}
        ]
        mock_count_all.return_value = 10

        response = auth_employee_client.get('/api/bitacora/?page=1&limit=10')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["total"] == 10
        assert len(json_data["data"]) == 1

    @patch("model.bitacora_model.BitacoraModel._get_by_user")
    def test_get_by_user_authorized_success(self, mock_get_by_user, auth_employee_client):
        mock_get_by_user.return_value = [
            {"id": 1, "usuario_id": 5, "accion": "UPDATE"}
        ]
        response = auth_employee_client.get('/api/bitacora/user/5')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.bitacora_model.BitacoraModel._get_by_module")
    def test_get_by_module_authorized_success(self, mock_get_by_module, auth_employee_client):
        mock_get_by_module.return_value = [
            {"id": 2, "modulo": "clientes", "accion": "CREATE"}
        ]
        response = auth_employee_client.get('/api/bitacora/module/clientes')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.bitacora_model.BitacoraModel._search")
    def test_search_authorized_success(self, mock_search, auth_employee_client):
        mock_search.return_value = [
            {"id": 3, "accion": "DELETE", "descripcion": "Eliminación de rol"}
        ]
        response = auth_employee_client.get('/api/bitacora/search?q=rol')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.bitacora_model.BitacoraModel._get_by_date_range")
    def test_filter_by_date_authorized_success(self, mock_get_date_range, auth_employee_client):
        mock_get_date_range.return_value = [
            {"id": 4, "fecha": "2026-08-20"}
        ]
        response = auth_employee_client.get('/api/bitacora/filter?start=2026-08-01&end=2026-08-31')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1
