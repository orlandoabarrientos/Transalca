from flask import send_from_directory, session, request, redirect, url_for

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
from controller.modulo_controller import modulo_bp
from componente_ia.api_asistente import asistente_bp
from model.modulo_model import ModuloModel


PUBLIC_CLIENT_PAGES = {'home', 'catalog'}
_modulo_model = ModuloModel()

BLUEPRINTS = (
    (auth_bp, '/auth'),
    (user_bp, '/api/users'),
    (role_bp, '/api/roles'),
    (profile_bp, '/api/profile'),
    (bitacora_bp, '/api/bitacora'),
    (backup_bp, '/api/backup'),
    (product_bp, '/api/products'),
    (category_bp, '/api/categories'),
    (brand_bp, '/api/brands'),
    (supplier_bp, '/api/suppliers'),
    (mechanic_bp, '/api/mechanics'),
    (inventory_bp, '/api/inventory'),
    (service_bp, '/api/services'),
    (promotion_bp, '/api/promotions'),
    (payment_bp, '/api/payments'),
    (payment_method_bp, '/api/payment-methods'),
    (order_bp, '/api/orders'),
    (qr_bp, '/api/qr'),
    (scanner_bp, '/api/scanner'),
    (report_bp, '/api/reports'),
    (sucursal_bp, '/api/sucursales'),
    (rates_bp, '/api/rates'),
    (stats_bp, '/api/stats'),
    (service_mechanic_bp, '/api/service-mechanics'),
    (tasa_bp, '/api/tasas'),
    (vehicle_bp, '/api/vehicles'),
    (notification_bp, '/api/notifications'),
    (ticket_bp, '/api/tickets'),
    (commission_bp, '/api/commissions'),
    (pricing_bp, '/api/pricing'),
    (client_bp, '/api/clients'),
    (company_bp, '/api/companies'),
    (credit_bp, '/api/credit'),
    (purchase_order_bp, '/api/purchase-orders'),
    (vehicle_log_bp, '/api/vehicle-log'),
    (modulo_bp, '/api/modulos'),
    (asistente_bp, '/api/asistente'),
)


def _can_view_admin_page(page):
    if 'Administrador' in (session.get('roles') or []):
        return True
    try:
        modulo = _modulo_model.ejecutar("get_by_ruta", f"/admin/{page}")
    except Exception:
        return True
    if not modulo or not modulo.get('estado'):
        return True
    if modulo.get('publico'):
        return True
    perms = session.get('permisos') or {}
    return bool((perms.get(modulo['nombre']) or {}).get('leer'))


def register_blueprints(app):
    for blueprint, prefix in BLUEPRINTS:
        app.register_blueprint(blueprint, url_prefix=prefix)


def register_page_routes(app):
    @app.route('/')
    def index():
        return redirect('/client/home')

    @app.route('/admin/<page>')
    def admin_page(page):
        allowed_admin_tipos = {'empleado', 'admin', 'vendedor', 'mecanico', 'soporte'}
        if 'user_id' not in session or session.get('user_tipo') not in allowed_admin_tipos:
            return redirect('/auth/login')
        if not _can_view_admin_page(page):
            return redirect('/admin/dashboard')
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


def register_routes(app):
    register_blueprints(app)
    register_page_routes(app)
