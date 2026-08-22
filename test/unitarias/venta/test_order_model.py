import pytest
from unittest.mock import patch, MagicMock
from model.order_model import OrderModel
from config.validation import ValidationError


class TestOrderModelHelpers:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para resolución de métodos de pago e ítems de carrito."""

    # DATA PROVIDER: Resolución de métodos de pago por ID o nombre
    @pytest.mark.parametrize("method_input, expected_name, is_valid", [
        ("1", "pago_movil", True),
        ("zelle", "zelle", True),
        ("transferencia", "transferencia", True),
        ("metodo_inexistente", None, False),
        ("", None, False),
        (None, None, False),
    ])
    @patch.object(OrderModel, "fetch_one")
    def test_get_payment_method_data_provider(self, mock_fetch_one, method_input, expected_name, is_valid):
        if is_valid:
            mock_fetch_one.return_value = {"id": 1, "nombre": expected_name, "permite_credito": 0, "moneda": "usd"}
        else:
            mock_fetch_one.return_value = None

        model = OrderModel()
        result = model._get_payment_method(method_input)

        if is_valid:
            assert result is not None
            assert model._is_valid_payment_method(method_input) is True
        else:
            assert result is None
            assert model._is_valid_payment_method(method_input) is False

    # DATA PROVIDER: Validaciones de adición de ítems al carrito (tipo y cantidad)
    @pytest.mark.parametrize("tipo, cantidad, is_valid", [
        ("producto", 1, True),
        ("servicio", 3, True),
        ("producto", -5, False),  # Cantidad negativa
        ("producto", "invalido", False), # Cantidad no numérica
        ("tipo_invalido", 1, False),  # Tipo item no permitido
    ])
    def test_add_to_cart_validation_data_provider(self, tipo, cantidad, is_valid):
        model = OrderModel()
        data = {
            "tipo": tipo,
            "cantidad": cantidad,
            "item_id": 10
        }

        if is_valid:
            with patch.object(OrderModel, "_ensure_client_exists", return_value=True), \
                 patch.object(OrderModel, "fetch_one", side_effect=[{"codigo": 10}, None]), \
                 patch.object(OrderModel, "insert", return_value=1):
                res = model._add_to_cart("V-12345678", data)
                assert res is not None
        else:
            with pytest.raises(ValidationError):
                model._add_to_cart("V-12345678", data)


class TestOrderModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para procesamiento de órdenes de venta."""

    @patch.object(OrderModel, "fetch_all")
    def test_get_cart(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "tipo": "producto", "cantidad": 2, "item_nombre": "Filtro Aceite", "precio": 15.00}
        ]
        model = OrderModel()
        cart = model.ejecutar("get_cart", "V-12345678")

        assert len(cart) == 1
        assert cart[0]["item_nombre"] == "Filtro Aceite"
        mock_fetch_all.assert_called_once()

    @patch.object(OrderModel, "fetch_one")
    def test_get_cart_count(self, mock_fetch_one):
        mock_fetch_one.return_value = {"total": 5}
        model = OrderModel()
        count = model.ejecutar("get_cart_count", "V-12345678")

        assert count == 5

    @patch.object(OrderModel, "update")
    def test_update_cart_quantity(self, mock_update):
        mock_update.return_value = 1
        model = OrderModel()
        result = model.ejecutar("update_cart_quantity", 1, 3)

        assert result == 1
        mock_update.assert_called_once()

    @patch.object(OrderModel, "delete")
    def test_remove_from_cart(self, mock_delete):
        mock_delete.return_value = 1
        model = OrderModel()
        result = model.ejecutar("remove_from_cart", 1)

        assert result == 1
        mock_delete.assert_called_once()

    @patch.object(OrderModel, "delete")
    def test_clear_cart(self, mock_delete):
        mock_delete.return_value = 1
        model = OrderModel()
        result = model.ejecutar("clear_cart", "V-12345678")

        assert result == 1
        mock_delete.assert_called_once()

    @patch.object(OrderModel, "fetch_all")
    def test_get_client_orders(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 100, "fecha": "2026-08-22", "total": 150.00, "metodo_pago": "Pago Móvil"}
        ]
        model = OrderModel()
        orders = model.ejecutar("get_client_orders", "V-12345678")

        assert len(orders) == 1
        assert orders[0]["id"] == 100

    @patch.object(OrderModel, "fetch_one")
    @patch.object(OrderModel, "fetch_all")
    def test_get_order_detail(self, mock_fetch_all, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"id": 100, "cliente_cedula": "V-12345678", "total": 150.00}, # Order main row
            {"nombre": "Carlos", "apellido": "Mendoza"},                 # Client info
            {"id": 5, "imagen_url": "comp.png"}                          # Payment receipt
        ]
        mock_fetch_all.return_value = [
            {"id": 1, "item_nombre": "Aceite 20W50", "cantidad": 2, "precio_unitario": 10.00, "subtotal": 20.00}
        ]

        model = OrderModel()
        detail = model.ejecutar("get_order_detail", 100)

        assert detail["id"] == 100
        assert len(detail["detalles"]) == 1
        assert detail["nombre"] == "Carlos"

    def test_ejecutar_invalid_action(self):
        model = OrderModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
