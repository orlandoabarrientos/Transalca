from flask import Flask, send_from_directory, session, request, redirect, url_for, jsonify
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import SECRET_KEY
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
from controller.maintenance_controller import maintenance_bp
from controller.pricing_controller import pricing_bp
from controller.client_controller import client_bp
from controller.fuel_controller import fuel_bp
from controller.vehicle_log_controller import vehicle_log_bp
from services.bcv_sync_service import start_bcv_auto_sync_scheduler

app = Flask(__name__, static_folder='public', template_folder='views')
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

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
app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
app.register_blueprint(pricing_bp, url_prefix='/api/pricing')
app.register_blueprint(client_bp, url_prefix='/api/clients')
app.register_blueprint(fuel_bp, url_prefix='/api/fuel')
app.register_blueprint(vehicle_log_bp, url_prefix='/api/vehicle-log')


PUBLIC_CLIENT_PAGES = {'home', 'catalog'}
PUBLIC_API_PREFIXES = (
    '/api/products/active',
    '/api/categories/active',
    '/api/sucursales/active',
    '/api/services/active',
    '/api/rates',
)


@app.before_request
def guard_public_access():
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
    if 'user_id' not in session or session.get('user_tipo') != 'empleado':
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


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/') or request.path.startswith('/auth/'):
        return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404
    return redirect('/client/home')


@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500


if __name__ == '__main__':
    debug_mode = True
    os.makedirs('public/assets/profile_pics', exist_ok=True)
    os.makedirs('public/assets/images', exist_ok=True)
    os.makedirs('public/assets/icons', exist_ok=True)
    os.makedirs('public/assets/comprobantes', exist_ok=True)
    os.makedirs('respaldos', exist_ok=True)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not debug_mode:
        start_bcv_auto_sync_scheduler()
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
