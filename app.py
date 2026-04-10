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
from controller.report_controller import report_bp
from controller.sucursal_controller import sucursal_bp
from controller.rates_controller import rates_bp
from controller.stats_controller import stats_bp

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
app.register_blueprint(report_bp, url_prefix='/api/reports')
app.register_blueprint(sucursal_bp, url_prefix='/api/sucursales')
app.register_blueprint(rates_bp, url_prefix='/api/rates')
app.register_blueprint(stats_bp, url_prefix='/api/stats')


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
    try:
        return send_from_directory('views/client', f'{page}.html')
    except Exception:
        return redirect('/client/home')


@app.route('/auth/<page>')
def auth_page(page):
    if page in ['login', 'register', 'recover']:
        return send_from_directory('views/auth', f'{page}.html')
    return redirect('/auth/login')


@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory('public', filename)


@app.route('/components/<path:filename>')
def serve_component(filename):
    return send_from_directory('public/components', filename)


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/') or request.path.startswith('/auth/'):
        return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404
    return redirect('/client/home')


@app.errorhandler(500)
def server_error(e):
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500


if __name__ == '__main__':
    os.makedirs('public/assets/profile_pics', exist_ok=True)
    os.makedirs('public/assets/images', exist_ok=True)
    os.makedirs('public/assets/icons', exist_ok=True)
    os.makedirs('public/assets/comprobantes', exist_ok=True)
    os.makedirs('respaldos', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
