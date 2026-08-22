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
def auth_regular_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


class TestTicketController:
    """Pruebas de integración de rutas API para tickets de soporte."""

    def test_get_all_unauthorized_fails(self, client):
        response = client.get('/api/tickets/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.ticket_model.TicketModel._get_all")
    def test_get_all_employee_authorized_success(self, mock_get_all, auth_employee_client):
        mock_get_all.return_value = [
            {"id": 1, "asunto": "Falla en vehículo", "estado": "abierto"}
        ]
        response = auth_employee_client.get('/api/tickets/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.ticket_model.TicketModel._get_by_cliente")
    def test_get_all_regular_client_returns_own_tickets(self, mock_get_by_cliente, auth_regular_client):
        mock_get_by_cliente.return_value = [
            {"id": 1, "asunto": "Mi ticket", "cliente_cedula": "V-12345678"}
        ]
        response = auth_regular_client.get('/api/tickets/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_get_by_cliente.assert_called_with("V-12345678")

    @patch("model.ticket_model.TicketModel._get_by_id")
    def test_get_one_ticket_found(self, mock_get_by_id, auth_employee_client):
        mock_get_by_id.return_value = {
            "id": 1,
            "asunto": "Consulta de repuesto",
            "cliente_cedula": "V-12345678",
            "respuestas": []
        }
        response = auth_employee_client.get('/api/tickets/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.ticket_model.TicketModel._get_by_id")
    def test_get_one_ticket_not_found(self, mock_get_by_id, auth_employee_client):
        mock_get_by_id.return_value = None
        response = auth_employee_client.get('/api/tickets/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    @patch("model.ticket_model.TicketModel._create")
    def test_create_ticket_success(self, mock_create, auth_employee_client):
        mock_create.return_value = 1
        response = auth_employee_client.post('/api/tickets/', json={
            "cliente_cedula": "V-12345678",
            "asunto": "Soporte general",
            "descripcion": "Descripción del problema"
        })
        json_data = response.get_json()

        assert response.status_code == 201
        assert json_data["status"] == "success"
        assert json_data["id"] == 1

    def test_create_ticket_missing_required_fields_fails(self, auth_employee_client):
        response = auth_employee_client.post('/api/tickets/', json={
            "descripcion": "Sin asunto ni cédula"
        })
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    @patch("model.ticket_model.TicketModel._count_by_estado")
    def test_stats_employee_success(self, mock_count_by_estado, auth_employee_client):
        mock_count_by_estado.return_value = [
            {"estado": "abierto", "total": 5}
        ]
        response = auth_employee_client.get('/api/tickets/stats')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
