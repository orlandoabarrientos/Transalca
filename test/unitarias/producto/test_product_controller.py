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


class TestProductController:
    """Pruebas de integracion de rutas API para gestion de productos."""

    # 1. Obtener listado de productos y filtros de estado / paginacion
    @patch("model.product_model.ProductModel._get_all")
    def test_get_all_unfiltered_success(self, mock_get_all, auth_admin):
        mock_get_all.return_value = [
            {"codigo": "PROD001", "nombre": "Pastillas de Freno", "precio": 25.00}
        ]
        response = auth_admin.get('/api/products/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.product_model.ProductModel._get_by_estado")
    def test_get_all_with_estado_filter(self, mock_get_by_estado, auth_admin):
        mock_get_by_estado.return_value = [
            {"codigo": "PROD001", "nombre": "Pastillas de Freno", "estado": 1}
        ]
        response = auth_admin.get('/api/products/?estado=1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_get_by_estado.assert_called_once_with(1)

    def test_get_all_with_invalid_estado_fails(self, auth_admin):
        response = auth_admin.get('/api/products/?estado=invalido')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    @patch("model.product_model.ProductModel._get_all_paginated")
    def test_get_all_paginated(self, mock_get_paginated, auth_admin):
        mock_get_paginated.return_value = {
            "data": [{"codigo": "PROD001", "nombre": "Filtro"}],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "pages": 1
        }
        response = auth_admin.get('/api/products/?page=1&per_page=10&q=Filtro')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["total"] == 1

    # 2. Productos activos y catalogo (Ruta publica)
    @patch("model.product_model.ProductModel._get_active")
    def test_get_active_unpaginated(self, mock_get_active, client):
        mock_get_active.return_value = [{"codigo": "PROD001", "nombre": "Amortiguador"}]
        response = client.get('/api/products/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.product_model.ProductModel._get_active_paginated")
    def test_get_active_paginated_with_filters(self, mock_get_active_pag, client):
        mock_get_active_pag.return_value = {
            "data": [{"codigo": "PROD001", "nombre": "Amortiguador"}],
            "total": 1,
            "page": 1,
            "per_page": 30,
            "pages": 1
        }
        response = client.get('/api/products/active?page=1&per_page=30&category=Suspension&branch=1&sort=price_asc')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["page"] == 1

    # 3. Comprobar unicidad de codigo
    @patch("model.product_model.ProductModel._codigo_exists", return_value=False)
    def test_check_unique_code_available(self, mock_exists, auth_admin):
        response = auth_admin.get('/api/products/check-unique?value=PROD999')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["exists"] is False

    def test_check_unique_missing_code_fails(self, auth_admin):
        response = auth_admin.get('/api/products/check-unique')
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    # 4. Detalle de producto por codigo
    @patch("model.product_model.ProductModel._get_by_codigo")
    def test_get_one_found(self, mock_get_by_codigo, auth_admin):
        mock_get_by_codigo.return_value = {
            "codigo": "PROD001", "nombre": "Bujia", "precio": 5.00
        }
        response = auth_admin.get('/api/products/detail/PROD001')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["codigo"] == "PROD001"

    @patch("model.product_model.ProductModel._get_by_codigo", return_value=None)
    def test_get_one_not_found(self, mock_get_by_codigo, auth_admin):
        response = auth_admin.get('/api/products/detail/NOEXISTE')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    # 5. Filtrados especificos: categoria, marca, busqueda, sucursal
    @patch("model.product_model.ProductModel._get_by_category")
    def test_get_by_category(self, mock_get_cat, auth_admin):
        mock_get_cat.return_value = [{"codigo": "PROD001", "categoria": "Frenos"}]
        response = auth_admin.get('/api/products/category/Frenos')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.product_model.ProductModel._get_by_brand")
    def test_get_by_brand(self, mock_get_brand, auth_admin):
        mock_get_brand.return_value = [{"codigo": "PROD001", "marca": "Bosch"}]
        response = auth_admin.get('/api/products/brand/Bosch')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.product_model.ProductModel._search")
    def test_search_products(self, mock_search, auth_admin):
        mock_search.return_value = [{"codigo": "PROD001", "nombre": "Aceite 10W40"}]
        response = auth_admin.get('/api/products/search?q=Aceite')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.product_model.ProductModel._get_by_sucursal")
    def test_get_by_sucursal(self, mock_get_suc, auth_admin):
        mock_get_suc.return_value = [{"codigo": "PROD001", "sucursal_nombre": "Centro"}]
        response = auth_admin.get('/api/products/sucursal/1')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    # 6. Registro de producto (POST /)
    def test_create_unauthorized_fails(self, client):
        response = client.post('/api/products/', json={"codigo": "PROD001"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.product_model.ProductModel._create", return_value="PROD001")
    @patch("model.product_model.ProductModel._validate")
    def test_create_json_success(self, mock_validate, mock_create, auth_admin):
        mock_validate.return_value = {
            "codigo": "PROD001", "nombre": "Correa de Tiempo", "precio": 45.00
        }
        response = auth_admin.post('/api/products/', json={
            "codigo": "PROD001",
            "nombre": "Correa de Tiempo",
            "precio": "45.00",
            "categoria": "Motor",
            "marca": "Gates",
            "sucursal_ids": [1]
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["codigo"] == "PROD001"

    @patch("model.product_model.ProductModel._create", return_value="PROD001")
    @patch("model.product_model.ProductModel._validate")
    def test_create_form_with_image_success(self, mock_validate, mock_create, auth_admin):
        mock_validate.return_value = {"codigo": "PROD001", "nombre": "Correa de Tiempo"}
        with patch("controller.product_controller._save_image", return_value=("prod_PROD001_12345.png", None)):
            data = {
                'codigo': 'PROD001',
                'nombre': 'Correa de Tiempo',
                'precio': '45.00',
                'categoria': 'Motor',
                'marca': 'Gates',
                'sucursal_ids': ['1'],
                'imagen': (io.BytesIO(b"fake image data"), 'foto.png')
            }
            response = auth_admin.post('/api/products/', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

            assert response.status_code == 200
            assert json_data["status"] == "success"

    @patch("model.product_model.ProductModel._validate")
    def test_create_form_with_invalid_image_fails(self, mock_validate, auth_admin):
        mock_validate.return_value = {"codigo": "PROD001", "nombre": "Correa de Tiempo"}
        with patch("controller.product_controller._save_image", return_value=(None, "Solo se permiten imagenes png, jpg, jpeg o webp.")):
            data = {
                'codigo': 'PROD001',
                'nombre': 'Correa de Tiempo',
                'imagen': (io.BytesIO(b"bad exe data"), 'file.exe')
            }
            response = auth_admin.post('/api/products/', data=data, content_type='multipart/form-data')
            json_data = response.get_json()

            assert response.status_code == 400
            assert json_data["status"] == "error"
            assert "imagen" in json_data["errors"]

    @patch("model.product_model.ProductModel._validate", side_effect=ValidationError({"nombre": "El nombre es obligatorio"}))
    def test_create_validation_error(self, mock_validate, auth_admin):
        response = auth_admin.post('/api/products/', json={"codigo": "PROD001"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"
        assert "nombre" in json_data["errors"]

    # 7. Modificacion de producto (PUT /update)
    def test_update_unauthorized_fails(self, client):
        response = client.put('/api/products/update', json={"codigo": "PROD001"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.product_model.ProductModel._update_product", return_value=1)
    @patch("model.product_model.ProductModel._validate")
    def test_update_json_success(self, mock_validate, mock_update, auth_admin):
        mock_validate.return_value = {"codigo": "PROD001", "nombre": "Correa Modificada"}
        response = auth_admin.put('/api/products/update', json={
            "old_codigo": "PROD001",
            "codigo": "PROD001",
            "nombre": "Correa Modificada",
            "precio": "50.00",
            "categoria": "Motor",
            "marca": "Gates",
            "sucursal_ids": [1]
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.product_model.ProductModel._validate", side_effect=ValidationError({"codigo": "Este codigo ya esta registrado."}))
    def test_update_validation_error(self, mock_validate, auth_admin):
        response = auth_admin.put('/api/products/update', json={"old_codigo": "PROD001", "codigo": "PROD002"})
        json_data = response.get_json()

        assert response.status_code == 400
        assert json_data["status"] == "error"

    # 8. Desactivacion / Cambio de estado (PUT /toggle)
    def test_toggle_unauthorized_fails(self, client):
        response = client.put('/api/products/toggle', json={"codigo": "PROD001"})
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.product_model.ProductModel._get_by_codigo", return_value=None)
    def test_toggle_not_found(self, mock_get, auth_admin):
        response = auth_admin.put('/api/products/toggle', json={"codigo": "PROD999"})
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    @patch("model.product_model.ProductModel._get_by_codigo", return_value={"codigo": "PROD001", "estado": 1})
    @patch("model.product_model.ProductModel._soft_delete", return_value=1)
    def test_toggle_success(self, mock_delete, mock_get, auth_admin):
        response = auth_admin.put('/api/products/toggle', json={"codigo": "PROD001"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        mock_delete.assert_called_once_with("PROD001")
