import pytest
from unittest.mock import patch, MagicMock
from model.product_model import ProductModel
from config.validation import ValidationError


class TestProductModelHelpersAndValidation:
    """Pruebas unitarias para getters, setters y validaciones con Data Provider (@pytest.mark.parametrize)."""

    # DATA PROVIDER: Propiedades del modelo de producto
    @pytest.mark.parametrize("prop_name, input_val, expected_val", [
        ("codigo", "  PROD-100  ", "PROD-100"),
        ("nombre", "  Filtro de Aire  ", "Filtro de Aire"),
        ("descripcion", "  Descripcion test  ", "Descripcion test"),
        ("precio", "45.50", 45.50),
        ("precio", 30, 30.0),
    ])
    def test_product_model_properties_data_provider(self, prop_name, input_val, expected_val):
        model = ProductModel()
        setattr(model, prop_name, input_val)
        assert getattr(model, prop_name) == expected_val

    # DATA PROVIDER: Validaciones de campos de registro y edicion de producto
    @pytest.mark.parametrize("data, is_valid, expected_error_field", [
        # Caso valido
        ({
            "codigo": "PROD001", "nombre": "Aceite Sintetico 5W30", "descripcion": "Motor",
            "precio": "35.50", "categoria": "Lubricantes", "marca": "Castrol", "sucursal_ids": [1, 2]
        }, True, None),
        # Codigo muy corto (< 2 chars)
        ({
            "codigo": "A", "nombre": "Aceite Sintetico", "precio": "35.50",
            "categoria": "Lubricantes", "marca": "Castrol", "sucursal_ids": [1]
        }, False, "codigo"),
        # Nombre muy corto (< 3 chars)
        ({
            "codigo": "PROD002", "nombre": "Ac", "precio": "35.50",
            "categoria": "Lubricantes", "marca": "Castrol", "sucursal_ids": [1]
        }, False, "nombre"),
        # Precio invalido / negativo
        ({
            "codigo": "PROD003", "nombre": "Aceite Sintetico", "precio": "-10.00",
            "categoria": "Lubricantes", "marca": "Castrol", "sucursal_ids": [1]
        }, False, "precio"),
        # Sin sucursales seleccionadas
        ({
            "codigo": "PROD004", "nombre": "Aceite Sintetico", "precio": "35.50",
            "categoria": "Lubricantes", "marca": "Castrol", "sucursal_ids": []
        }, False, "sucursal_id"),
        # Formato sucursales no lista
        ({
            "codigo": "PROD005", "nombre": "Aceite Sintetico", "precio": "35.50",
            "categoria": "Lubricantes", "marca": "Castrol", "sucursal_ids": "invalido"
        }, False, "sucursal_id"),
    ])
    def test_validate_data_provider(self, data, is_valid, expected_error_field):
        model = ProductModel()
        with patch.object(ProductModel, "_category_exists", return_value=True), \
             patch.object(ProductModel, "_brand_exists", return_value=True):
            if is_valid:
                clean = model._validate(data)
                assert clean["codigo"] == data["codigo"].upper()
                assert clean["nombre"] == data["nombre"]
                assert clean["precio"] == float(data["precio"])
            else:
                with pytest.raises(ValidationError) as exc_info:
                    model._validate(data)
                assert expected_error_field in exc_info.value.errors


class TestProductModelDatabaseOperations:
    """Pruebas unitarias para consultas, operaciones de persistencia y sincronizacion de sucursales."""

    @patch.object(ProductModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"codigo": "PROD001", "nombre": "Filtro", "precio": 15.0, "stock": 10}
        ]
        model = ProductModel()
        products = model.ejecutar("get_all")

        assert len(products) == 1
        assert products[0]["codigo"] == "PROD001"
        mock_fetch_all.assert_called_once()

    @patch.object(ProductModel, "fetch_all")
    @patch.object(ProductModel, "fetch_one")
    def test_get_all_paginated(self, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.return_value = {"total": 25}
        mock_fetch_all.return_value = [
            {"codigo": "PROD001", "nombre": "Filtro Aceite"}
        ]
        model = ProductModel()
        paginated = model.ejecutar("get_all_paginated", 1, 10, "Filtro")

        assert paginated["total"] == 25
        assert paginated["pages"] == 3
        assert len(paginated["data"]) == 1

    @patch.object(ProductModel, "fetch_all")
    @patch.object(ProductModel, "fetch_one")
    def test_get_active_paginated_with_sort(self, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.return_value = {"total": 5}
        mock_fetch_all.return_value = [
            {"codigo": "PROD001", "nombre": "Bujia", "precio": 5.0}
        ]
        model = ProductModel()
        paginated = model.ejecutar("get_active_paginated", 1, 10, category="Electrico", branch=1, sort="price_asc")

        assert paginated["total"] == 5
        assert len(paginated["data"]) == 1

    @patch.object(ProductModel, "fetch_all")
    def test_get_by_estado(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"codigo": "PROD001", "estado": 1}]
        model = ProductModel()
        result = model.ejecutar("get_by_estado", 1)

        assert len(result) == 1

    @patch.object(ProductModel, "fetch_one")
    def test_get_by_codigo(self, mock_fetch_one):
        mock_fetch_one.return_value = {"codigo": "PROD001", "nombre": "Pastillas"}
        model = ProductModel()
        product = model.ejecutar("get_by_codigo", "PROD001")

        assert product["codigo"] == "PROD001"

    @patch.object(ProductModel, "fetch_all")
    def test_get_by_category_and_brand(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"codigo": "PROD001"}]
        model = ProductModel()

        cat_res = model.ejecutar("get_by_category", "Frenos")
        assert len(cat_res) == 1

        brand_res = model.ejecutar("get_by_brand", "Bosch")
        assert len(brand_res) == 1

    @patch.object(ProductModel, "fetch_all")
    def test_get_by_sucursal(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"codigo": "PROD001", "sucursal_nombre": "Centro"}]
        model = ProductModel()
        res = model.ejecutar("get_by_sucursal", 1)

        assert len(res) == 1

    @patch.object(ProductModel, "fetch_all")
    def test_search(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"codigo": "PROD001", "nombre": "Aceite"}]
        model = ProductModel()
        res = model.ejecutar("search", "Aceite")

        assert len(res) == 1

    @patch.object(ProductModel, "insert")
    @patch.object(ProductModel, "update")
    @patch.object(ProductModel, "fetch_one")
    @patch.object(ProductModel, "fetch_all")
    def test_sync_sucursales(self, mock_fetch_all, mock_fetch_one, mock_update, mock_insert):
        # El producto esta actualmente en sucursal 1 y 2, se pasa [2, 3] -> borra 1, mantiene 2, inserta 3
        mock_fetch_all.return_value = [{"sucursal_id": 1}, {"sucursal_id": 2}]
        mock_fetch_one.side_effect = [{"producto_codigo": "PROD001"}, None]  # 2 existe, 3 no existe

        model = ProductModel()
        model._sync_sucursales("PROD001", [2, 3])

        mock_update.assert_called_once()  # DELETE sucursal 1
        mock_insert.assert_called_once()  # INSERT sucursal 3

    @patch.object(ProductModel, "_columns", return_value={'codigo', 'nombre_producto', 'precio_producto', 'categoria', 'marca', 'imagen_producto'})
    @patch.object(ProductModel, "_sync_sucursales")
    @patch.object(ProductModel, "insert", return_value="PROD001")
    @patch.object(ProductModel, "_get_by_codigo", return_value=None)
    @patch.object(ProductModel, "_validate")
    def test_create_new_product(self, mock_validate, mock_get_by_cod, mock_insert, mock_sync, mock_cols):
        mock_validate.return_value = {
            "codigo": "PROD001", "nombre": "Bomba de Agua", "precio": 60.0,
            "categoria": "Motor", "marca": "GMB", "sucursal_ids": [1]
        }
        model = ProductModel()
        pid = model.ejecutar("create", {"codigo": "PROD001", "nombre": "Bomba de Agua"})

        assert pid == "PROD001"
        mock_insert.assert_called_once()
        mock_sync.assert_called_once_with("PROD001", [1])

    @patch.object(ProductModel, "_reactivar")
    @patch.object(ProductModel, "_apply_update")
    @patch.object(ProductModel, "_get_by_codigo", return_value={"codigo": "PROD001", "estado": 0})
    @patch.object(ProductModel, "_validate")
    def test_create_reactivates_inactive_product(self, mock_validate, mock_get_by_cod, mock_update, mock_reactivar):
        mock_validate.return_value = {
            "codigo": "PROD001", "nombre": "Bomba de Agua", "precio": 60.0, "sucursal_ids": [1]
        }
        model = ProductModel()
        pid = model.ejecutar("create", {"codigo": "PROD001"})

        assert pid == "PROD001"
        mock_reactivar.assert_called_once_with("PROD001")

    @patch.object(ProductModel, "_get_by_codigo", return_value={"codigo": "PROD001", "estado": 1})
    @patch.object(ProductModel, "_validate", return_value={"codigo": "PROD001", "nombre": "Bomba", "precio": 50.0})
    def test_create_already_active_raises_error(self, mock_validate, mock_get):
        model = ProductModel()
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("create", {"codigo": "PROD001"})

        assert "codigo" in exc_info.value.errors

    @patch.object(ProductModel, "_apply_update", return_value=1)
    @patch.object(ProductModel, "_codigo_exists", return_value=False)
    @patch.object(ProductModel, "_validate")
    def test_update_product_success(self, mock_validate, mock_exists, mock_apply):
        mock_validate.return_value = {
            "codigo": "PROD002", "nombre": "Bomba Modificada", "precio": 70.0, "sucursal_ids": [1]
        }
        model = ProductModel()
        res = model.ejecutar("update_product", "PROD001", {"codigo": "PROD002", "nombre": "Bomba Modificada"})

        assert res == 1
        mock_apply.assert_called_once()

    @patch.object(ProductModel, "_codigo_exists", return_value=True)
    @patch.object(ProductModel, "_validate", return_value={"codigo": "PROD002", "nombre": "Bomba", "precio": 50.0})
    def test_update_product_duplicate_code_fails(self, mock_validate, mock_exists):
        model = ProductModel()
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("update_product", "PROD001", {"codigo": "PROD002"})

        assert "codigo" in exc_info.value.errors

    @patch.object(ProductModel, "update", return_value=1)
    def test_soft_delete_and_toggle(self, mock_update):
        model = ProductModel()
        res = model.ejecutar("soft_delete", "PROD001")
        assert res == 1

        toggle_res = model.ejecutar("toggle_estado", "PROD001")
        assert toggle_res == 1

    @patch.object(ProductModel, "fetch_one")
    def test_exists_methods(self, mock_fetch_one):
        model = ProductModel()

        mock_fetch_one.return_value = {"codigo": "PROD001"}
        assert model.ejecutar("codigo_exists", "PROD001") is True

        mock_fetch_one.return_value = None
        assert model.ejecutar("codigo_exists", "PROD999") is False

        mock_fetch_one.return_value = {"nombre_categoria": "Frenos"}
        assert model.ejecutar("category_exists", "Frenos") is True

        mock_fetch_one.return_value = {"nombre_marca": "Bosch"}
        assert model.ejecutar("brand_exists", "Bosch") is True

    def test_ejecutar_invalid_action(self):
        model = ProductModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
