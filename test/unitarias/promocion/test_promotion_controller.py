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


class TestPromotionController:
    """Pruebas de integración de rutas API para promociones y programa de fidelidad."""

    @patch("model.promotion_model.PromotionModel._nombre_exists")
    def test_check_unique_name(self, mock_nombre_exists, auth_employee_client):
        mock_nombre_exists.return_value = False
        response = auth_employee_client.get('/api/promotions/check-unique?value=PromoTest')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is True

    @patch("model.promotion_model.PromotionModel._get_all")
    def test_get_all_promotions(self, mock_get_all, auth_employee_client):
        mock_get_all.return_value = [
            {"id": 1, "nombre": "5to Cambio Gratis", "tipo": "puntos"}
        ]
        response = auth_employee_client.get('/api/promotions/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.promotion_model.PromotionModel._get_active")
    def test_get_active_promotions(self, mock_get_active, auth_employee_client):
        mock_get_active.return_value = [
            {"id": 1, "nombre": "5to Cambio Gratis"}
        ]
        response = auth_employee_client.get('/api/promotions/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.promotion_model.PromotionModel._get_by_id")
    def test_get_one_promotion_found(self, mock_get_by_id, auth_employee_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "5to Cambio Gratis"}
        response = auth_employee_client.get('/api/promotions/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["id"] == 1

    @patch("model.promotion_model.PromotionModel._get_by_id")
    def test_get_one_promotion_not_found(self, mock_get_by_id, auth_employee_client):
        mock_get_by_id.return_value = None
        response = auth_employee_client.get('/api/promotions/999')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    def test_create_regular_client_denied(self, auth_regular_client):
        response = auth_regular_client.post('/api/promotions/', json={
            "nombre": "Promo Test",
            "tipo": "puntos",
            "puntos_requeridos": 3
        })
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"

    @patch("model.promotion_model.PromotionModel._create")
    def test_create_employee_authorized_success(self, mock_create, auth_employee_client):
        mock_create.return_value = 1
        response = auth_employee_client.post('/api/promotions/', json={
            "nombre": "Promo Test",
            "tipo": "puntos",
            "puntos_requeridos": 3
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["id"] == 1

    @patch("model.promotion_model.PromotionModel._soft_delete")
    @patch("model.promotion_model.PromotionModel._get_by_id")
    def test_delete_promotion_success(self, mock_get_by_id, mock_soft_delete, auth_employee_client):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Promo Test"}
        mock_soft_delete.return_value = 0

        response = auth_employee_client.delete('/api/promotions/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
