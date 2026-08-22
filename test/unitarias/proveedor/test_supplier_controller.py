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


class TestSupplierController:
    """Pruebas de integración de rutas API para proveedores."""

    @patch("model.supplier_model.SupplierModel._get_all")
    def test_get_all_suppliers(self, mock_get_all, auth_client):
        mock_get_all.return_value = [
            {"rif": "J-12345678-9", "nombre": "Proveedor Repuestos C.A.", "telefono": "04121234567"}
        ]
        response = auth_client.get('/api/suppliers/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.supplier_model.SupplierModel._get_active")
    def test_get_active_suppliers(self, mock_get_active, auth_client):
        mock_get_active.return_value = [
            {"rif": "J-12345678-9", "nombre": "Proveedor Repuestos C.A."}
        ]
        response = auth_client.get('/api/suppliers/active')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    @patch("model.supplier_model.SupplierModel._get_by_rif")
    def test_get_one_supplier_found(self, mock_get_by_rif, auth_client):
        mock_get_by_rif.return_value = {"rif": "J-12345678-9", "nombre": "Proveedor Repuestos C.A."}
        response = auth_client.get('/api/suppliers/J-12345678-9')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["data"]["rif"] == "J-12345678-9"

    @patch("model.supplier_model.SupplierModel._get_by_rif")
    def test_get_one_supplier_not_found(self, mock_get_by_rif, auth_client):
        mock_get_by_rif.return_value = None
        response = auth_client.get('/api/suppliers/J-99999999-9')
        json_data = response.get_json()

        assert response.status_code == 404
        assert json_data["status"] == "error"

    def test_create_unauthorized_fails(self, client):
        response = client.post('/api/suppliers/', json={
            "rif": "J-123456789",
            "nombre": "Proveedor Repuestos C.A."
        })
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.supplier_model.SupplierModel._create")
    def test_create_authorized_success(self, mock_create, auth_client):
        mock_create.return_value = "J-12345678-9"
        response = auth_client.post('/api/suppliers/', json={
            "rif": "J-123456789",
            "nombre": "Proveedor Repuestos C.A."
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["rif"] == "J-12345678-9"

    @patch("model.supplier_model.SupplierModel._soft_delete")
    @patch("model.supplier_model.SupplierModel._get_by_rif")
    def test_toggle_supplier_success(self, mock_get_by_rif, mock_soft_delete, auth_client):
        mock_get_by_rif.return_value = {"rif": "J-12345678-9", "nombre": "Proveedor C.A."}
        mock_soft_delete.return_value = 1

        response = auth_client.put('/api/suppliers/toggle', json={"rif": "J-12345678-9"})
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
