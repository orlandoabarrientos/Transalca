from flask import Blueprint, request, jsonify, session
from model.product_model import ProductModel
import os
import time
from werkzeug.utils import secure_filename

from config.validation import SELECT_TAMPER_MESSAGE, ValidationError, optional_text

product_bp = Blueprint('products', __name__)
model = ProductModel()

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'public', 'assets', 'product_imgs')

def _save_image(file, codigo):
    if not file or file.filename == '':
        return None, None
    allowed = {'png', 'jpg', 'jpeg', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed:
        return None, "Solo se permiten imagenes png, jpg, jpeg o webp."
    if file.mimetype not in {'image/png', 'image/jpeg', 'image/webp', 'image/jpg'}:
        return None, "El archivo no es una imagen valida."
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        return None, "La imagen no debe superar los 2MB."
    safe_codigo = secure_filename(codigo)
    filename = f"prod_{safe_codigo}_{int(time.time())}.{ext}"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return filename, None


@product_bp.route('/', methods=['GET'])
def get_all():
    try:
        estado = request.args.get('estado')
        if estado is not None:
            if estado not in ('0', '1', 0, 1):
                return jsonify({"status": "error", "message": SELECT_TAMPER_MESSAGE}), 400
            products = model.ejecutar("get_by_estado", int(estado))
            return jsonify({"status": "success", "data": products})

        page_val = request.args.get('page')
        q = request.args.get('q', '').strip()
        if page_val is not None:
            try:
                page = int(page_val)
                per_page = int(request.args.get('per_page', 10))
            except (ValueError, TypeError):
                page = 1
                per_page = 10
            paginated = model.ejecutar("get_all_paginated", page, per_page, q if q else None)
            return jsonify({
                "status": "success",
                "data": paginated["data"],
                "total": paginated["total"],
                "page": paginated["page"],
                "per_page": paginated["per_page"],
                "pages": paginated["pages"]
            })

        products = model.ejecutar("get_all")
        return jsonify({"status": "success", "data": products})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/active', methods=['GET'])
def get_active():
    try:
        if request.args.get('page') is not None or request.args.get('per_page') is not None:
            try:
                page = max(1, int(request.args.get('page', 1)))
            except (ValueError, TypeError):
                page = 1
            try:
                per_page = max(1, min(100, int(request.args.get('per_page', 30))))
            except (ValueError, TypeError):
                per_page = 30

            branch = None
            branch_raw = request.args.get('branch')
            if branch_raw:
                try:
                    branch = int(branch_raw)
                except (ValueError, TypeError):
                    branch = None

            sort = request.args.get('sort') if request.args.get('sort') in ('price_asc', 'price_desc', 'name') else None
            paginated = model.ejecutar("get_active_paginated", 
                page,
                per_page,
                category=(request.args.get('category') or '').strip()[:150] or None,
                branch=branch,
                q=(request.args.get('q') or '').strip()[:80] or None,
                sort=sort
            )
            return jsonify({
                "status": "success",
                "data": paginated["data"],
                "total": paginated["total"],
                "page": paginated["page"],
                "per_page": paginated["per_page"],
                "pages": paginated["pages"]
            })
        return jsonify({"status": "success", "data": model.ejecutar("get_active")})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/check-unique', methods=['GET'])
def check_unique():
    try:
        codigo = optional_text({}, 'codigo', request.args.get('value'), 'El codigo', max_len=50, allow_serial=True).upper()
        exclude = request.args.get('exclude') or None
        if not codigo:
            return jsonify({"status": "error", "message": "El codigo es obligatorio"}), 400
        return jsonify({"status": "success", "exists": model.ejecutar("codigo_exists", codigo, exclude)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo validar el codigo"}), 500


@product_bp.route('/detail/<path:codigo>', methods=['GET'])
def get_one(codigo):
    try:
        product = model.ejecutar("get_by_codigo", codigo)
        if product:
            return jsonify({"status": "success", "data": product})
        return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cargar el producto"}), 500


@product_bp.route('/category/<path:categoria>', methods=['GET'])
def get_by_category(categoria):
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_by_category", categoria)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/brand/<path:marca>', methods=['GET'])
def get_by_brand(marca):
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_by_brand", marca)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/search', methods=['GET'])
def search():
    try:
        q = request.args.get('q', '')[:80]
        return jsonify({"status": "success", "data": model.ejecutar("search", q)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo buscar productos"}), 500


@product_bp.route('/sucursal/<int:sid>', methods=['GET'])
def get_by_sucursal(sid):
    try:
        return jsonify({"status": "success", "data": model.ejecutar("get_by_sucursal", sid)})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar los productos"}), 500


@product_bp.route('/', methods=['POST'])
def create():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if request.is_json:
            raw = request.get_json() or {}
        else:
            raw = request.form.to_dict()
            raw['sucursal_ids'] = request.form.getlist('sucursal_ids')
        clean = model.ejecutar("validate", raw)
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename != '':
            filename, img_err = _save_image(imagen_file, clean['codigo'])
            if img_err:
                return jsonify({"status": "error", "message": "Error al subir la imagen", "errors": {"imagen": img_err}}), 400
            raw['imagen'] = filename
        elif str(raw.get('imagen_remove') or '').strip() == '1':
            raw['imagen'] = 'default_product.png'
        model.ejecutar("create", raw)
        return jsonify({"status": "success", "message": "Producto registrado correctamente", "codigo": clean['codigo']})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar el producto"}), 500


@product_bp.route('/update', methods=['PUT'])
def update():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        if request.is_json:
            raw = request.get_json() or {}
        else:
            raw = request.form.to_dict()
            raw['sucursal_ids'] = request.form.getlist('sucursal_ids')
        old_codigo = raw.get('old_codigo', '')
        clean = model.ejecutar("validate", raw, old_codigo)
        imagen_file = request.files.get('imagen')
        if imagen_file and imagen_file.filename != '':
            filename, img_err = _save_image(imagen_file, clean['codigo'])
            if img_err:
                return jsonify({"status": "error", "message": "Error al subir la imagen", "errors": {"imagen": img_err}}), 400
            raw['imagen'] = filename
            existing = model.ejecutar("get_by_codigo", old_codigo)
            if existing:
                old_img = existing.get('imagen')
                if old_img and old_img != 'default_product.png':
                    old_path = os.path.join(UPLOAD_FOLDER, old_img)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
        elif str(raw.get('imagen_remove') or '').strip() == '1':
            raw['imagen'] = 'default_product.png'
            existing = model.ejecutar("get_by_codigo", old_codigo)
            if existing:
                old_img = existing.get('imagen')
                if old_img and old_img != 'default_product.png':
                    old_path = os.path.join(UPLOAD_FOLDER, old_img)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass
        model.ejecutar("update_product", old_codigo, raw)
        return jsonify({"status": "success", "message": "Producto modificado correctamente"})
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.message, "errors": e.errors}), 400
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo modificar el producto"}), 500


@product_bp.route('/toggle', methods=['PUT'])
def toggle():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json() or {}
        codigo = (data.get('codigo') or '').strip()
        product = model.ejecutar("get_by_codigo", codigo)
        if not product:
            return jsonify({"status": "error", "message": "Producto no encontrado"}), 404
        model.ejecutar("soft_delete", codigo)

        return jsonify({"status": "success", "message": "Producto eliminado correctamente"})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo cambiar el estado del producto"}), 500
