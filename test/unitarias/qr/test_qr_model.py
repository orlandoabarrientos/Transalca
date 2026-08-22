import pytest
from unittest.mock import patch
from model.qr_model import QRModel, qr_tipo_to_int
from config.validation import ValidationError


class TestQRModelHelpers:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para utilidades del modelo QR."""

    # DATA PROVIDER: Mapeo de tipo de QR de texto a entero
    @pytest.mark.parametrize("tipo_str, expected_int", [
        ("info", 0),
        ("pago", 1),
        ("promocion", 2),
        ("servicio", 3),
        ("INFO", 0),
        ("PAGO", 1),
        (2, 2),            # Si pasa un entero directamente
        ("desconocido", 0),  # Valor por defecto
    ])
    def test_qr_tipo_to_int_data_provider(self, tipo_str, expected_int):
        assert qr_tipo_to_int(tipo_str) == expected_int


class TestQRModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de QR."""

    # DATA PROVIDER: Pruebas con tipos y utilidades válidas
    @pytest.mark.parametrize("tipo_valido, utilidad_valida", [
        ("info", "catalogo"),
        ("pago", "validar_pago"),
        ("promocion", "canje_puntos"),
        ("servicio", "reserva_mecanico"),
    ])
    def test_validate_valid_qr_data_provider(self, tipo_valido, utilidad_valida):
        model = QRModel()
        data = {
            "tipo": tipo_valido,
            "utilidad_tipo": utilidad_valida,
            "referencia_id": 10 if tipo_valido == "promocion" else None
        }
        # No debe lanzar ValidationError
        model._validate(data)

    # DATA PROVIDER: Pruebas con tipos o utilidades inválidas
    @pytest.mark.parametrize("invalid_data, expected_field", [
        ({"tipo": "", "utilidad_tipo": "info"}, "tipo"),                      # Tipo vacío
        ({"tipo": "tipo_inexistente", "utilidad_tipo": "info"}, "tipo"),      # Tipo no en lista
        ({"tipo": "info", "utilidad_tipo": ""}, "utilidad_tipo"),             # Utilidad vacía
        ({"tipo": "promocion", "utilidad_tipo": "promocion", "referencia_id": ""}, "referencia_id"), # Promoción sin referencia
    ])
    def test_validate_invalid_qr_data_provider(self, invalid_data, expected_field):
        model = QRModel()
        with pytest.raises(ValidationError) as exc_info:
            model._validate(invalid_data)
        assert expected_field in exc_info.value.errors


class TestQRModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de código QR."""

    @patch.object(QRModel, "fetch_all")
    def test_get_user_qrs(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "tipo": "pago", "referencia_id": 10, "estado": 1}
        ]
        model = QRModel()
        result = model.ejecutar("get_user_qrs", "V-12345678")

        assert len(result) == 1
        assert result[0]["tipo"] == "pago"
        mock_fetch_all.assert_called_once()

    @patch.object(QRModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {
            "id": 1,
            "usuario_cedula": "V-12345678",
            "tipo": "promocion",
            "utilidad": "promocion",
            "contenido": '{"kind": "promocion", "estado": "activa", "nota": "Promo 5to cambio"}'
        }
        model = QRModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        assert result["utilidad_estado"] == "activa"
        assert result["contenido_resumen"] == "Promo 5to cambio"

    @patch.object(QRModel, "update")
    def test_delete_qr(self, mock_update):
        mock_update.return_value = 1
        model = QRModel()
        result = model.ejecutar("soft_delete", 1)

        assert result == 1
        mock_update.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = QRModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
