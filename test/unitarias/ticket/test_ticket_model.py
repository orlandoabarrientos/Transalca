import pytest
from unittest.mock import patch
from model.ticket_model import TicketModel


class TestTicketModelProperties:
    """Pruebas unitarias para getters y setters del modelo de ticket de soporte."""

    def test_property_setters_strip_whitespace(self):
        model = TicketModel()
        model.cliente_cedula = "  V-12345678  "
        model.asunto = "  Problema con factura  "
        model.descripcion = "  No aparece reflejado el pago  "
        model.prioridad = "  alta  "

        assert model.cliente_cedula == "V-12345678"
        assert model.asunto == "Problema con factura"
        assert model.descripcion == "No aparece reflejado el pago"
        assert model.prioridad == "alta"

    def test_property_setters_none(self):
        model = TicketModel()
        model.cliente_cedula = None
        model.asunto = None
        model.descripcion = None
        model.prioridad = None

        assert model.cliente_cedula is None
        assert model.asunto is None
        assert model.descripcion is None
        assert model.prioridad is None


class TestTicketModelValidation:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para tickets."""

    # DATA PROVIDER: Pruebas con diferentes prioridades válidas
    @pytest.mark.parametrize("prioridad_valida", [
        "baja",
        "media",
        "alta",
        "urgente",
    ])
    @patch.object(TicketModel, "insert")
    def test_create_with_valid_priorities_data_provider(self, mock_insert, prioridad_valida):
        mock_insert.return_value = 1
        model = TicketModel()
        data = {
            "cliente_cedula": "V-12345678",
            "asunto": "Consulta de servicio",
            "descripcion": "Detalles adicionales",
            "prioridad": prioridad_valida
        }
        tid = model.ejecutar("create", data)

        assert tid == 1
        assert model.prioridad == prioridad_valida
        mock_insert.assert_called_once()

    # DATA PROVIDER: Pruebas con diferentes tipos de referencias (general, vehiculo, producto, servicio)
    @pytest.mark.parametrize("ref_tipo, ref_field, ref_val, expected_type", [
        ("general", "ref_none", None, "general"),
        ("vehiculo", "vehiculo_placa", "ABC123", "vehiculo"),
        ("producto", "referencia_id", "PROD-001", "producto"),
        ("servicio", "referencia_id", "5", "servicio"),
    ])
    @patch.object(TicketModel, "fetch_one")
    @patch.object(TicketModel, "insert")
    def test_create_with_reference_types_data_provider(
        self, mock_insert, mock_fetch_one, ref_tipo, ref_field, ref_val, expected_type
    ):
        mock_insert.return_value = 10
        # Simular respuestas según la consulta de referencia
        if ref_tipo == "vehiculo":
            mock_fetch_one.return_value = {"placa_vehiculo": "ABC123"}
        elif ref_tipo == "producto":
            mock_fetch_one.return_value = {"codigo": "PROD-001"}
        elif ref_tipo == "servicio":
            mock_fetch_one.return_value = {"id": 5}
        else:
            mock_fetch_one.return_value = None

        model = TicketModel()
        data = {
            "cliente_cedula": "V-12345678",
            "asunto": "Soporte técnico",
            "referencia_tipo": ref_tipo,
            ref_field: ref_val
        }
        tid = model.ejecutar("create", data)

        assert tid == 10
        mock_insert.assert_called_once()


class TestTicketModelDatabaseOperations:
    """Pruebas unitarias con mocks de base de datos para operaciones de ticket de soporte."""

    @patch.object(TicketModel, "fetch_all")
    def test_get_all(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "asunto": "Falla en vehículo", "estado": "abierto", "prioridad": "alta"}
        ]
        model = TicketModel()
        result = model.ejecutar("get_all")

        assert len(result) == 1
        assert result[0]["asunto"] == "Falla en vehículo"
        mock_fetch_all.assert_called_once()

    @patch.object(TicketModel, "_get_responses")
    @patch.object(TicketModel, "fetch_one")
    def test_get_by_id(self, mock_fetch_one, mock_get_responses):
        mock_fetch_one.return_value = {"id": 1, "asunto": "Falla en vehículo", "cliente_cedula": "V-12345678"}
        mock_get_responses.return_value = [{"id": 10, "mensaje": "En revisión"}]

        model = TicketModel()
        result = model.ejecutar("get_by_id", 1)

        assert result["id"] == 1
        assert len(result["respuestas"]) == 1

    @patch.object(TicketModel, "update")
    def test_update_status(self, mock_update):
        mock_update.return_value = 1
        model = TicketModel()
        result = model.ejecutar("update_status", 1, "resuelto")

        assert result == 1
        mock_update.assert_called_once()

    @patch.object(TicketModel, "insert")
    def test_add_response(self, mock_insert):
        mock_insert.return_value = 5
        model = TicketModel()
        data = {
            "ticket_id": 1,
            "autor_id": 2,
            "autor_tipo": "admin",
            "mensaje": "Su requerimiento fue procesado.",
            "adjunto_url": None
        }
        rid = model.ejecutar("add_response", data)

        assert rid == 5
        mock_insert.assert_called_once()

    @patch.object(TicketModel, "fetch_all")
    def test_count_by_estado(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"estado": "abierto", "total": 4},
            {"estado": "resuelto", "total": 10}
        ]
        model = TicketModel()
        stats = model.ejecutar("count_by_estado")

        assert len(stats) == 2
        assert stats[0]["estado"] == "abierto"

    def test_ejecutar_invalid_action(self):
        model = TicketModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
