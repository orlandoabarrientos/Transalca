from flask import Flask, session, request, redirect, jsonify, g
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
from config.validation import ValidationError
from routes import register_routes
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

register_routes(app)


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


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400


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
