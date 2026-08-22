import pytest
from unittest.mock import patch
from model.modulo_model import ModuloModel
from config.validation import ValidationError


class TestModuloModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para la clave y ruta de módulos."""

    # DATA PROVIDER: Pruebas con claves de módulo válidas (SLUG)
    @pytest.mark.parametrize("valid_nombre, valid_ruta", [
        ("ordenes_compra", "/admin/ordenes-compra"),
        ("clientes", "/admin/clientes"),
        ("gestion_inventario_1", "/admin/inventario"),
    ])
    @patch.object(ModuloModel, "_ruta_exists", return_value=False)
    @patch.object(ModuloModel, "_nombre_exists", return_value=False)
    def test_validate_valid_module_data_provider(
        self, mock_name_exists, mock_route_exists, valid_nombre, valid_ruta
    ):
        model = ModuloModel()
        data = {
            "nombre": valid_nombre,
            "titulo": "Título de Prueba",
            "ruta": valid_ruta,
            "grupo": "Sistema"
        }
        clean = model._validate(data)
        assert clean["nombre"] == valid_nombre
        assert clean["ruta"] == valid_ruta

    # DATA PROVIDER: Pruebas con claves de módulo inválidas
    @pytest.mark.parametrize("invalid_nombre", [
        "Modulo Con Espacios",
        "CLAVE-MAYUSCULA",
        "123_inicial_numero",
        "",
    ])
    def test_validate_invalid_slug_data_provider(self, invalid_nombre):
        model = ModuloModel()
        data = {
            "nombre": invalid_nombre,
            "titulo": "Título de Prueba",
            "ruta": "/admin/prueba",
            "grupo": "Sistema"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "nombre" in exc_info.value.errors

    # DATA PROVIDER: Pruebas con rutas de módulo inválidas
    @pytest.mark.parametrize("invalid_ruta", [
        "admin/sin_slash_inicial",
        "http://sitio_externo.com",
        "/ruta con espacios",
        "",
    ])
    def test_validate_invalid_route_data_provider(self, invalid_ruta):
        model = ModuloModel()
        data = {
            "nombre": "modulo_prueba",
            "titulo": "Título de Prueba",
            "ruta": invalid_ruta,
            "grupo": "Sistema"
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "ruta" in exc_info.value.errors


class TestModuloModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones del módulo dinámico de módulos."""

    @patch.object(ModuloModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "clientes", "titulo": "Clientes", "ruta": "/admin/clientes", "estado": 1}
        ]
        model = ModuloModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "clientes"
        mock_fetch_all.assert_called_once()

    @patch.object(ModuloModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "nombre": "clientes", "titulo": "Clientes"}
        model = ModuloModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()

    @patch.object(ModuloModel, "fetch_all")
    def test_get_sidebar_modules(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"nombre": "clientes", "titulo": "Clientes", "ruta": "/admin/clientes", "icono": "bi bi-people"}
        ]
        model = ModuloModel()
        result = model.ejecutar("get_sidebar_modules")

        assert len(result) == 1
        assert result[0]["icono"] == "bi bi-people"

    @patch.object(ModuloModel, "update")
    @patch.object(ModuloModel, "_get_by_id")
    def test_soft_delete(self, mock_get_by_id, mock_update):
        mock_get_by_id.return_value = {"id": 1, "nombre": "clientes"}
        mock_update.return_value = 1

        model = ModuloModel()
        result = model.ejecutar("soft_delete", 1)

        assert result == 0
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = ModuloModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
