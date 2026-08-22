import pytest
from unittest.mock import patch
from model.bitacora_model import BitacoraModel


class TestBitacoraModelHelpers:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para la función helper _request_limit del controlador de bitácora."""

    # DATA PROVIDER: Normalización de límites de consulta (entre 1 y 100)
    @pytest.mark.parametrize("limit_input, expected_limit", [
        (50, 50),
        (200, 100),   # Supera el máximo -> ajusta a 100
        (-10, 1),     # Menor a 1 -> ajusta a 1
        ("30", 30),   # Cadena convertible a entero
        ("invalido", 100), # Texto no entero -> valor por defecto
    ])
    def test_request_limit_data_provider(self, limit_input, expected_limit):
        from controller.bitacora_controller import _request_limit
        with flask_app.test_request_context(f"/?limit={limit_input}"):
            assert _request_limit() == expected_limit


class TestBitacoraModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para registro y consulta de eventos de bitácora."""

    @patch.object(BitacoraModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "usuario_id": 1, "nombre": "Admin", "apellido": "Sistema", "accion": "LOGIN", "modulo": "auth"}
        ]
        model = BitacoraModel()
        logs = model.ejecutar("get_all", 50, 0)

        assert len(logs) == 1
        assert logs[0]["accion"] == "LOGIN"
        mock_fetch_all.assert_called_once()

    @patch.object(BitacoraModel, "fetch_all")
    def test_get_by_user(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "usuario_id": 5, "nombre": "Carlos", "apellido": "Mendoza", "accion": "UPDATE"}
        ]
        model = BitacoraModel()
        logs = model.ejecutar("get_by_user", 5, 50)

        assert len(logs) == 1
        assert logs[0]["usuario_id"] == 5

    @patch.object(BitacoraModel, "fetch_all")
    def test_get_by_module(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 2, "modulo": "clientes", "accion": "CREATE_CLIENT"}
        ]
        model = BitacoraModel()
        logs = model.ejecutar("get_by_module", "clientes", 50)

        assert len(logs) == 1
        assert logs[0]["modulo"] == "clientes"

    @patch.object(BitacoraModel, "insert")
    def test_log_action(self, mock_insert):
        mock_insert.return_value = 100
        model = BitacoraModel()
        log_id = model.ejecutar("log_action", 1, "INSERT", "proveedores", "Registro de nuevo proveedor", "192.168.1.10")

        assert log_id == 100
        mock_insert.assert_called_once()

    @patch.object(BitacoraModel, "fetch_one")
    def test_count_all(self, mock_fetch_one):
        mock_fetch_one.return_value = {"total": 250}
        model = BitacoraModel()
        total = model.ejecutar("count_all")

        assert total == 250

    @patch.object(BitacoraModel, "fetch_all")
    def test_search(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 3, "accion": "DELETE", "modulo": "usuarios", "descripcion": "Eliminación de usuario"}
        ]
        model = BitacoraModel()
        results = model.ejecutar("search", "usuario")

        assert len(results) == 1
        assert results[0]["accion"] == "DELETE"

    def test_ejecutar_invalid_action(self):
        model = BitacoraModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)


from app import app as flask_app
