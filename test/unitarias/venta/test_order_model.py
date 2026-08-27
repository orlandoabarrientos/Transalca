import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock
from model.order_model import OrderModel
from config.validation import ValidationError


class TestOrderModelHelpers:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para resolucion de metodos de pago y helpers."""

    # DATA PROVIDER: Resolucion de metodos de pago por ID o nombre
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

    # DATA PROVIDER: Validaciones de adicion de items al carrito (tipo y cantidad)
    @pytest.mark.parametrize("tipo, cantidad, is_valid", [
        ("producto", 1, True),
        ("servicio", 3, True),
        ("producto", -5, False),  # Cantidad negativa
        ("producto", "invalido", False),  # Cantidad no numerica
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

    @patch.object(OrderModel, "fetch_one")
    def test_ensure_client_exists_already_registered(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id_cliente": 1}
        model = OrderModel()
        assert model._ensure_client_exists("V-12345678") is True

    @patch.object(OrderModel, "insert", return_value=5)
    @patch.object(OrderModel, "fetch_one")
    def test_ensure_client_exists_registers_from_users(self, mock_fetch_one, mock_insert):
        mock_fetch_one.side_effect = [
            None,  # No existe en cliente
            {"id": 10, "cedula": "V-12345678", "nombre": "Pedro", "apellido": "Perez", "email": "p@mail.com", "telefono": "123", "direccion": "Caracas"}  # Existe en usuarios
        ]
        model = OrderModel()
        assert model._ensure_client_exists("V-12345678") is True
        assert mock_insert.call_count == 2  # cliente y cliente_natural

    @patch.object(OrderModel, "fetch_one", return_value=None)
    def test_ensure_client_exists_not_found(self, mock_fetch_one):
        model = OrderModel()
        assert model._ensure_client_exists("V-00000000") is False

    @patch.object(OrderModel, "fetch_one")
    def test_supports_qr_order_relation(self, mock_fetch_one):
        mock_fetch_one.return_value = {"Field": "orden_venta_id"}
        model = OrderModel()
        assert model._supports_qr_order_relation() is True

    @patch.object(OrderModel, "fetch_one")
    def test_get_current_rate(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "monto": 36.50, "tipo_tasa_cambio": "bcv"}
        model = OrderModel()
        rate = model._get_current_rate("bcv")
        assert rate["monto"] == 36.50

    @patch.object(OrderModel, "fetch_all")
    def test_get_active_payment_methods(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "pago_movil", "permite_credito": 0, "moneda": "usd"}
        ]
        model = OrderModel()
        methods = model._get_active_payment_methods()
        assert len(methods) == 1


class TestOrderModelCartOperations:
    """Pruebas unitarias para operaciones de carrito de compras."""

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

    @patch.object(OrderModel, "update", return_value=1)
    @patch.object(OrderModel, "fetch_one")
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_add_to_cart_increments_existing_product(self, mock_ensure, mock_fetch_one, mock_update):
        mock_fetch_one.side_effect = [
            {"codigo": "PROD001"},  # Producto existe
            {"id": 10, "cantidad": 2}  # Ya en carrito
        ]
        model = OrderModel()
        res = model._add_to_cart("V-12345678", {"tipo": "producto", "item_id": "PROD001", "cantidad": 3})

        assert res == 1
        mock_update.assert_called_once()

    @patch.object(OrderModel, "insert", return_value=12)
    @patch.object(OrderModel, "fetch_one")
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_add_to_cart_service_new(self, mock_ensure, mock_fetch_one, mock_insert):
        mock_fetch_one.side_effect = [
            {"id_servicio": 5},  # Servicio existe
            None  # No en carrito
        ]
        model = OrderModel()
        res = model._add_to_cart("V-12345678", {"tipo": "servicio", "item_id": 5})

        assert res == 12
        mock_insert.assert_called_once()

    @patch.object(OrderModel, "fetch_one", return_value=None)
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_add_to_cart_unavailable_product_raises_error(self, mock_ensure, mock_fetch_one):
        model = OrderModel()
        with pytest.raises(ValueError) as exc_info:
            model._add_to_cart("V-12345678", {"tipo": "producto", "item_id": "NOEXISTE", "cantidad": 1})

        assert "no disponible" in str(exc_info.value).lower()

    @patch.object(OrderModel, "update")
    def test_update_cart_quantity(self, mock_update):
        mock_update.return_value = 1
        model = OrderModel()
        result = model.ejecutar("update_cart_quantity", 1, 3)

        assert result == 1
        mock_update.assert_called_once()

    def test_update_cart_quantity_invalid_raises_error(self):
        model = OrderModel()
        with pytest.raises(ValidationError) as exc_info:
            model.ejecutar("update_cart_quantity", 1, -2)

        assert "cantidad" in exc_info.value.errors

    @patch.object(OrderModel, "fetch_one")
    def test_cart_item_owner(self, mock_fetch_one):
        mock_fetch_one.return_value = {"cliente_cedula": "V-12345678"}
        model = OrderModel()
        owner = model.ejecutar("cart_item_owner", 1)

        assert owner == "V-12345678"

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


class TestOrderModelTransactionsAndOrders:
    """Pruebas unitarias transaccionales para procesamiento de ordenes de venta y servicios mecanicos."""

    # PRUEBA TRANSACCIONAL: Crear orden de venta de contado en USD (Commit)
    @patch.object(OrderModel, "_supports_qr_order_relation", return_value=True)
    @patch.object(OrderModel, "_get_current_rate", return_value={"id": 1, "monto": 36.50})
    @patch.object(OrderModel, "_get_payment_method", return_value={"id": 1, "nombre": "pago_movil", "permite_credito": 0, "moneda": "usd"})
    @patch.object(OrderModel, "_get_cart")
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_create_sale_order_contado_usd_success(self, mock_ensure, mock_cart, mock_pay, mock_rate, mock_qr):
        mock_cart.return_value = [
            {"tipo": "producto", "producto_codigo": "PROD001", "cantidad": 2, "precio": 25.0},
            {"tipo": "servicio", "servicio_id": 5, "cantidad": 1, "precio": 50.0}
        ]
        model = OrderModel()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 200

        with patch.object(OrderModel, "con_transalca", return_value=mock_conn), \
             patch.object(OrderModel, "fetch_one", return_value={"tipo_cliente": "natural"}):
            order_id = model.ejecutar("create_sale_order", "V-12345678", "pago_movil", "comp.png", 1)

            assert order_id == 200
            mock_conn.begin.assert_called_once()
            mock_conn.commit.assert_called_once()
            mock_conn.rollback.assert_not_called()

    # PRUEBA TRANSACCIONAL: Crear orden a credito para cliente juridico (Commit)
    @patch.object(OrderModel, "_supports_qr_order_relation", return_value=False)
    @patch.object(OrderModel, "_get_current_rate", return_value={"id": 1, "monto": 36.50})
    @patch.object(OrderModel, "_get_payment_method", return_value={"id": 2, "nombre": "credito_30", "permite_credito": 1, "moneda": "usd"})
    @patch.object(OrderModel, "_get_cart")
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_create_sale_order_credito_juridico_success(self, mock_ensure, mock_cart, mock_pay, mock_rate, mock_qr):
        mock_cart.return_value = [
            {"tipo": "producto", "producto_codigo": "PROD001", "cantidad": 10, "precio": 20.0}
        ]
        model = OrderModel()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 201

        with patch.object(OrderModel, "con_transalca", return_value=mock_conn), \
             patch.object(OrderModel, "fetch_one", return_value={"tipo_cliente": "juridica", "dias_credito": 30}):
            order_id = model.ejecutar("create_sale_order", "J-12345678-0", "credito_30")

            assert order_id == 201
            mock_conn.commit.assert_called_once()

    # PRUEBA TRANSACCIONAL: Crear orden a credito para cliente natural falla (Rollback)
    @patch.object(OrderModel, "_get_payment_method", return_value={"id": 2, "nombre": "credito_30", "permite_credito": 1, "moneda": "usd"})
    @patch.object(OrderModel, "_get_cart", return_value=[{"tipo": "producto", "producto_codigo": "PROD001", "cantidad": 1, "precio": 10.0}])
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_create_sale_order_credito_natural_raises_error_and_rollback(self, mock_ensure, mock_cart, mock_pay):
        model = OrderModel()
        mock_conn = MagicMock()

        with patch.object(OrderModel, "con_transalca", return_value=mock_conn), \
             patch.object(OrderModel, "fetch_one", return_value={"tipo_cliente": "natural"}):
            with pytest.raises(ValueError) as exc_info:
                model.ejecutar("create_sale_order", "V-12345678", "credito_30")

            assert "empresas" in str(exc_info.value).lower()
            mock_conn.rollback.assert_called_once()

    # PRUEBA TRANSACCIONAL: Carrito vacio retorna None
    @patch.object(OrderModel, "_get_cart", return_value=[])
    @patch.object(OrderModel, "_ensure_client_exists", return_value=True)
    def test_create_sale_order_empty_cart_returns_none(self, mock_ensure, mock_cart):
        model = OrderModel()
        order_id = model.ejecutar("create_sale_order", "V-12345678", "pago_movil")
        assert order_id is None

    # PRUEBA: Activacion de servicios mecanicos tras orden
    @patch.object(OrderModel, "insert", return_value=1)
    @patch.object(OrderModel, "fetch_all")
    @patch.object(OrderModel, "fetch_one")
    def test_activate_services_for_order(self, mock_fetch_one, mock_fetch_all, mock_insert):
        mock_fetch_one.side_effect = [
            {"id_orden_venta": 100, "cliente_cedula": "V-12345678"},  # Order
            None  # Servicio aun no asignado
        ]
        mock_fetch_all.return_value = [{"servicio_id": 10}]
        model = OrderModel()
        created = model.ejecutar("activate_services_for_order", 100)

        assert created == 1
        mock_insert.assert_called_once()

    @patch.object(OrderModel, "fetch_all")
    def test_get_client_orders(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 100, "fecha": "2026-08-22", "total": 150.00, "metodo_pago": "Pago Movil"}
        ]
        model = OrderModel()
        orders = model.ejecutar("get_client_orders", "V-12345678")

        assert len(orders) == 1
        assert orders[0]["id"] == 100

    @patch.object(OrderModel, "fetch_one")
    @patch.object(OrderModel, "fetch_all")
    def test_get_order_detail(self, mock_fetch_all, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"id": 100, "cliente_cedula": "V-12345678", "total": 150.00},  # Order main row
            {"nombre": "Carlos", "apellido": "Mendoza", "email": "c@mail.com", "telefono": "123"},  # Client info
            {"id": 5, "imagen_url": "comp.png"}  # Payment receipt
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
