import pytest
from unittest.mock import patch
from model.user_model import UserModel
from config.validation import ValidationError


class TestUserModelProperties:
    """Pruebas unitarias para getters y setters del modelo de usuario."""

    def test_property_setters_strip_whitespace(self):
        model = UserModel()
        model.cedula = "  V-12345678  "
        model.nombre = "  María  "
        model.apellido = "  Delgado  "
        model.email = "  maria@ejemplo.com  "
        model.telefono = "  04161234567  "
        model.direccion = "  Calle Principal  "

        assert model.cedula == "V-12345678"
        assert model.nombre == "María"
        assert model.apellido == "Delgado"
        assert model.email == "maria@ejemplo.com"
        assert model.telefono == "04161234567"
        assert model.direccion == "Calle Principal"

    def test_property_setters_none(self):
        model = UserModel()
        model.cedula = None
        model.nombre = None

        assert model.cedula is None
        assert model.nombre is None


class TestUserModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de usuario."""

    # DATA PROVIDER: Pruebas con formatos de contraseñas válidas e inválidas
    @pytest.mark.parametrize("password, is_valid", [
        ("Clave123!", True),
        ("Admin2026#", True),
        ("Pass.1234", True),
        ("corta1!", False),            # Menos de 8 caracteres
        ("sinmayus1!", False),          # Sin mayúscula
        ("SINMINUS1!", False),          # Sin minúscula
        ("SinNumero!", False),          # Sin número
        ("SinEspecial123", False),     # Sin carácter especial
    ])
    @patch.object(UserModel, "_role_exists", return_value=True)
    def test_validate_password_data_provider(self, mock_role_exists, password, is_valid):
        model = UserModel()
        data = {
            "nombre": "María",
            "apellido": "Delgado",
            "cedula": "V-12345678",
            "email": "maria@ejemplo.com",
            "rol_id": 1,
            "tipo": "empleado",
            "password": password,
            "confirm_password": password
        }
        if is_valid:
            clean = model.ejecutar("validate", data, require_password=True)
            assert clean["password"] == password
        else:
            with pytest.raises(ValidationError) as exc_info:
                model.ejecutar("validate", data, require_password=True)
            assert "password" in exc_info.value.errors

    # DATA PROVIDER: Pruebas con contraseñas que no coinciden en confirmación
    @pytest.mark.parametrize("password, confirm_password", [
        ("Clave123!", "Clave1234!"),
        ("Admin2026#", "admin2026#"),
    ])
    @patch.object(UserModel, "_role_exists", return_value=True)
    def test_validate_password_mismatch_data_provider(self, mock_role_exists, password, confirm_password):
        model = UserModel()
        data = {
            "nombre": "María",
            "apellido": "Delgado",
            "cedula": "V-12345678",
            "email": "maria@ejemplo.com",
            "rol_id": 1,
            "tipo": "empleado",
            "password": password,
            "confirm_password": confirm_password
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("validate", data, require_password=True)
        assert "confirm_password" in exc_info.value.errors

    # DATA PROVIDER: Pruebas de rol obligatorio
    @pytest.mark.parametrize("invalid_rol_id", [None, "", 0, "0"])
    def test_validate_missing_role_data_provider(self, invalid_rol_id):
        model = UserModel()
        data = {
            "nombre": "María",
            "apellido": "Delgado",
            "cedula": "V-12345678",
            "email": "maria@ejemplo.com",
            "rol_id": invalid_rol_id,
            "tipo": "empleado"
        }
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("validate", data)
        assert "rol_id" in exc_info.value.errors


class TestUserModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de usuario."""

    @patch.object(UserModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "María", "apellido": "Delgado", "email": "maria@ejemplo.com", "estado": 1}
        ]
        model = UserModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "María"
        mock_fetch_all.assert_called_once()

    @patch.object(UserModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "nombre": "María", "cedula": "V-12345678"}
        model = UserModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        assert result["nombre"] == "María"
        mock_fetch_one.assert_called_once()

    @patch.object(UserModel, "update")
    def test_update_status(self, mock_update):
        mock_update.return_value = 1
        model = UserModel()
        result = model.ejecutar("update_status", 1, 0)

        assert result == 1
        mock_update.assert_called_once()

    def test_update_status_invalid_value_raises_error(self):
        model = UserModel()
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("update_status", 1, 99)
        assert "estado" in exc_info.value.errors

    @patch.object(UserModel, "fetch_one")
    def test_soft_delete_last_admin_fails(self, mock_fetch_one):
        # Simular que el usuario es Administrador y es el único activo
        mock_fetch_one.side_effect = [
            {"id": 1},                 # es admin
            {"total": 1}               # total administradores = 1
        ]
        model = UserModel()
        result = model.ejecutar("soft_delete", 1)

        assert result is False

    def test_ejecutar_invalid_action(self):
        model = UserModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")
        assert "Accion no permitida" in str(exc_info.value)
