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


class TestServiceController:
    """Pruebas de integración de rutas API para servicios."""

    @patch("model.service_model.ServiceModel._nombre_exists")
    def test_check_unique_name(self, mock_nombre_exists, auth_client):
        mock_nombre_exists.return_value = False
        response = auth_client.get('/api/services/check-unique?value=Alineacion')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is True

    @patch("model.service_model.ServiceModel._get_all")
    def test_get_all_services(self, mock_get_all, auth_client):
        mock_get_all.return_value = [
            {"id": 1, "nombre": "Alineación", "precio": 30.00}
        ]
        response = auth_client.get('/api/services/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.service_model.ServiceModel._get_active")
    def test_get_active_services(self, mock_get_active, client):
        mock_get_active.return_value = [
            {"id": 1, "nombre": "Alineación"}
        ]
        response = client.get('/api/services/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.service_model.ServiceModel._get_by_id")
    def test_get_one_service_found(self, mock_get_by_id, auth_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Alineación"}
        response = auth_client.get('/api/services/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.service_model.ServiceModel._get_by_id")
    def test_get_one_service_not_found(self, mock_get_by_id, auth_client):
        mock_get_by_id.return_value = None
        response = auth_client.get('/api/services/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    @patch("model.service_model.ServiceModel._get_by_sucursal")
    def test_get_services_by_sucursal(self, mock_get_by_sucursal, auth_client):
        mock_get_by_sucursal.return_value = [
            {"id": 1, "nombre": "Alineación", "sucursal_nombre": "Sucursal Centro"}
        ]
        response = auth_client.get('/api/services/sucursal/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    def test_create_unauthorized_fails(self, client):
        response = client.post('/api/services/', json={
            "nombre": "Alineación",
            "precio": 30.00,
            "tipo": "general",
            "sucursal_ids": [1]
        })
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.service_model.ServiceModel._create")
    def test_create_authorized_success(self, mock_create, auth_client):
        mock_create.return_value = 1
        response = auth_client.post('/api/services/', json={
            "nombre": "Alineación",
            "precio": 30.00,
            "tipo": "general",
            "sucursal_ids": [1]
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["id"] == 1

    @patch("model.service_model.ServiceModel._soft_delete")
    @patch("model.service_model.ServiceModel._get_by_id")
    def test_delete_service_success(self, mock_get_by_id, mock_soft_delete, auth_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Alineación"}
        mock_soft_delete.return_value = 1

        response = auth_client.delete('/api/services/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
