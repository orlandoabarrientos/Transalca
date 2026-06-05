import pymysql
import threading
from config.config import DB_CONFIG_MANTENIMIENTO, DB_CONFIG_TRANSALCA


class Connection:
    _local = threading.local()

    def __init__(self):
        pass

    def _init_mantenimiento(self):
        try:
            Connection._local.mantenimiento = pymysql.connect(
                host=DB_CONFIG_MANTENIMIENTO["host"],
                port=DB_CONFIG_MANTENIMIENTO["port"],
                user=DB_CONFIG_MANTENIMIENTO["user"],
                password=DB_CONFIG_MANTENIMIENTO["password"],
                database=DB_CONFIG_MANTENIMIENTO["database"],
                charset=DB_CONFIG_MANTENIMIENTO["charset"],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        except pymysql.MySQLError:
            Connection._local.mantenimiento = None

    def _init_transalca(self):
        try:
            Connection._local.transalca = pymysql.connect(
                host=DB_CONFIG_TRANSALCA["host"],
                port=DB_CONFIG_TRANSALCA["port"],
                user=DB_CONFIG_TRANSALCA["user"],
                password=DB_CONFIG_TRANSALCA["password"],
                database=DB_CONFIG_TRANSALCA["database"],
                charset=DB_CONFIG_TRANSALCA["charset"],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
        except pymysql.MySQLError:
            Connection._local.transalca = None

    def con_mantenimiento(self):
        if not hasattr(Connection._local, 'mantenimiento') or Connection._local.mantenimiento is None or not getattr(Connection._local.mantenimiento, 'open', False):
            self._init_mantenimiento()
        if hasattr(Connection._local, 'mantenimiento') and Connection._local.mantenimiento is not None:
            try:
                Connection._local.mantenimiento.ping(reconnect=True)
            except Exception:
                self._init_mantenimiento()
        if not hasattr(Connection._local, 'mantenimiento') or Connection._local.mantenimiento is None:
            raise Exception("No se pudo conectar a la base de datos de mantenimiento")
        return Connection._local.mantenimiento

    def con_transalca(self):
        if not hasattr(Connection._local, 'transalca') or Connection._local.transalca is None or not getattr(Connection._local.transalca, 'open', False):
            self._init_transalca()
        if hasattr(Connection._local, 'transalca') and Connection._local.transalca is not None:
            try:
                Connection._local.transalca.ping(reconnect=True)
            except Exception:
                self._init_transalca()
        if not hasattr(Connection._local, 'transalca') or Connection._local.transalca is None:
            raise Exception("No se pudo conectar a la base de datos de transalca")
        return Connection._local.transalca

    def _set_session_variables(self, cursor):
        from flask import has_request_context, session, request
        user_id = 1
        ip = '127.0.0.1'
        if has_request_context():
            user_id = session.get('user_id', 1)
            ip = request.remote_addr or '127.0.0.1'
        cursor.execute("SET @current_usuario_id = %s, @current_ip = %s", (user_id, ip))

    def execute_query(self, db, sql, params=None):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        cursor = conn.cursor()
        self._set_session_variables(cursor)
        cursor.execute(sql, params or ())
        return cursor

    def fetch_all(self, db, sql, params=None):
        cursor = self.execute_query(db, sql, params)
        return cursor.fetchall()

    def fetch_one(self, db, sql, params=None):
        cursor = self.execute_query(db, sql, params)
        return cursor.fetchone()

    def insert(self, db, sql, params=None):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        cursor = conn.cursor()
        self._set_session_variables(cursor)
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid

    def update(self, db, sql, params=None):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        cursor = conn.cursor()
        self._set_session_variables(cursor)
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.rowcount

    def delete(self, db, sql, params=None):
        return self.update(db, sql, params)

    def begin_transaction(self, db):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        conn.begin()
        return conn

    def commit_transaction(self, db):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        conn.commit()

    def rollback_transaction(self, db):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        conn.rollback()

    def email_exists_globally(self, email, exclude=None):
        normalized = (email or '').strip().lower()
        if not normalized:
            return False
        exclude = exclude or {}
        
        class_name = self.__class__.__name__
        tables_to_check = []
        if class_name == 'SucursalModel' or 'sucursal_id' in exclude:
            tables_to_check.append("sucursales")
        elif class_name == 'SupplierModel' or 'proveedor_rif' in exclude:
            tables_to_check.append("proveedores")
        elif class_name in ('ClientModel', 'CompanyModel', 'UserModel', 'AuthModel', 'ProfileModel') or any(k in exclude for k in ('cliente_cedula', 'usuario_cedula', 'usuario_id')):
            tables_to_check.append("clientes")
            tables_to_check.append("usuarios")
        else:
            tables_to_check = ["usuarios", "clientes", "proveedores", "sucursales"]

        checks = [
            ("mantenimiento", "usuarios", "email", "id", exclude.get("usuario_id"), "cedula", exclude.get("usuario_cedula")),
            ("transalca", "clientes", "email", "cedula", exclude.get("cliente_cedula"), None, None),
            ("transalca", "proveedores", "email", "rif", exclude.get("proveedor_rif"), None, None),
            ("transalca", "sucursales", "email", "id", exclude.get("sucursal_id"), None, None),
        ]
        for db, table, column, key, excluded_value, second_key, second_excluded_value in checks:
            if table not in tables_to_check:
                continue
            try:
                where = [f"LOWER({column}) = %s", "estado = 1"]
                params = [normalized]
                if excluded_value not in (None, ''):
                    where.append(f"{key} != %s")
                    params.append(excluded_value)
                if second_key and second_excluded_value not in (None, ''):
                    where.append(f"{second_key} != %s")
                    params.append(second_excluded_value)
                row = self.fetch_one(
                    db,
                    f"SELECT {key} FROM {table} WHERE {' AND '.join(where)} LIMIT 1",
                    tuple(params)
                )
                if row:
                    return True
            except Exception:
                continue
        return False
