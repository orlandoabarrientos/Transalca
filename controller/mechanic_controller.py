from flask import Blueprint, request, jsonify, session
from model.mechanic_model import MechanicModel
from model.bitacora_model import BitacoraModel

mechanic_bp = Blueprint('mechanics', __name__)
model = MechanicModel()
bitacora = BitacoraModel()


@mechanic_bp.route('/', methods=['GET'])
def get_all():
    try:
        return jsonify({"status": "success", "data": model.get_all()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@mechanic_bp.route('/<path:cedula>', methods=['GET'])
def get_one(cedula):
    try:
        item = model.get_by_cedula(cedula)
        if item:
            return jsonify({"status": "success", "data": item})
        return jsonify({"status": "error", "message": "Mecanico no encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@mechanic_bp.route('/history/<path:cedula>', methods=['GET'])
def get_history(cedula):
    try:
        return jsonify({"status": "success", "data": model.get_service_history(cedula)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@mechanic_bp.route('/', methods=['POST'])
def create():
    try:
        import os
        from werkzeug.utils import secure_filename
        import time
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.form.to_dict()
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre es obligatorio'
        if not data.get('apellido') or len(data['apellido'].strip()) < 2:
            errors['apellido'] = 'El apellido es obligatorio'
        if not data.get('cedula'):
            errors['cedula'] = 'La cédula es obligatoria'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        if model.cedula_exists(data['cedula'].strip()):
            return jsonify({"status": "error", "message": "La cedula ya esta registrada", "errors": {"cedula": "La cedula ya esta registrada"}}), 400
        if 'foto_perfil' in request.files and request.files['foto_perfil'].filename != '':
            file = request.files['foto_perfil']
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"mec_{data['cedula'].strip()}_{int(time.time()*1000)}.{ext}"
            file.save(os.path.join('public', 'assets', 'profile_pics', secure_filename(filename)))
            data['foto_perfil'] = filename
        model.create(data)
        bitacora.log_action(session['user_id'], 'CREAR', 'MECANICOS',
            f"Mecanico creado: {data['cedula']}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico creado", "cedula": data['cedula'].strip()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@mechanic_bp.route('/update', methods=['PUT'])
def update():
    try:
        import os
        from werkzeug.utils import secure_filename
        import time
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.form.to_dict()
        old_cedula = data.get('old_cedula', '')
        errors = {}
        if not data.get('nombre') or len(data['nombre'].strip()) < 2:
            errors['nombre'] = 'El nombre es obligatorio'
        if not data.get('apellido') or len(data['apellido'].strip()) < 2:
            errors['apellido'] = 'El apellido es obligatorio'
        if not data.get('cedula'):
            errors['cedula'] = 'La cédula es obligatoria'
        if not old_cedula:
            errors['old_cedula'] = 'Identificador requerido'
        if errors:
            return jsonify({"status": "error", "message": "Errores de validacion", "errors": errors}), 400
        new_cedula = data['cedula'].strip()
        if new_cedula != old_cedula and model.cedula_exists(new_cedula):
            return jsonify({"status": "error", "message": "La cedula ya esta registrada", "errors": {"cedula": "La cedula ya esta registrada"}}), 400
        if 'foto_perfil' in request.files and request.files['foto_perfil'].filename != '':
            file = request.files['foto_perfil']
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"mec_{new_cedula}_{int(time.time()*1000)}.{ext}"
            file.save(os.path.join('public', 'assets', 'profile_pics', secure_filename(filename)))
            data['foto_perfil'] = filename
        model.update_mechanic(old_cedula, data)
        bitacora.log_action(session['user_id'], 'MODIFICAR', 'MECANICOS',
            f"Mecanico modificado: {old_cedula}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico actualizado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@mechanic_bp.route('/delete', methods=['DELETE'])
def delete():
    try:
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "No autorizado"}), 401
        data = request.get_json()
        cedula = data.get('cedula', '')
        model.soft_delete(cedula)
        bitacora.log_action(session['user_id'], 'ELIMINAR', 'MECANICOS',
            f"Mecanico desactivado: {cedula}", request.remote_addr)
        return jsonify({"status": "success", "message": "Mecanico desactivado"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
