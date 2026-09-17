import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
from decimal import Decimal

from config.config import (
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_SENDER_NAME,
    APP_BASE_URL,
)

logger = logging.getLogger(__name__)


class MailService:

    @staticmethod
    def _logo_path():
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "public", "img", "transalca-logo.png")

    @classmethod
    def _send_mime_message(cls, to_email, subject, plain_text, html_body):
        try:
            msg_root = MIMEMultipart("related")
            msg_root["From"] = formataddr((MAIL_SENDER_NAME, MAIL_USERNAME))
            msg_root["To"] = to_email
            msg_root["Subject"] = subject

            msg_alt = MIMEMultipart("alternative")
            msg_root.attach(msg_alt)

            if plain_text:
                msg_alt.attach(MIMEText(plain_text, "plain", "utf-8"))
            if html_body:
                msg_alt.attach(MIMEText(html_body, "html", "utf-8"))

            logo_file = cls._logo_path()
            if os.path.exists(logo_file):
                try:
                    with open(logo_file, "rb") as f:
                        img = MIMEImage(f.read())
                        img.add_header("Content-ID", "<transalca_logo>")
                        img.add_header("Content-Disposition", "inline", filename="transalca-logo.png")
                        msg_root.attach(img)
                except Exception as exc:
                    logger.warning("Fallo al adjuntar logotipo institucional al correo: %s", exc)

            port = int(MAIL_PORT)
            if port == 465:
                with smtplib.SMTP_SSL(MAIL_SERVER, port, timeout=15) as server:
                    if MAIL_USERNAME and MAIL_PASSWORD:
                        server.login(MAIL_USERNAME, MAIL_PASSWORD)
                    server.sendmail(MAIL_USERNAME, [to_email], msg_root.as_string())
            else:
                with smtplib.SMTP(MAIL_SERVER, port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    if MAIL_USERNAME and MAIL_PASSWORD:
                        server.login(MAIL_USERNAME, MAIL_PASSWORD)
                    server.sendmail(MAIL_USERNAME, [to_email], msg_root.as_string())

            logger.info("Correo enviado exitosamente a %s con asunto: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.error("Error despachando correo a %s: %s", to_email, exc)
            return False

    @classmethod
    def _render_layout(cls, badge_text, badge_color, badge_bg, title, content_html, cta_text=None, cta_url=None):
        cta_block = ""
        if cta_text and cta_url:
            cta_block = f"""
            <div style="text-align: center; margin: 32px 0 24px;">
                <a href="{cta_url}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #E67E22 0%, #D35400 100%); color: #FFFFFF; text-decoration: none; font-weight: 700; font-size: 15px; border-radius: 8px; box-shadow: 0 4px 14px rgba(230, 126, 34, 0.35); text-align: center;">
                    {cta_text}
                </a>
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #F8FAFC; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #1E293B;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; background-color: #F8FAFC; padding: 32px 12px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05); overflow: hidden;">
                    <tr>
                        <td style="padding: 36px 36px 20px; text-align: center; background: linear-gradient(180deg, #FFF7ED 0%, #FFFFFF 100%); border-bottom: 1px solid #F1F5F9;">
                            <img src="cid:transalca_logo" alt="Transalca C.A." width="170" style="display: block; margin: 0 auto; max-width: 170px; height: auto; border: 0;" />
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px 36px 36px;">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <span style="display: inline-block; padding: 6px 16px; border-radius: 9999px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: {badge_color}; background-color: {badge_bg};">
                                    {badge_text}
                                </span>
                            </div>
                            <h1 style="margin: 0 0 20px; font-size: 22px; font-weight: 800; color: #1E293B; line-height: 1.35; text-align: center;">
                                {title}
                            </h1>
                            <div style="font-size: 15px; line-height: 1.65; color: #334155;">
                                {content_html}
                            </div>
                            {cta_block}
                            <div style="margin-top: 36px; padding-top: 24px; border-top: 1px solid #E2E8F0; text-align: center; font-size: 12px; color: #94A3B8; line-height: 1.6;">
                                <p style="margin: 0 0 6px; font-weight: 700; color: #64748B;">Transalca C.A. &bull; RIF: J-40810142-3</p>
                                <p style="margin: 0 0 6px;">Barquisimeto, Estado Lara, Venezuela &bull; <a href="mailto:info@transalcagroup.com" style="color: #E67E22; text-decoration: none; font-weight: 600;">info@transalcagroup.com</a></p>
                                <p style="margin: 12px 0 0; font-size: 11px; color: #94A3B8;">Este es un mensaje institucional automático. Por favor no responda directamente a esta casilla.</p>
                                <p style="margin: 4px 0 0; font-size: 11px; color: #CBD5E1;">&copy; 2026 Transalca C.A. Todos los derechos reservados.</p>
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

    @classmethod
    def send_email(cls, to_email, subject, html_content, text_content=None):
        if not to_email or not str(to_email).strip():
            return False
        return cls._send_mime_message(to_email.strip(), subject, text_content or "", html_content)

    @classmethod
    def send_recovery_email(cls, to_email, user_name, reset_url):
        subject = "Recuperación de Contraseña - Transalca C.A."
        greeting_name = (user_name or "Usuario").strip()
        badge_text = "Seguridad de la Cuenta"
        badge_color = "#1D4ED8"
        badge_bg = "#EFF6FF"
        title = "Recuperación de Contraseña"

        content_html = f"""
        <p style="margin: 0 0 16px;">Hola <strong>{greeting_name}</strong>,</p>
        <p style="margin: 0 0 16px;">Hemos recibido una solicitud para restablecer la contraseña de acceso a tu cuenta en el sistema <strong>TRANSALCA</strong>.</p>
        <p style="margin: 0 0 20px;">Para definir una nueva contraseña, haz clic en el siguiente botón seguro. Este enlace tiene un período de validez de <strong>1 hora</strong> por motivos de seguridad:</p>
        <p style="margin: 20px 0 8px; font-size: 13px; color: #64748B;">Si el botón no responde, copia y pega este enlace en tu navegador web:</p>
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; font-size: 12px; word-break: break-all; color: #E67E22;">
            <a href="{reset_url}" style="color: #E67E22; text-decoration: underline;">{reset_url}</a>
        </div>
        <div style="margin-top: 24px; padding: 14px 18px; background-color: #FFFBEB; border-left: 4px solid #F59E0B; border-radius: 4px; font-size: 13px; color: #92400E;">
            <strong>Nota importante:</strong> Si no solicitaste este cambio, puedes ignorar este mensaje de forma segura. Tu contraseña actual no sufrirá ninguna modificación sin este enlace.
        </div>
        """

        plain_text = (
            f"Hola {greeting_name},\n\n"
            f"Hemos recibido una solicitud para restablecer la contrasena de su cuenta en TRANSALCA.\n"
            f"Para crear una nueva contrasena, ingrese al siguiente enlace valido por 1 hora:\n\n"
            f"{reset_url}\n\n"
            f"Si usted no realizo esta solicitud, ignore este mensaje.\n"
            f"Transalca C.A."
        )

        html = cls._render_layout(
            badge_text=badge_text,
            badge_color=badge_color,
            badge_bg=badge_bg,
            title=title,
            content_html=content_html,
            cta_text="Restablecer mi contraseña",
            cta_url=reset_url,
        )

        return cls.send_email(to_email, subject, html, plain_text)

    @classmethod
    def _format_money(cls, amount):
        try:
            val = Decimal(str(amount or 0)).quantize(Decimal("0.01"))
            return f"{val:,.2f}"
        except Exception:
            return "0.00"

    @classmethod
    def send_credit_reminder_7d(cls, to_email, company_name, order_id, amount_usd, due_date, days_left, amount_bs=None):
        subject = f"Aviso Preventivo: Vencimiento de Crédito en {days_left} días - Orden #{order_id}"
        company = (company_name or "Estimado Cliente").strip()
        due_str = due_date.strftime("%d/%m/%Y") if hasattr(due_date, "strftime") else str(due_date)
        usd_formatted = cls._format_money(amount_usd)
        bs_row_html = ""
        bs_plain = ""
        if amount_bs is not None:
            bs_formatted = cls._format_money(amount_bs)
            bs_row_html = f"""
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Monto en Bolívares (BCV)</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">Bs. {bs_formatted}</td>
            </tr>
            """
            bs_plain = f"Monto en Bolívares: Bs. {bs_formatted}\n"

        badge_text = "Aviso Preventivo"
        badge_color = "#B45309"
        badge_bg = "#FEF3C7"
        title = "Recordatorio Preventivo de Vencimiento"

        orders_url = f"{APP_BASE_URL}/client/orders"

        content_html = f"""
        <p style="margin: 0 0 16px;">Estimados señores de <strong>{company}</strong>,</p>
        <p style="margin: 0 0 16px;">Le recordamos de forma cordial que su crédito comercial correspondiente a la <strong>Orden de Venta #{order_id}</strong> se encuentra próximo a vencer en <strong>{days_left} días</strong>.</p>
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 20px 0; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; border-collapse: collapse;">
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">N° de Orden de Venta</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">#{order_id}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Saldo Pendiente (USD)</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #E67E22; border-bottom: 1px solid #E2E8F0; text-align: right;">${usd_formatted} USD</td>
            </tr>
            {bs_row_html}
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Fecha Límite de Pago</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">{due_str}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B;">Plazo Restante</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #D97706; text-align: right;">{days_left} días restantes</td>
            </tr>
        </table>
        <p style="margin: 0 0 16px;">Le invitamos a gestionar o reportar su pago oportunamente para mantener su línea de crédito activa e impecable.</p>
        """

        plain_text = (
            f"Estimados senores de {company},\n\n"
            f"Le recordamos que su credito correspondiente a la Orden #{order_id} vencera el {due_str} ({days_left} dias restantes).\n"
            f"Saldo pendiente: ${usd_formatted} USD\n"
            f"{bs_plain}\n"
            f"Puede consultar el estado ingresando a: {orders_url}\n\n"
            f"Transalca C.A."
        )

        html = cls._render_layout(
            badge_text=badge_text,
            badge_color=badge_color,
            badge_bg=badge_bg,
            title=title,
            content_html=content_html,
            cta_text="Revisar estado en Mis Pedidos",
            cta_url=orders_url,
        )

        return cls.send_email(to_email, subject, html, plain_text)

    @classmethod
    def send_credit_alert_2d(cls, to_email, company_name, order_id, amount_usd, due_date, days_left, amount_bs=None):
        subject = f"Alerta Próxima: Vencimiento de Crédito en {days_left} días - Orden #{order_id}"
        company = (company_name or "Estimado Cliente").strip()
        due_str = due_date.strftime("%d/%m/%Y") if hasattr(due_date, "strftime") else str(due_date)
        usd_formatted = cls._format_money(amount_usd)
        bs_row_html = ""
        bs_plain = ""
        if amount_bs is not None:
            bs_formatted = cls._format_money(amount_bs)
            bs_row_html = f"""
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Monto en Bolívares (BCV)</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">Bs. {bs_formatted}</td>
            </tr>
            """
            bs_plain = f"Monto en Bolívares: Bs. {bs_formatted}\n"

        badge_text = "Vencimiento Próximo"
        badge_color = "#C2410C"
        badge_bg = "#FFEDD5"
        title = "Alerta Próxima de Vencimiento de Crédito"

        orders_url = f"{APP_BASE_URL}/client/orders"

        content_html = f"""
        <p style="margin: 0 0 16px;">Estimados señores de <strong>{company}</strong>,</p>
        <p style="margin: 0 0 16px;">Le notificamos que el crédito comercial asociado a la <strong>Orden de Venta #{order_id}</strong> está próximo a expirar en tan solo <strong>{days_left} días</strong> ({due_str}).</p>
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 20px 0; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; border-collapse: collapse;">
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">N° de Orden de Venta</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">#{order_id}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Saldo Pendiente (USD)</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #EA580C; border-bottom: 1px solid #E2E8F0; text-align: right;">${usd_formatted} USD</td>
            </tr>
            {bs_row_html}
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Fecha Límite de Pago</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">{due_str}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B;">Plazo Restante</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #EA580C; text-align: right;">{days_left} días restantes</td>
            </tr>
        </table>
        <div style="margin: 20px 0; padding: 14px 18px; background-color: #FFF7ED; border-left: 4px solid #EA580C; border-radius: 4px; font-size: 13px; color: #9A3412;">
            Agradecemos coordinar su liquidación a la brevedad para evitar la suspensión temporal de beneficios o recargos administrativos sobre su cuenta corporativa.
        </div>
        """

        plain_text = (
            f"Estimados senores de {company},\n\n"
            f"ALERTA: El credito de la Orden #{order_id} vencera en {days_left} dias ({due_str}).\n"
            f"Saldo pendiente: ${usd_formatted} USD\n"
            f"{bs_plain}\n"
            f"Acceda a su cuenta para revisar detalles o reportar pago: {orders_url}\n\n"
            f"Transalca C.A."
        )

        html = cls._render_layout(
            badge_text=badge_text,
            badge_color=badge_color,
            badge_bg=badge_bg,
            title=title,
            content_html=content_html,
            cta_text="Revisar estado en Mis Pedidos",
            cta_url=orders_url,
        )

        return cls.send_email(to_email, subject, html, plain_text)

    @classmethod
    def send_credit_expired(cls, to_email, company_name, order_id, amount_usd, due_date, days_overdue, amount_bs=None):
        subject = f"Aviso de Crédito Vencido - Orden #{order_id} - Transalca C.A."
        company = (company_name or "Estimado Cliente").strip()
        due_str = due_date.strftime("%d/%m/%Y") if hasattr(due_date, "strftime") else str(due_date)
        usd_formatted = cls._format_money(amount_usd)
        bs_row_html = ""
        bs_plain = ""
        if amount_bs is not None:
            bs_formatted = cls._format_money(amount_bs)
            bs_row_html = f"""
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Monto en Bolívares (BCV)</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">Bs. {bs_formatted}</td>
            </tr>
            """
            bs_plain = f"Monto en Bolívares: Bs. {bs_formatted}\n"

        badge_text = "Crédito Vencido"
        badge_color = "#B91C1C"
        badge_bg = "#FEE2E2"
        title = "Notificación Formal de Crédito Vencido"

        orders_url = f"{APP_BASE_URL}/client/orders"

        content_html = f"""
        <p style="margin: 0 0 16px;">Estimados señores de <strong>{company}</strong>,</p>
        <p style="margin: 0 0 16px;">Por medio de la presente le notificamos formalmente que el plazo acordado para la liquidación del crédito comercial de la <strong>Orden de Venta #{order_id}</strong> ha expirado el <strong>{due_str}</strong>.</p>
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin: 20px 0; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; border-collapse: collapse;">
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">N° de Orden de Venta</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">#{order_id}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Deuda Pendiente (USD)</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #DC2626; border-bottom: 1px solid #E2E8F0; text-align: right;">${usd_formatted} USD</td>
            </tr>
            {bs_row_html}
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B; border-bottom: 1px solid #E2E8F0;">Fecha de Vencimiento</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #1E293B; border-bottom: 1px solid #E2E8F0; text-align: right;">{due_str}</td>
            </tr>
            <tr>
                <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #64748B;">Estado Actual</td>
                <td style="padding: 12px 16px; font-size: 14px; font-weight: 700; color: #DC2626; text-align: right;">Vencido ({days_overdue} días de retraso)</td>
            </tr>
        </table>
        <div style="margin: 20px 0; padding: 14px 18px; background-color: #FEF2F2; border-left: 4px solid #DC2626; border-radius: 4px; font-size: 13px; color: #991B1B;">
            Le solicitamos amablemente regularizar este saldo pendiente a la brevedad posible a fin de reactivar su línea de compras a crédito y evitar bloqueos en nuevos pedidos. Si ya realizó el pago, por favor repórtelo en la plataforma o contáctenos de inmediato.
        </div>
        """

        plain_text = (
            f"Estimados senores de {company},\n\n"
            f"NOTIFICACION FORMAL: Su credito para la Orden #{order_id} vencio el {due_str} ({days_overdue} dias de retraso).\n"
            f"Deuda pendiente: ${usd_formatted} USD\n"
            f"{bs_plain}\n"
            f"Por favor regularice su pago a la brevedad ingresando a: {orders_url}\n\n"
            f"Transalca C.A."
        )

        html = cls._render_layout(
            badge_text=badge_text,
            badge_color=badge_color,
            badge_bg=badge_bg,
            title=title,
            content_html=content_html,
            cta_text="Revisar estado en Mis Pedidos",
            cta_url=orders_url,
        )

        return cls.send_email(to_email, subject, html, plain_text)
