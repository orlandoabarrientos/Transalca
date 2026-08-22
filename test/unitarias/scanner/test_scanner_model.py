import pytest
from unittest.mock import patch
from model.scanner_model import ScannerModel


class TestScannerModelResolvers:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para la resolución de QR crudos."""

    # DATA PROVIDER: Resolución de texto crudo de QR a ID de base de datos
    @pytest.mark.parametrize("raw_input, expected_id, is_valid", [
        ("15", 15, True),                                                # ID numérico directo
        ("http://localhost/scanner?qr=15", 15, True),                   # URL del escáner
        ("http://transalca.com/client/qr_scan?id=20", 20, True),        # URL cliente
        ("/scanner?qr=99", 99, True),                                    # Ruta relativa scanner
        ("", None, False),                                               # Texto vacío
        ("codigo_qr_no_sistema", None, False),                          # Texto no numérico
    ])
    @patch.object(ScannerModel, "_get_active_qr_by_id")
    def test_resolve_qr_from_raw_data_provider(
        self, mock_get_active_qr, raw_input, expected_id, is_valid
    ):
        mock_get_active_qr.return_value = {"id": expected_id, "tipo": "pago"} if expected_id else None
        model = ScannerModel()

        qr, error = model._resolve_qr_from_raw(raw_input)

        if is_valid:
            assert qr is not None
            assert qr["id"] == expected_id
            assert error is None
        else:
            assert qr is None
            assert error is not None


class TestScannerModelUtilityState:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para estados de utilidad de QR."""

    # DATA PROVIDER: Evaluación del estado de la utilidad del QR
    @pytest.mark.parametrize("contenido, expected_active, expected_msg_part", [
        ('{"utilidad": "info"}', False, "no tiene nada todavia"),
        ('{"utilidad": "pago", "estado": "cumplida"}', False, "ya fue utilizado"),
        ('{"utilidad": "pago", "estado": "usado"}', False, "ya fue utilizado"),
        ('{"utilidad": "promocion", "estado": "activa", "referencia_id": 5}', True, "activa"),
    ])
    def test_get_utility_state_data_provider(
        self, contenido, expected_active, expected_msg_part
    ):
        model = ScannerModel()
        qr = {"id": 1, "tipo": "promocion", "contenido": contenido}

        state = model._get_utility_state(qr)

        assert state["active"] == expected_active
        assert expected_msg_part in state["message"].lower()


class TestScannerModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para procesamiento de escaneo."""

    @patch.object(ScannerModel, "_get_order_full")
    @patch.object(ScannerModel, "_mark_completed")
    @patch.object(ScannerModel, "_get_utility_state")
    def test_process_scan_for_employee_factura_valid(
        self, mock_get_utility_state, mock_mark_completed, mock_get_order_full
    ):
        mock_get_utility_state.return_value = {
            "active": True,
            "utility": "factura",
            "reference_id": 10,
            "content": {"kind": "factura", "orden_id": 10}
        }
        mock_get_order_full.return_value = {"id": 10, "total": 250.00, "cliente_cedula": "V-12345678"}
        qr = {"id": 1, "tipo": "pago", "referencia_id": 10, "contenido": "{}"}

        model = ScannerModel()
        result = model.ejecutar("process_scan_for_employee", qr)

        assert result["mode"] == "factura_validada"
        assert result["order"]["id"] == 10
        mock_mark_completed.assert_called_once_with(qr)

    @patch.object(ScannerModel, "fetch_all")
    def test_get_active_promotions(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "nombre": "Promo 5to Cambio", "puntos_requeridos": 5}
        ]
        model = ScannerModel()
        promos = model.ejecutar("get_active_promotions")

        assert len(promos) == 1
        assert promos[0]["nombre"] == "Promo 5to Cambio"

    def test_ejecutar_invalid_action(self):
        model = ScannerModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
