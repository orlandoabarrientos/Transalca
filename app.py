from flask import Flask, send_from_directory, session, request, redirect, url_for, jsonify, g
import os
import sys
import logging
import re
import secrets
import uuid
from werkzeug.exceptions import HTTPException
from werkzeug.serving import WSGIRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import (
    ALLOWED_ORIGINS,
    APP_DEBUG,
    APP_HOST,
    APP_PORT,
    SECRET_KEY,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
)
from controller.auth_controller import auth_bp
from controller.user_controller import user_bp
from controller.role_controller import role_bp
from controller.profile_controller import profile_bp
from controller.bitacora_controller import bitacora_bp
from controller.backup_controller import backup_bp
from controller.product_controller import product_bp
from controller.category_controller import category_bp
from controller.brand_controller import brand_bp
from controller.supplier_controller import supplier_bp
from controller.mechanic_controller import mechanic_bp
from controller.inventory_controller import inventory_bp
from controller.service_controller import service_bp
from controller.promotion_controller import promotion_bp
from controller.payment_controller import payment_bp
from controller.payment_method_controller import payment_method_bp
from controller.order_controller import order_bp
from controller.qr_controller import qr_bp
from controller.scanner_controller import scanner_bp
from controller.report_controller import report_bp
from controller.sucursal_controller import sucursal_bp
from controller.rates_controller import rates_bp
from controller.stats_controller import stats_bp
from controller.service_mechanic_controller import service_mechanic_bp
from controller.tasa_cambio_controller import tasa_bp
from controller.vehicle_controller import vehicle_bp
from controller.notification_controller import notification_bp
from controller.ticket_controller import ticket_bp
from controller.commission_controller import commission_bp
from controller.pricing_controller import pricing_bp
from controller.client_controller import client_bp
from controller.company_controller import company_bp
from controller.credit_controller import credit_bp
from controller.purchase_order_controller import purchase_order_bp
from controller.vehicle_log_controller import vehicle_log_bp
from componente_ia.api_asistente import asistente_bp
from model.bcv_sync_model import start_bcv_auto_sync_scheduler
from model.vehicle_log_model import start_bitacora_scheduler
from model.backup_model import start_backup_scheduler

app = Flask(__name__, static_folder='public', template_folder='views')
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = SESSION_COOKIE_SAMESITE
app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE

logger = logging.getLogger(__name__)
WSGIRequestHandler.server_version = "Transalca"
WSGIRequestHandler.sys_version = ""

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(role_bp, url_prefix='/api/roles')
app.register_blueprint(profile_bp, url_prefix='/api/profile')
app.register_blueprint(bitacora_bp, url_prefix='/api/bitacora')
app.register_blueprint(backup_bp, url_prefix='/api/backup')
app.register_blueprint(product_bp, url_prefix='/api/products')
app.register_blueprint(category_bp, url_prefix='/api/categories')
app.register_blueprint(brand_bp, url_prefix='/api/brands')
app.register_blueprint(supplier_bp, url_prefix='/api/suppliers')
app.register_blueprint(mechanic_bp, url_prefix='/api/mechanics')
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(service_bp, url_prefix='/api/services')
app.register_blueprint(promotion_bp, url_prefix='/api/promotions')
app.register_blueprint(payment_bp, url_prefix='/api/payments')
app.register_blueprint(payment_method_bp, url_prefix='/api/payment-methods')
app.register_blueprint(order_bp, url_prefix='/api/orders')
app.register_blueprint(qr_bp, url_prefix='/api/qr')
app.register_blueprint(scanner_bp, url_prefix='/api/scanner')
app.register_blueprint(report_bp, url_prefix='/api/reports')
app.register_blueprint(sucursal_bp, url_prefix='/api/sucursales')
app.register_blueprint(rates_bp, url_prefix='/api/rates')
app.register_blueprint(stats_bp, url_prefix='/api/stats')
app.register_blueprint(service_mechanic_bp, url_prefix='/api/service-mechanics')
app.register_blueprint(tasa_bp, url_prefix='/api/tasas')
app.register_blueprint(vehicle_bp, url_prefix='/api/vehicles')
app.register_blueprint(notification_bp, url_prefix='/api/notifications')
app.register_blueprint(ticket_bp, url_prefix='/api/tickets')
app.register_blueprint(commission_bp, url_prefix='/api/commissions')
app.register_blueprint(pricing_bp, url_prefix='/api/pricing')
app.register_blueprint(client_bp, url_prefix='/api/clients')
app.register_blueprint(company_bp, url_prefix='/api/companies')
app.register_blueprint(credit_bp, url_prefix='/api/credit')
app.register_blueprint(purchase_order_bp, url_prefix='/api/purchase-orders')
app.register_blueprint(vehicle_log_bp, url_prefix='/api/vehicle-log')
app.register_blueprint(asistente_bp, url_prefix='/api/asistente')


PUBLIC_CLIENT_PAGES = {'home', 'catalog'}
PUBLIC_API_PREFIXES = (
    '/api/products/active',
    '/api/categories/active',
    '/api/sucursales/active',
    '/api/services/active',
    '/api/rates',
    '/api/asistente',
)


SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(self), microphone=(), geolocation=(), payment=(), usb=(), fullscreen=(self)',
}


def _same_origin():
    scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
    return f"{scheme}://{request.host}".rstrip("/")


def _allowed_origin(origin):
    if not origin:
        return None
    origin = origin.rstrip("/")
    if origin == _same_origin() or origin in ALLOWED_ORIGINS:
        return origin
    return None


def _content_security_policy(nonce):
    return "; ".join([
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "img-src 'self' data: blob:",
        "font-src 'self' data:",
        "connect-src 'self'",
        f"script-src 'self' 'nonce-{nonce}'",
        "script-src-attr 'unsafe-inline'",
        f"style-src-elem 'self' 'nonce-{nonce}'",
        "style-src-attr 'unsafe-inline'",
        "manifest-src 'self'",
    ])


def _apply_html_nonce(response, nonce):
    content_type = response.headers.get('Content-Type', '')
    if 'text/html' not in content_type.lower():
        return response
    if response.direct_passthrough:
        response.direct_passthrough = False
    try:
        body = response.get_data(as_text=True)
    except RuntimeError:
        return response
    body = re.sub(r'<script(?![^>]*\bnonce=)', f'<script nonce="{nonce}"', body, flags=re.IGNORECASE)
    body = re.sub(r'<style(?![^>]*\bnonce=)', f'<style nonce="{nonce}"', body, flags=re.IGNORECASE)
    response.set_data(body)
    response.headers['Content-Length'] = str(len(response.get_data()))
    return response


def _error_response(status_code, message, error_id=None):
    payload = {"status": "error", "message": message}
    if error_id:
        payload["error_id"] = error_id
    return jsonify(payload), status_code


@app.before_request
def guard_public_access():
    g.csp_nonce = secrets.token_urlsafe(16)
    origin = request.headers.get('Origin')
    if origin and not _allowed_origin(origin):
        return jsonify({"status": "error", "message": "Origen no autorizado."}), 403
    if request.method == 'OPTIONS':
        return ('', 204)

    if request.path.startswith('/api/') and 'user_id' not in session:
        if any(request.path == p or request.path.startswith(p + '/') for p in PUBLIC_API_PREFIXES):
            return None
        return jsonify({"status": "error", "message": "Debe iniciar sesion."}), 401
    return None


@app.route('/')
def index():
    return redirect('/client/home')


@app.route('/admin/<page>')
def admin_page(page):
    allowed_admin_tipos = {'empleado', 'admin', 'vendedor', 'mecanico', 'soporte'}
    if 'user_id' not in session or session.get('user_tipo') not in allowed_admin_tipos:
        return redirect('/auth/login')
    try:
        return send_from_directory('views/admin', f'{page}.html')
    except Exception:
        return redirect('/admin/dashboard')




@app.route('/client/<page>')
def client_page(page):
    if page not in PUBLIC_CLIENT_PAGES and 'user_id' not in session:
        next_path = request.full_path if request.query_string else request.path
        return redirect(url_for('auth.login_page', next=next_path.rstrip('?')))
    try:
        return send_from_directory('views/client', f'{page}.html')
    except Exception:
        return redirect('/client/home')


@app.route('/scanner')
def scanner_page():
    if 'user_id' not in session:
        next_path = request.full_path if request.query_string else request.path
        next_path = next_path.rstrip('?')
        return redirect(url_for('auth.login_page', next=next_path))
    return send_from_directory('views/client', 'scanner.html')


@app.route('/auth/<page>')
def auth_page(page):
    if page in ['login', 'register', 'recover']:
        return send_from_directory('views/auth', f'{page}.html')
    return redirect('/auth/login')


@app.route('/components/<path:filename>')
def serve_component(filename):
    return send_from_directory('public/components', filename)


@app.route('/componente_ia/<path:filename>')
def serve_componente_ia(filename):
    return send_from_directory('componente_ia', filename)


@app.errorhandler(400)
def bad_request(e):
    return _error_response(400, "Solicitud invalida.")


@app.errorhandler(401)
def unauthorized(e):
    return _error_response(401, "Debe iniciar sesion.")


@app.errorhandler(403)
def forbidden(e):
    return _error_response(403, "No autorizado.")


@app.errorhandler(404)
def not_found(e):
    if (
        request.path.startswith('/api/')
        or request.path.startswith('/auth/')
        or request.path.startswith('/public/')
        or request.path.startswith('/components/')
        or request.path.startswith('/componente_ia/')
    ):
        return _error_response(404, "Ruta no encontrada.")
    return redirect('/client/home')


@app.errorhandler(405)
def method_not_allowed(e):
    return _error_response(405, "Metodo no permitido.")


@app.errorhandler(Exception)
def server_error(e):
    if isinstance(e, HTTPException):
        return e
    error_id = uuid.uuid4().hex[:12]
    logger.exception("Error interno no controlado. id=%s", error_id)
    return _error_response(500, "Error interno del servidor.", error_id)


@app.after_request
def apply_response_headers(response):
    nonce = getattr(g, 'csp_nonce', secrets.token_urlsafe(16))
    _apply_html_nonce(response, nonce)
    response.headers['Content-Security-Policy'] = _content_security_policy(nonce)
    for key, value in SECURITY_HEADERS.items():
        response.headers[key] = value
    response.headers['Server'] = 'Transalca'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    origin = _allowed_origin(request.headers.get('Origin'))
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin, Cookie' if response.headers.get('Vary') else 'Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'

    path = request.path or ''
    if path.startswith('/public/') or path.startswith('/components/') or path.startswith('/admin/') or path.startswith('/client/') or path.startswith('/auth/') or path.startswith('/api/') or path.startswith('/componente_ia/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    os.makedirs('public/assets/profile_pics', exist_ok=True)
    os.makedirs('public/assets/images', exist_ok=True)
    os.makedirs('public/assets/icons', exist_ok=True)
    os.makedirs('public/assets/comprobantes', exist_ok=True)
    os.makedirs('respaldos', exist_ok=True)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not APP_DEBUG:
        start_bcv_auto_sync_scheduler()
        start_bitacora_scheduler()
        start_backup_scheduler()
    app.run(debug=APP_DEBUG, host=APP_HOST, port=APP_PORT)
