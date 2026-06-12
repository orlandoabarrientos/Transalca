from flask import Blueprint, request, jsonify, session, Response
from model.purchase_order_model import PurchaseOrderModel

from controller._guards import require_login, is_employee, deny
from decimal import Decimal
from datetime import datetime
import logging
import uuid

purchase_order_bp = Blueprint('purchase_orders', __name__)
model = PurchaseOrderModel()
logger = logging.getLogger(__name__)



@purchase_order_bp.route('/', methods=['GET'])
def get_all():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()

        search = request.args.get('q')
        estado = request.args.get('estado')
        orders = model.ejecutar("get_all", search, estado)
        return jsonify({"status": "success", "data": orders})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las ordenes de compra."}), 500


@purchase_order_bp.route('/stats', methods=['GET'])
def stats():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()

        stats_data = model.ejecutar("get_stats")
        return jsonify({"status": "success", "data": stats_data})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudieron cargar las estadisticas."}), 500


@purchase_order_bp.route('/', methods=['POST'])
def create():
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()

        data = request.get_json() or {}
        errors = {}


        proveedor_rif = (data.get('proveedor_rif') or '').strip()
        if not proveedor_rif:
            errors['proveedor_rif'] = "El proveedor es obligatorio."

        sucursal_id = data.get('sucursal_id')
        if not sucursal_id:
            errors['sucursal_id'] = "La sucursal destino es obligatoria."

        items = data.get('items') or []
        if not items:
            errors['items'] = "Debe agregar al menos un producto."
        else:
            for idx, item in enumerate(items):
                p_code = (item.get('producto_codigo') or '').strip()
                p_qty = item.get('cantidad')
                p_price = item.get('precio_unitario')

                if not p_code:
                    errors[f'items_{idx}_code'] = "Codigo de producto obligatorio."
                try:
                    qty = int(p_qty)
                    if qty <= 0:
                        errors[f'items_{idx}_qty'] = "La cantidad debe ser mayor a cero."
                except (ValueError, TypeError):
                    errors[f'items_{idx}_qty'] = "La cantidad no es valida."

                try:
                    price = Decimal(str(p_price).replace(',', '.')).quantize(Decimal("0.01"))
                    if price < 0:
                        errors[f'items_{idx}_price'] = "El precio no puede ser negativo."
                except Exception:
                    errors[f'items_{idx}_price'] = "El precio no es valido."

        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion.", "errors": errors}), 400

        result = model.ejecutar("create", data)
        if not result.get('ok'):
            return jsonify({"status": "error", "message": result.get('message')}), 400

        if session.get('user_id'):



            pass

        return jsonify({"status": "success", "message": result.get('message'), "data": {"id": result.get('id')}})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo registrar la orden de compra."}), 500


@purchase_order_bp.route('/<int:order_id>', methods=['GET'])
def get_one_order(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()

        order = model.ejecutar("get_by_id", order_id)
        if not order:
            return jsonify({"status": "error", "message": "Orden de compra no encontrada."}), 404

        return jsonify({"status": "success", "data": order})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo obtener la orden de compra."}), 500


@purchase_order_bp.route('/<int:order_id>/buy', methods=['POST'])
def mark_as_bought(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()

        result = model.ejecutar("mark_as_bought", order_id)
        if not result.get('ok'):
            return jsonify({"status": "error", "message": result.get('message')}), 400

        if session.get('user_id'):



            pass

        return jsonify({"status": "success", "message": result.get('message')})
    except Exception:
        return jsonify({"status": "error", "message": "No se pudo completar la transaccion."}), 500


@purchase_order_bp.route('/<int:order_id>/pdf', methods=['GET'])
def get_pdf(order_id):
    try:
        auth = require_login()
        if auth:
            return auth
        if not is_employee():
            return deny()

        order = model.ejecutar("get_by_id", order_id)
        if not order:
            return jsonify({"status": "error", "message": "Orden de compra no encontrada."}), 404

        from fpdf import FPDF

        class CustomPDF(FPDF):
            def header(self):

                self.set_fill_color(26, 54, 93)
                self.rect(0, 0, 210, 40, 'F')

                self.set_text_color(255, 255, 255)
                self.set_font("helvetica", "B", 22)
                self.cell(0, 10, "TRANSALCA C.A.", new_x="LMARGIN", new_y="NEXT", align="L")
                self.set_font("helvetica", "B", 10)
                self.cell(0, 5, "RIF: J-50012345-0 | Soluciones en Repuestos y Servicios", new_x="LMARGIN", new_y="NEXT", align="L")

                self.set_y(12)
                self.set_font("helvetica", "B", 16)
                self.cell(0, 10, "ORDEN DE COMPRA", new_x="LMARGIN", align="R")
                self.set_y(22)
                self.set_font("helvetica", "B", 11)
                self.cell(0, 5, f"NUMERO: #{order['id']:05d}", new_x="LMARGIN", align="R")


                self.set_y(48)

            def footer(self):
                self.set_y(-15)
                self.set_font("helvetica", "I", 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f"Pagina {self.page_no()} de {{nb}} | Transalca C.A. - Control Interno", align="C")

        pdf = CustomPDF()
        pdf.set_margins(15, 15, 15)
        pdf.alias_nb_pages()
        pdf.add_page()


        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "B", 10)


        fecha_str = order['fecha'].strftime('%d/%m/%Y %H:%M') if isinstance(order['fecha'], datetime) else str(order['fecha'])
        pdf.cell(90, 5, f"Fecha de Emision: {fecha_str}")
        pdf.cell(90, 5, f"Estado de la Orden: {order['estado'].upper()}", align="R")
        pdf.ln(10)


        start_y = pdf.get_y()


        pdf.set_fill_color(240, 244, 248)
        pdf.rect(15, start_y, 85, 42, 'F')
        pdf.set_xy(17, start_y + 2)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(26, 54, 93)
        pdf.cell(81, 5, "PROVEEDOR", new_x="LEFT", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 9)
        pdf.cell(81, 4, f"Nombre: {order['proveedor_nombre']}", new_x="LEFT", new_y="NEXT")
        pdf.cell(81, 4, f"RIF: {order['proveedor_rif']}", new_x="LEFT", new_y="NEXT")
        pdf.cell(81, 4, f"Telefono: {order['proveedor_telefono'] or 'N/A'}", new_x="LEFT", new_y="NEXT")
        pdf.cell(81, 4, f"Email: {order['proveedor_email'] or 'N/A'}", new_x="LEFT", new_y="NEXT")


        pdf.set_fill_color(240, 244, 248)
        pdf.rect(110, start_y, 85, 42, 'F')
        pdf.set_xy(112, start_y + 2)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(26, 54, 93)
        pdf.cell(81, 5, "SUCURSAL DESTINO", new_x="LEFT", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 9)
        pdf.cell(81, 4, f"Nombre: {order['sucursal_nombre']}", new_x="LEFT", new_y="NEXT")
        pdf.cell(81, 4, f"Direccion: {order['sucursal_direccion'] or 'N/A'}", new_x="LEFT", new_y="NEXT")

        pdf.set_y(start_y + 48)


        if order.get('observaciones'):
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 5, "Observaciones:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "I", 9)
            pdf.multi_cell(0, 5, order['observaciones'])
            pdf.ln(5)


        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(26, 54, 93)


        pdf.cell(30, 8, "CODIGO", border=1, align="C", fill=True)
        pdf.cell(90, 8, "PRODUCTO", border=1, align="L", fill=True)
        pdf.cell(20, 8, "CANT.", border=1, align="C", fill=True)
        pdf.cell(20, 8, "P. UNIT.", border=1, align="R", fill=True)
        pdf.cell(20, 8, "SUBTOTAL", border=1, align="R", fill=True)
        pdf.ln(8)


        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(0, 0, 0)
        for row in order.get('detalles', []):
            pdf.cell(30, 7, str(row['producto_codigo']), border=1, align="C")
            pdf.cell(90, 7, str(row['producto_nombre'])[:40], border=1, align="L")
            pdf.cell(20, 7, str(row['cantidad']), border=1, align="C")
            pdf.cell(20, 7, f"${row['precio_unitario']:.2f}", border=1, align="R")
            pdf.cell(20, 7, f"${row['subtotal']:.2f}", border=1, align="R")
            pdf.ln(7)


        pdf.set_font("helvetica", "B", 10)
        pdf.cell(140, 8, "")
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(234, 88, 12)
        pdf.cell(20, 8, "TOTAL", border=1, align="C", fill=True)
        pdf.cell(20, 8, f"${order['total']:.2f}", border=1, align="R", fill=True)
        pdf.ln(10)

        output = bytearray(pdf.output())
        filename = f"orden_compra_{order_id:05d}.pdf"
        return Response(bytes(output), mimetype="application/pdf", headers={"Content-Disposition": f"attachment;filename={filename}"})
    except Exception:
        error_id = uuid.uuid4().hex[:12]
        logger.exception("No se pudo generar el PDF de orden de compra %s. id=%s", order_id, error_id)
        return jsonify({
            "status": "error",
            "message": "No se pudo generar el PDF de la orden de compra.",
            "error_id": error_id
        }), 500
