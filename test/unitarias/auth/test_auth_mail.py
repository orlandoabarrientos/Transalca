import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date
from flask import Flask
from model.mail_service import MailService
from controller.auth_controller import auth_bp, recovery_throttle
from model.auth_model import AuthModel


@pytest.fixture
def client():
    recovery_throttle.clear()
    app = Flask(__name__, template_folder='views')
    app.secret_key = 'test_secret_key'
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c
    recovery_throttle.clear()


class TestMailService:

    @patch("smtplib.SMTP_SSL")
    def test_send_mime_ssl_port_465(self, mock_smtp_ssl):
        server_instance = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = server_instance

        with patch("model.mail_service.MAIL_PORT", 465):
            success = MailService.send_email(
                "cliente@empresa.com",
                "Asunto de prueba",
                "<p>Contenido HTML</p>",
                "Contenido texto"
            )

        assert success is True
        mock_smtp_ssl.assert_called_once()
        server_instance.login.assert_called_once()
        server_instance.sendmail.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_mime_starttls_port_587(self, mock_smtp):
        server_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = server_instance

        with patch("model.mail_service.MAIL_PORT", 587):
            success = MailService.send_email(
                "cliente@empresa.com",
                "Asunto de prueba 587",
                "<p>Contenido HTML</p>",
                "Contenido texto"
            )

        assert success is True
        mock_smtp.assert_called_once()
        server_instance.starttls.assert_called_once()
        server_instance.login.assert_called_once()
        server_instance.sendmail.assert_called_once()

    @patch("smtplib.SMTP_SSL", side_effect=Exception("Connection refused"))
    def test_send_mime_handles_network_failure_safely(self, mock_smtp_ssl):
        with patch("model.mail_service.MAIL_PORT", 465):
            success = MailService.send_email(
                "cliente@empresa.com",
                "Falla intencional",
                "<p>HTML</p>"
            )

        assert success is False

    def test_send_email_empty_recipient_returns_false(self):
        assert MailService.send_email("", "Asunto", "<p>HTML</p>") is False
        assert MailService.send_email(None, "Asunto", "<p>HTML</p>") is False

    @patch.object(MailService, "_send_mime_message", return_value=True)
    def test_send_recovery_email(self, mock_send):
        success = MailService.send_recovery_email(
            "usuario@ejemplo.com",
            "Carlos Perez",
            "http://127.0.0.1:5000/auth/reset?token=testtoken123"
        )
        assert success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "usuario@ejemplo.com"
        assert "Recuperación de Contraseña" in args[1]
        assert "http://127.0.0.1:5000/auth/reset?token=testtoken123" in args[3]

    @patch.object(MailService, "_send_mime_message", return_value=True)
    def test_send_credit_reminder_7d(self, mock_send):
        success = MailService.send_credit_reminder_7d(
            "empresa@ejemplo.com",
            "Inversiones Lara C.A.",
            105,
            Decimal("1250.50"),
            date(2026, 9, 25),
            7,
            Decimal("45000.00")
        )
        assert success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "empresa@ejemplo.com"
        assert "7 días" in args[1]
        assert "1,250.50" in args[3]
        assert "45,000.00" in args[3]

    @patch.object(MailService, "_send_mime_message", return_value=True)
    def test_send_credit_alert_2d(self, mock_send):
        success = MailService.send_credit_alert_2d(
            "empresa@ejemplo.com",
            "Inversiones Lara C.A.",
            105,
            Decimal("1250.50"),
            date(2026, 9, 20),
            2,
            Decimal("45000.00")
        )
        assert success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "empresa@ejemplo.com"
        assert "2 días" in args[1]

    @patch.object(MailService, "_send_mime_message", return_value=True)
    def test_send_credit_expired(self, mock_send):
        success = MailService.send_credit_expired(
            "empresa@ejemplo.com",
            "Inversiones Lara C.A.",
            105,
            Decimal("1250.50"),
            date(2026, 9, 15),
            3,
            Decimal("45000.00")
        )
        assert success is True
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        assert args[0] == "empresa@ejemplo.com"
        assert "Crédito Vencido" in args[1]
        assert "Vencido" in args[3]


class TestAuthRecoveryFlow:

    @patch.object(AuthModel, "ejecutar")
    @patch.object(MailService, "send_recovery_email", return_value=True)
    def test_do_recover_sends_email_and_hides_token(self, mock_mail, mock_ejecutar, client):
        def fake_ejecutar(action, *args, **kwargs):
            if action == "create_recovery_token":
                return "secret_token_abc123"
            if action == "get_user_by_email":
                return {"id": 1, "nombre": "Maria", "email": "maria@correo.com"}
            return None

        mock_ejecutar.side_effect = fake_ejecutar

        response = client.post('/auth/do_recover', json={"email": "maria@correo.com"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "token" not in data
        mock_mail.assert_called_once()
        mail_args = mock_mail.call_args[0]
        assert mail_args[0] == "maria@correo.com"
        assert mail_args[1] == "Maria"
        assert "token=secret_token_abc123" in mail_args[2]

    @patch.object(AuthModel, "ejecutar", return_value=None)
    def test_do_recover_email_not_found(self, mock_ejecutar, client):
        response = client.post('/auth/do_recover', json={"email": "noexiste@correo.com"})
        assert response.status_code == 404
        data = response.get_json()
        assert data["status"] == "error"

    def test_reset_page_without_token_redirects(self, client):
        response = client.get('/auth/reset')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    @patch("controller.auth_controller.send_from_directory", return_value="reset_page_content")
    def test_reset_page_with_token_serves_html(self, mock_send, client):
        response = client.get('/auth/reset?token=validtoken123')
        assert response.status_code == 200
        mock_send.assert_called_once_with('views/auth', 'reset.html')

    @patch.object(AuthModel, "ejecutar", return_value=True)
    def test_do_reset_success(self, mock_ejecutar, client):
        payload = {
            "token": "validtoken123",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        response = client.post('/auth/do_reset', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"

    def test_do_reset_missing_token(self, client):
        payload = {
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        response = client.post('/auth/do_reset', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"

    def test_recovery_throttle_progression(self):
        email = "throttle_test@transalca.com"
        ip = "127.0.0.1"
        recovery_throttle.clear(ip, email)

        allowed, _, _ = recovery_throttle.check(ip, email)
        assert allowed is True

        cooldown, count = recovery_throttle.register_success(ip, email)
        assert cooldown == 300
        assert count == 1

        allowed, remaining, msg = recovery_throttle.check(ip, email)
        assert allowed is False
        assert remaining > 0
        assert "5 minutos" in msg

        for expected_count in range(2, 5):
            recovery_throttle._records[recovery_throttle.key(ip, email)]['locked_until'] = 0
            cooldown, count = recovery_throttle.register_success(ip, email)
            assert cooldown == 300
            assert count == expected_count

        recovery_throttle._records[recovery_throttle.key(ip, email)]['locked_until'] = 0
        cooldown, count = recovery_throttle.register_success(ip, email)
        assert cooldown == 3600
        assert count == 5

        allowed, remaining, msg = recovery_throttle.check(ip, email)
        assert allowed is False
        assert remaining > 0
        assert "1 hora" in msg

        for expected_count in range(6, 10):
            recovery_throttle._records[recovery_throttle.key(ip, email)]['locked_until'] = 0
            cooldown, count = recovery_throttle.register_success(ip, email)
            assert cooldown == 300
            assert count == expected_count

        recovery_throttle._records[recovery_throttle.key(ip, email)]['locked_until'] = 0
        cooldown, count = recovery_throttle.register_success(ip, email)
        assert cooldown == 86400
        assert count == 10

        allowed, remaining, msg = recovery_throttle.check(ip, email)
        assert allowed is False
        assert remaining > 0
        assert "24 horas" in msg

        recovery_throttle.clear(ip, email)

    @patch.object(AuthModel, "ejecutar")
    @patch.object(MailService, "send_recovery_email", return_value=True)
    def test_do_recover_rate_limiting_http_429(self, mock_mail, mock_ejecutar, client):
        def fake_ejecutar(action, *args, **kwargs):
            if action == "create_recovery_token":
                return "token_cooldown_123"
            if action == "get_user_by_email":
                return {"id": 1, "nombre": "Usuario Prueba", "email": "testcooldown@transalca.com"}
            return None

        mock_ejecutar.side_effect = fake_ejecutar
        test_email = "testcooldown@transalca.com"

        res1 = client.post('/auth/do_recover', json={"email": test_email})
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert data1["status"] == "success"
        assert data1["cooldown"] == 300
        assert data1["attempt"] == 1

        res2 = client.post('/auth/do_recover', json={"email": test_email})
        assert res2.status_code == 429
        data2 = res2.get_json()
        assert data2["status"] == "error"
        assert "5 minutos" in data2["message"]
        assert data2["cooldown"] > 0
