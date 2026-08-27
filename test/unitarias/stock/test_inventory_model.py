import pytest
from unittest.mock import patch, MagicMock
from model.inventory_model import InventoryModel
from config.validation import ValidationError


class TestInventoryModelHelpers:
    """Pruebas unitarias para metodos auxiliares del modelo de inventario/stock."""

    @patch.object(InventoryModel, "fetch_one")
    def test_get_low_stock_threshold_from_config(self, mock_fetch_one):
        mock_fetch_one.return_value = {"valor": "8"}
        model = InventoryModel()
        assert model._get_low_stock_threshold() == 8

    @patch.object(InventoryModel, "fetch_one", return_value=None)
    def test_get_low_stock_threshold_default(self, mock_fetch_one):
        model = InventoryModel()
        assert model._get_low_stock_threshold() == 5

    @patch.object(InventoryModel, "fetch_one")
    def test_client_name_found_in_usuarios(self, mock_fetch_one):
        mock_fetch_one.return_value = {"nombre": "Ana", "apellido": "Gomez"}
        model = InventoryModel()
        name = model._client_name("V-12345678")
        assert name == "Ana Gomez"

    @patch.object(InventoryModel, "fetch_one")
    def test_client_name_found_in_cliente_table(self, mock_fetch_one):
        mock_fetch_one.side_effect = [None, {"nombre_cliente": "Empresa ABC"}]
        model = InventoryModel()
        name = model._client_name("J-12345678-0")
        assert name == "Empresa ABC"

    @patch.object(InventoryModel, "fetch_one", return_value=None)
    def test_client_name_not_found(self, mock_fetch_one):
        model = InventoryModel()
        name = model._client_name("V-99999999")
        assert name == "N/A"


class TestInventoryModelValidationAndStockUpdates:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones y operaciones de stock."""

    # DATA PROVIDER: Validacion de datos de actualizacion de stock
    @pytest.mark.parametrize("data, is_valid, expected_error_key", [
        ({"producto_codigo": "PROD001", "stock": 10, "sucursal_id": 1}, True, None),
        ({"producto_codigo": "PROD001", "stock": "0", "sucursal_id": 1}, True, None),
        ({"producto_codigo": "", "stock": 10}, False, "producto_codigo"),
        ({"producto_codigo": "PROD001", "stock": -5}, False, "stock"),
        ({"producto_codigo": "PROD001", "stock": "invalido"}, False, "stock"),
    ])
    def test_update_stock_validation_data_provider(self, data, is_valid, expected_error_key):
        model = InventoryModel()
        if is_valid:
            with patch.object(InventoryModel, "fetch_one", return_value={"producto_codigo": "PROD001"}), \
                 patch.object(InventoryModel, "update", return_value=1), \
                 patch.object(InventoryModel, "_check_low_stock_and_notify", return_value=0):
                res = model._update_stock(data)
                assert res == 1
        else:
            with pytest.raises(ValidationError) as exc_info:
                model._update_stock(data)
            assert expected_error_key in exc_info.value.errors

    @patch.object(InventoryModel, "insert", return_value=1)
    @patch.object(InventoryModel, "fetch_one", return_value=None)
    @patch.object(InventoryModel, "_check_low_stock_and_notify")
    def test_update_stock_inserts_new_branch_record(self, mock_notify, mock_fetch_one, mock_insert):
        model = InventoryModel()
        data = {"producto_codigo": "PROD001", "sucursal_id": 2, "stock": 15}
        res = model._update_stock(data)

        assert res == 1
        mock_insert.assert_called_once()

    @patch.object(InventoryModel, "update", return_value=1)
    def test_update_min_stock(self, mock_update):
        model = InventoryModel()
        res = model.ejecutar("update_min_stock", "PROD001", 10, sucursal_id=1)
        assert res == 1
        mock_update.assert_called_once()

    @patch.object(InventoryModel, "_get_low_stock_threshold", return_value=5)
    @patch.object(InventoryModel, "_get_low_stock")
    def test_check_low_stock_and_notify(self, mock_get_low, mock_threshold):
        mock_get_low.return_value = [
            {"codigo": "PROD001", "producto_nombre": "Filtro", "stock": 2, "stock_minimo": 5, "sucursal_nombre": "Central"}
        ]
        with patch("model.inventory_model.NotificationModel.ejecutar", return_value=1) as mock_notify:
            model = InventoryModel()
            notified = model._check_low_stock_and_notify("PROD001")

            assert notified == 1
            mock_notify.assert_called_once()


class TestInventoryModelQueries:
    """Pruebas unitarias para consultas y paginacion de inventario y detalle de ordenes de venta."""

    @patch.object(InventoryModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"codigo": "PROD001", "stock": 15}]
        model = InventoryModel()
        res = model.ejecutar("get_all")

        assert len(res) == 1

    @patch.object(InventoryModel, "fetch_all")
    def test_get_by_sucursal(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"codigo": "PROD001", "sucursal_id": 1, "stock": 10}]
        model = InventoryModel()
        res = model.ejecutar("get_by_sucursal", 1)

        assert len(res) == 1

    @patch.object(InventoryModel, "fetch_all")
    @patch.object(InventoryModel, "fetch_one")
    def test_get_paginated(self, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.return_value = {"total": 20}
        mock_fetch_all.return_value = [{"codigo": "PROD001", "stock": 10}]
        model = InventoryModel()
        pag = model.ejecutar("get_paginated", 1, 10, sucursal_id=1, q="Filtro")

        assert pag["total"] == 20
        assert pag["pages"] == 2
        assert len(pag["data"]) == 1

    @patch.object(InventoryModel, "fetch_all")
    @patch.object(InventoryModel, "fetch_one")
    def test_get_low_stock(self, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.return_value = {"valor": "5"}
        mock_fetch_all.return_value = [{"codigo": "PROD001", "stock": 1}]
        model = InventoryModel()
        low = model.ejecutar("get_low_stock", "PROD001")

        assert len(low) == 1

    @patch.object(InventoryModel, "_client_name", return_value="Carlos Mendoza")
    @patch.object(InventoryModel, "fetch_all")
    def test_get_sales_orders(self, mock_fetch_all, mock_cname):
        mock_fetch_all.return_value = [
            {"id": 1, "cliente_cedula": "V-12345678", "total": 200.0}
        ]
        model = InventoryModel()
        orders = model.ejecutar("get_sales_orders")

        assert len(orders) == 1
        assert orders[0]["cliente_nombre"] == "Carlos Mendoza"

    @patch.object(InventoryModel, "fetch_all")
    @patch.object(InventoryModel, "fetch_one")
    def test_get_sales_order_detail(self, mock_fetch_one, mock_fetch_all):
        mock_fetch_one.side_effect = [
            {"id": 1, "cliente_cedula": "V-12345678", "total": 100.0}, # Order
            {"nombre": "Carlos", "apellido": "Mendoza", "email": "c@mail.com", "telefono": "123"} # Client
        ]
        mock_fetch_all.return_value = [
            {"id": 1, "item_nombre": "Filtro", "cantidad": 2, "precio_unitario": 50.0}
        ]
        model = InventoryModel()
        detail = model.ejecutar("get_sales_order_detail", 1)

        assert detail["id"] == 1
        assert detail["cliente_nombre"] == "Carlos Mendoza"
        assert len(detail["detalles"]) == 1

    def test_ejecutar_invalid_action(self):
        model = InventoryModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
