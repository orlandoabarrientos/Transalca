import pytest
from unittest.mock import patch
from model.role_model import RoleModel
from config.validation import ValidationError


class TestRoleModelProperties:
    """Pruebas unitarias para getters y setters del modelo de rol."""

    def test_property_setters_strip_whitespace(self):
        model = RoleModel()
        model.nombre = "  Supervisión  "
        model.descripcion = "  Rol con permisos de auditoría  "

        assert model.nombre == "Supervisión"
        assert model.descripcion == "Rol con permisos de auditoría"

    def test_property_setters_none(self):
        model = RoleModel()
        model.nombre = None
        model.descripcion = None

        assert model.nombre is None
        assert model.descripcion is None


class TestRoleModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de rol."""

    # DATA PROVIDER: Nombres de roles válidos
    @pytest.mark.parametrize("valid_nombre", [
        "Administrador",
        "Mecánico Senior",
        "Cajero Principal",
        "Vendedor de Campo",
    ])
    def test_validate_valid_nombre_data_provider(self, valid_nombre):
        model = RoleModel()
        data = {
            "nombre": valid_nombre,
            "descripcion": "Descripción opcional del rol"
        }
        clean = model._validate(data)
        assert clean["nombre"] == valid_nombre

    # DATA PROVIDER: Nombres de roles inválidos
    @pytest.mark.parametrize("invalid_nombre", [
        "",         # Nombre vacío
        "AB",       # Menor a 3 caracteres
    ])
    def test_validate_invalid_nombre_data_provider(self, invalid_nombre):
        model = RoleModel()
        data = {
            "nombre": invalid_nombre
        }
        with pytest.raises(ValidationError) as exc_info:
            model._validate(data)
        assert "nombre" in exc_info.value.errors


class TestRoleModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de roles y permisos."""

    @patch.object(RoleModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "Administrador", "descripcion": "Acceso total", "estado": 1}
        ]
        model = RoleModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "Administrador"
        mock_fetch_all.assert_called_once()

    @patch.object(RoleModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "nombre": "Administrador"}
        model = RoleModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        mock_fetch_one.assert_called_once()

    @patch.object(RoleModel, "_get_by_id")
    def test_soft_delete_administrator_protected(self, mock_get_by_id):
        mock_get_by_id.return_value = {"id": 1, "nombre": "Administrador", "estado": 1}

        model = RoleModel()
        result = model.ejecutar("soft_delete", 1)

        assert result is False

    @patch.object(RoleModel, "update")
    @patch.object(RoleModel, "_get_by_id")
    def test_soft_delete_custom_role(self, mock_get_by_id, mock_update):
        mock_get_by_id.return_value = {"id": 2, "nombre": "Asistente", "estado": 1}
        mock_update.return_value = 1

        model = RoleModel()
        result = model.ejecutar("soft_delete", 2)

        assert result == 0
        mock_update.assert_called_once()

    @patch.object(RoleModel, "fetch_all")
    def test_get_permissions(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 10, "rol_id": 1, "modulo": "clientes", "crear": 1, "leer": 1, "actualizar": 1, "eliminar": 1}
        ]
        model = RoleModel()
        perms = model.ejecutar("get_permissions", 1)

        assert len(perms) == 1
        assert perms[0]["modulo"] == "clientes"

    def test_ejecutar_invalid_action(self):
        model = RoleModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
