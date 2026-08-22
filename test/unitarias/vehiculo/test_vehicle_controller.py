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


@pytest.fixture
def auth_client_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


class TestVehicleController:
    """Pruebas de integración de rutas API para gestión de vehículos."""

    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/vehicles/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.vehicle_model.VehicleModel._get_all")
    def test_get_all_employee_authorized_success(self, mock_get_all, auth_employee_client):
        mock_get_all.return_value = [
            {"id": "ABC-1234", "placa": "ABC-1234", "marca": "Toyota", "modelo": "Corolla"}
        ]
        response = auth_employee_client.get('/api/vehicles/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.vehicle_model.VehicleModel._get_km_history")
    @patch("model.vehicle_model.VehicleModel._get_cauchos")
    @patch("model.vehicle_model.VehicleModel._get_by_id")
    def test_get_one_employee_success(self, mock_get_by_id, mock_get_cauchos, mock_get_km, auth_employee_client):
        mock_get_by_id.return_value = {"id": "ABC-1234", "placa": "ABC-1234", "marca": "Toyota", "cliente_cedula": "V-12345678"}
        mock_get_cauchos.return_value = []
        mock_get_km.return_value = []

        response = auth_employee_client.get('/api/vehicles/ABC-1234')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["placa"] == "ABC-1234"

    @patch("controller.vehicle_controller.can_access_client", return_value=True)
    @patch("model.vehicle_model.VehicleModel._get_by_placa")
    @patch("model.vehicle_model.VehicleModel._create")
    @patch("model.vehicle_model.VehicleModel._validate")
    def test_create_vehicle_employee_success(
        self, mock_validate, mock_create, mock_get_by_placa, mock_can_access, auth_employee_client
    ):
        mock_validate.return_value = {
            "marca": "Toyota", "modelo": "Yaris", "placa": "ABC-1234",
            "tipo_combustible": "gasolina", "kilometraje_actual": 10000
        }
        mock_get_by_placa.return_value = None
        mock_create.return_value = "ABC-1234"

        response = auth_employee_client.post('/api/vehicles/', json={
            "marca": "Toyota",
            "modelo": "Yaris",
            "placa": "ABC-1234",
            "cliente_cedula": "V-12345678"
        })
        json_data = response.get_json()

        assert response.status_code == 201
        assert json_data["status"] == "success"
        assert json_data["id"] == "ABC-1234"

    @patch("model.vehicle_model.VehicleModel._update_kilometraje")
    @patch("model.vehicle_model.VehicleModel._get_by_id")
    def test_update_km_success(self, mock_get_by_id, mock_update_km, auth_employee_client):
        mock_get_by_id.return_value = {"id": "ABC-1234", "placa": "ABC-1234", "cliente_cedula": "V-12345678"}
        mock_update_km.return_value = True

        response = auth_employee_client.put('/api/vehicles/ABC-1234/km', json={"kilometraje": 60000})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "kilometraje actualizado" in json_data["message"].lower()

    @patch("model.vehicle_model.VehicleModel._soft_delete")
    @patch("model.vehicle_model.VehicleModel._get_by_id")
    def test_delete_vehicle_success(self, mock_get_by_id, mock_soft_delete, auth_employee_client):
        mock_get_by_id.return_value = {"id": "ABC-1234", "placa": "ABC-1234", "cliente_cedula": "V-12345678"}
        mock_soft_delete.return_value = 1

        response = auth_employee_client.delete('/api/vehicles/ABC-1234')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
