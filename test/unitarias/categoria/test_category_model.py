import pytest
from unittest.mock import patch, MagicMock
from model.category_model import CategoryModel
from config.validation import ValidationError


class TestCategoryModelHelpersAndValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para propiedades y validaciones de categorias."""

    # DATA PROVIDER: Propiedades del modelo de categoria
    @pytest.mark.parametrize("prop_name, input_val, expected_val", [
        ("nombre", "  Lubricantes  ", "Lubricantes"),
        ("descripcion", "  Aceites de motor  ", "Aceites de motor"),
    ])
    def test_category_properties_data_provider(self, prop_name, input_val, expected_val):
        model = CategoryModel()
        setattr(model, prop_name, input_val)
        assert getattr(model, prop_name) == expected_val

    # DATA PROVIDER: Validaciones de campos de categoria
    @pytest.mark.parametrize("data, is_valid, expected_error_field", [
        # Caso valido
        ({"nombre": "Frenos", "descripcion": "Sistemas de frenado"}, True, None),
        # Nombre muy corto (< 3 chars)
        ({"nombre": "Fr", "descripcion": "Sistemas de frenado"}, False, "nombre"),
        # Nombre vacio
        ({"nombre": "", "descripcion": "Sistemas de frenado"}, False, "nombre"),
        # Nombre excesivamente largo (> 30 chars)
        ({"nombre": "A" * 35, "descripcion": "Valido"}, False, "nombre"),
        # Descripcion excesivamente larga (> 150 chars)
        ({"nombre": "Frenos", "descripcion": "D" * 155}, False, "descripcion"),
    ])
    def test_validate_data_provider(self, data, is_valid, expected_error_field):
        model = CategoryModel()
        if is_valid:
            clean = model._validate(data)
            assert clean["nombre"] == data["nombre"]
        else:
            with pytest.raises(ValidationError) as exc_info:
                model._validate(data)
            assert expected_error_field in exc_info.value.errors


class TestCategoryModelDatabaseOperations:
    """Pruebas unitarias para consultas y operaciones CRUD de categorias."""

    @patch.object(CategoryModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"nombre": "Lubricantes", "descripcion": "Aceites", "total_productos": 10}
        ]
        model = CategoryModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["nombre"] == "Lubricantes"

    @patch.object(CategoryModel, "fetch_all")
    def test_get_active(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"nombre": "Frenos", "descripcion": "Pastillas"}
        ]
        model = CategoryModel()
        result = model.ejecutar("get_active")

        assert len(result) == 1
        assert result[0]["nombre"] == "Frenos"

    @patch.object(CategoryModel, "fetch_one")
    def test_get_by_nombre(self, mock_fetch_one):
        mock_fetch_one.return_value = {"nombre": "Motor", "descripcion": "Partes de motor"}
        model = CategoryModel()
        result = model.ejecutar("get_by_nombre", "Motor")

        assert result["nombre"] == "Motor"

    @patch.object(CategoryModel, "insert", return_value="Suspension")
    @patch.object(CategoryModel, "_get_by_nombre", return_value=None)
    @patch.object(CategoryModel, "_validate")
    def test_create_new_category(self, mock_validate, mock_get_by_nom, mock_insert):
        mock_validate.return_value = {"nombre": "Suspension", "descripcion": "Amortiguadores"}
        model = CategoryModel()
        nombre = model.ejecutar("create", {"nombre": "Suspension"})

        assert nombre == "Suspension"
        mock_insert.assert_called_once()

    @patch.object(CategoryModel, "update", return_value=1)
    @patch.object(CategoryModel, "_get_by_nombre", return_value={"nombre": "Suspension", "estado": 0})
    @patch.object(CategoryModel, "_validate")
    def test_create_reactivate_inactive_category(self, mock_validate, mock_get, mock_update):
        mock_validate.return_value = {"nombre": "Suspension", "descripcion": "Amortiguadores"}
        model = CategoryModel()
        nombre = model.ejecutar("create", {"nombre": "Suspension"})

        assert nombre == "Suspension"
        mock_update.assert_called_once()

    @patch.object(CategoryModel, "_get_by_nombre", return_value={"nombre": "Suspension", "estado": 1})
    @patch.object(CategoryModel, "_validate", return_value={"nombre": "Suspension"})
    def test_create_already_active_raises_error(self, mock_validate, mock_get):
        model = CategoryModel()
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", {"nombre": "Suspension"})

        assert "nombre" in exc_info.value.errors

    @patch.object(CategoryModel, "update", return_value=1)
    @patch.object(CategoryModel, "_nombre_exists", return_value=False)
    @patch.object(CategoryModel, "_validate")
    def test_update_category_success(self, mock_validate, mock_exists, mock_update):
        mock_validate.return_value = {"nombre": "Suspension Modificada", "descripcion": "Desc"}
        model = CategoryModel()
        res = model.ejecutar("update_category", "Suspension", {"nombre": "Suspension Modificada"})

        assert res == 1
        mock_update.assert_called_once()

    @patch.object(CategoryModel, "_nombre_exists", return_value=True)
    @patch.object(CategoryModel, "_validate", return_value={"nombre": "Frenos"})
    def test_update_category_duplicate_name_fails(self, mock_validate, mock_exists):
        model = CategoryModel()
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("update_category", "Suspension", {"nombre": "Frenos"})

        assert "nombre" in exc_info.value.errors

    @patch.object(CategoryModel, "update", return_value=1)
    def test_soft_delete_and_toggle(self, mock_update):
        model = CategoryModel()
        res = model.ejecutar("soft_delete", "Frenos")
        assert res == 1

        toggle_res = model.ejecutar("toggle_estado", "Frenos")
        assert toggle_res == 1

    @patch.object(CategoryModel, "fetch_one")
    def test_nombre_exists(self, mock_fetch_one):
        model = CategoryModel()

        mock_fetch_one.return_value = {"nombre_categoria": "Frenos"}
        assert model.ejecutar("nombre_exists", "Frenos") is True

        mock_fetch_one.return_value = None
        assert model.ejecutar("nombre_exists", "NoExiste") is False

    @patch.object(CategoryModel, "update", return_value=1)
    def test_reactivar(self, mock_update):
        model = CategoryModel()
        res = model.ejecutar("reactivar", "Frenos")
        assert res == 1

    def test_ejecutar_invalid_action(self):
        model = CategoryModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
