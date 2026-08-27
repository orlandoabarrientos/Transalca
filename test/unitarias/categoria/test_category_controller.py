import io
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


class TestCategoryController:
    """Pruebas de integracion de rutas API para categorias."""

    # 1. Obtener listado de categorias y categorias activas
    @patch("model.category_model.CategoryModel._get_all")
    def test_get_all_success(self, mock_get_all, auth_admin):
        mock_get_all.return_value = [
            {"nombre": "Lubricantes", "descripcion": "Aceites y fluidos", "total_productos": 5}
        ]
        response = auth_admin.get('/api/categories/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.category_model.CategoryModel._get_active")
    def test_get_active_success(self, mock_get_active, client):
        mock_get_active.return_value = [{"nombre": "Frenos", "descripcion": "Discos y pastillas"}]
        response = client.get('/api/categories/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    # 2. Comprobar unicidad de nombre de categoria
    @patch("model.category_model.CategoryModel._nombre_exists", return_value=False)
    def test_check_unique_name_available(self, mock_exists, auth_admin):
        response = auth_admin.get('/api/categories/check-unique?value=Baterias')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is True

    @patch("model.category_model.CategoryModel._nombre_exists", return_value=True)
    def test_check_unique_name_taken(self, mock_exists, auth_admin):
        response = auth_admin.get('/api/categories/check-unique?value=Lubricantes')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["unique"] is False

    # 3. Detalle de categoria por nombre
    @patch("model.category_model.CategoryModel._get_by_nombre")
    def test_get_one_found(self, mock_get_by_nombre, auth_admin):
        mock_get_by_nombre.return_value = {"nombre": "Motor", "descripcion": "Partes de motor"}
        response = auth_admin.get('/api/categories/Motor')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["nombre"] == "Motor"

    @patch("model.category_model.CategoryModel._get_by_nombre", return_value=None)
    def test_get_one_not_found(self, mock_get_by_nombre, auth_admin):
        response = auth_admin.get('/api/categories/Inexistente')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    # 4. Creacion de categoria (POST /)
    def test_create_unauthorized_fails(self, client):
        response = client.post('/api/categories/', json={"nombre": "Suspension"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.category_model.CategoryModel._create", return_value="Suspension")
    @patch("model.category_model.CategoryModel._validate")
    def test_create_json_success(self, mock_validate, mock_create, auth_admin):
        mock_validate.return_value = {"nombre": "Suspension", "descripcion": "Amortiguadores"}
        response = auth_admin.post('/api/categories/', json={"nombre": "Suspension", "descripcion": "Amortiguadores"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["nombre"] == "Suspension"

    @patch("model.category_model.CategoryModel._validate", side_effect=ValidationError({"nombre": "El nombre debe tener al menos 3 caracteres"}))
    def test_create_validation_error(self, mock_validate, auth_admin):
        response = auth_admin.post('/api/categories/', json={"nombre": "A"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "nombre" in json_data["errors"]

    # 5. Modificacion de categoria (PUT /update)
    def test_update_unauthorized_fails(self, client):
        response = client.put('/api/categories/update', json={"nombre": "Suspension"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.category_model.CategoryModel._update_category", return_value=1)
    @patch("model.category_model.CategoryModel._validate")
    def test_update_json_success(self, mock_validate, mock_update, auth_admin):
        mock_validate.return_value = {"nombre": "Suspension Modificada"}
        response = auth_admin.put('/api/categories/update', json={
            "old_nombre": "Suspension", "nombre": "Suspension Modificada"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    # 6. Eliminacion y Toggle (DELETE /delete & PUT /toggle)
    @patch("model.category_model.CategoryModel._soft_delete", return_value=1)
    def test_delete_success(self, mock_soft_delete, auth_admin):
        response = auth_admin.delete('/api/categories/delete', json={"nombre": "Suspension"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_soft_delete.assert_called_once_with("Suspension")

    @patch("model.category_model.CategoryModel._toggle_estado", return_value=1)
    def test_toggle_success(self, mock_toggle, auth_admin):
        response = auth_admin.put('/api/categories/toggle', json={"nombre": "Suspension"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_toggle.assert_called_once_with("Suspension")
