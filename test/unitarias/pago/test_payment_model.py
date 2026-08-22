import pytest
from unittest.mock import patch
from model.payment_model import PaymentModel
from config.validation import ValidationError


class TestPaymentModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de pago."""

    # DATA PROVIDER: Validación de motivos de rechazo de pago
    @pytest.mark.parametrize("observaciones, is_valid", [
        ("Número de referencia no coincide con el estado de cuenta", True),
        ("Monto transferido no cubre el total de la orden", True),
        ("", False),           # Motivo obligatorio vacío
        ("   ", False),        # Solo espacios en blanco
        (None, False),         # Ninguno enviado
    ])
    @patch.object(PaymentModel, "update")
    @patch.object(PaymentModel, "fetch_one")
    def test_reject_observaciones_data_provider(
        self, mock_fetch_one, mock_update, observaciones, is_valid
    ):
        mock_fetch_one.return_value = {"id": 1, "orden_venta_id": 10, "estado": "pendiente"}
        mock_update.return_value = 1
        model = PaymentModel()

        if is_valid:
            result = model._reject(1, "V-10000000", observaciones)
            assert result is True
        else:
            with pytest.raises(ValidationError) as exc_info:
                model._reject(1, "V-10000000", observaciones)
            assert "observaciones" in exc_info.value.errors


class TestPaymentModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de comprobantes de pago."""

    @patch.object(PaymentModel, "_attach_client")
    @patch.object(PaymentModel, "fetch_all")
    def test_get_pending(self, mock_fetch_all, mock_attach_client):
        mock_fetch_all.return_value = [
            {"id": 1, "orden_venta_id": 10, "estado": "pendiente", "total": 150.00}
        ]
        mock_attach_client.side_effect = lambda x: x
        model = PaymentModel()
        result = model.ejecutar("get_pending")

        assert len(result) == 1
        assert result[0]["estado"] == "pendiente"
        mock_fetch_all.assert_called_once()

    @patch.object(PaymentModel, "_attach_client")
    @patch.object(PaymentModel, "fetch_all")
    def test_get_all_by_status(self, mock_fetch_all, mock_attach_client):
        mock_fetch_all.return_value = [
            {"id": 1, "orden_venta_id": 10, "estado": "verificado"}
        ]
        mock_attach_client.side_effect = lambda x: x
        model = PaymentModel()
        result = model.ejecutar("get_all", "verificado")

        assert len(result) == 1
        assert result[0]["estado"] == "verificado"

    @patch.object(PaymentModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.side_effect = [
            {"id": 1, "orden_venta_id": 10, "cliente_cedula": "V-12345678"},  # comprobante
            {"nombre": "Ana", "apellido": "López", "email": "ana@ejemplo.com"} # cliente
        ]
        model = PaymentModel()
        with patch.object(PaymentModel, "fetch_all", return_value=[]):
            result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        assert result["nombre"] == "Ana"

    @patch("model.order_model.OrderModel.ejecutar")
    @patch.object(PaymentModel, "update")
    @patch.object(PaymentModel, "fetch_one")
    def test_approve_payment(self, mock_fetch_one, mock_update, mock_order_ejecutar):
        mock_fetch_one.return_value = {"id": 1, "orden_venta_id": 10, "estado": "pendiente"}
        mock_update.return_value = 1
        model = PaymentModel()

        result = model.ejecutar("approve", 1, "V-10000000")

        assert result is True
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = PaymentModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
