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


class TestBrandController:
    """Pruebas de integracion de rutas API para marcas."""

    # 1. Listado de marcas y marcas activas
    @patch("model.brand_model.BrandModel._get_all")
    def test_get_all_success(self, mock_get_all, auth_admin):
        mock_get_all.return_value = [
            {"nombre": "Bosch", "descripcion": "Repuestos alemanes", "total_productos": 8}
        ]
        response = auth_admin.get('/api/brands/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.brand_model.BrandModel._get_active")
    def test_get_active_success(self, mock_get_active, auth_admin):
        mock_get_active.return_value = [{"nombre": "Castrol", "descripcion": "Aceites"}]
        response = auth_admin.get('/api/brands/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    # 2. Comprobar unicidad de nombre de marca
    @patch("model.brand_model.BrandModel._nombre_exists", return_value=False)
    def test_check_unique_name_available(self, mock_exists, auth_admin):
        response = auth_admin.get('/api/brands/check-unique?value=Monroe')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is True

    @patch("model.brand_model.BrandModel._nombre_exists", return_value=True)
    def test_check_unique_name_taken(self, mock_exists, auth_admin):
        response = auth_admin.get('/api/brands/check-unique?value=Bosch')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is False

    # 3. Detalle de marca por nombre
    @patch("model.brand_model.BrandModel._get_by_nombre")
    def test_get_one_found(self, mock_get_by_nombre, auth_admin):
        mock_get_by_nombre.return_value = {"nombre": "Denso", "descripcion": "Bujias y sensores"}
        response = auth_admin.get('/api/brands/Denso')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["nombre"] == "Denso"

    @patch("model.brand_model.BrandModel._get_by_nombre", return_value=None)
    def test_get_one_not_found(self, mock_get_by_nombre, auth_admin):
        response = auth_admin.get('/api/brands/Inexistente')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    # 4. Creacion de marca (POST /)
    def test_create_unauthorized_fails(self, client):
        response = client.post('/api/brands/', json={"nombre": "Gates"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.brand_model.BrandModel._create", return_value="Gates")
    def test_create_authorized_success(self, mock_create, auth_admin):
        response = auth_admin.post('/api/brands/', json={"nombre": "Gates", "descripcion": "Correas"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["nombre"] == "Gates"

    @patch("model.brand_model.BrandModel._create", side_effect=ValidationError({"nombre": "El nombre debe tener al menos 2 caracteres"}))
    def test_create_validation_error(self, mock_create, auth_admin):
        response = auth_admin.post('/api/brands/', json={"nombre": "G"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "nombre" in json_data["errors"]

    # 5. Modificacion de marca (PUT /update)
    def test_update_unauthorized_fails(self, client):
        response = client.put('/api/brands/update', json={"nombre": "Gates"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.brand_model.BrandModel._update_brand", return_value=1)
    def test_update_authorized_success(self, mock_update, auth_admin):
        response = auth_admin.put('/api/brands/update', json={
            "old_nombre": "Gates", "nombre": "Gates International"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    # 6. Eliminacion y Toggle (DELETE /delete & PUT /toggle)
    @patch("model.brand_model.BrandModel._soft_delete", return_value=1)
    def test_delete_success(self, mock_soft_delete, auth_admin):
        response = auth_admin.delete('/api/brands/delete', json={"nombre": "Gates"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_soft_delete.assert_called_once_with("Gates")

    @patch("model.brand_model.BrandModel._toggle_estado", return_value=1)
    def test_toggle_success(self, mock_toggle, auth_admin):
        response = auth_admin.put('/api/brands/toggle', json={"nombre": "Gates"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_toggle.assert_called_once_with("Gates")
