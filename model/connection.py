import logging
import pymysql
import re
import threading
from config.config import DB_CONFIG_MANTENIMIENTO, DB_CONFIG_TRANSALCA


logger = logging.getLogger(__name__)
SQL_IDENTIFIER_RE = re.compile(r'^[A-Za-z0-9_]+$')


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

    def sql_identifier(self, value, allowed):
        if value not in allowed or not SQL_IDENTIFIER_RE.fullmatch(str(value or '')):
            raise ValueError("Identificador SQL no permitido.")
        return "`" + value + "`"

    def sql_identifier_list(self, values, allowed):
        return ", ".join(self.sql_identifier(value, allowed) for value in values)

    def sql_placeholders(self, count):
        return ", ".join(["%s"] * count)

    def sql_assignments(self, values, allowed):
        return ", ".join(self.sql_identifier(value, allowed) + " = %s" for value in values)

    def build_insert_sql(self, table, columns, allowed_tables, allowed_columns):
        table_sql = self.sql_identifier(table, allowed_tables)
        columns_sql = self.sql_identifier_list(columns, allowed_columns)
        values_sql = self.sql_placeholders(len(columns))
        return " ".join(["INSERT INTO", table_sql, "(" + columns_sql + ")", "VALUES", "(" + values_sql + ")"])

    def build_update_by_key_sql(self, table, columns, key_column, allowed_tables, allowed_columns):
        table_sql = self.sql_identifier(table, allowed_tables)
        assignments_sql = self.sql_assignments(columns, allowed_columns)
        key_sql = self.sql_identifier(key_column, allowed_columns)
        return " ".join(["UPDATE", table_sql, "SET", assignments_sql, "WHERE", key_sql, "= %s"])

    def build_upsert_sql(self, table, columns, key_column, allowed_tables, allowed_columns):
        table_sql = self.sql_identifier(table, allowed_tables)
        columns_sql = self.sql_identifier_list(columns, allowed_columns)
        values_sql = self.sql_placeholders(len(columns))
        update_columns = [column for column in columns if column != key_column]
        update_sql = ", ".join(
            self.sql_identifier(column, allowed_columns) + "=VALUES(" + self.sql_identifier(column, allowed_columns) + ")"
            for column in update_columns
        )
        return " ".join([
            "INSERT INTO", table_sql, "(" + columns_sql + ")", "VALUES", "(" + values_sql + ")",
            "ON DUPLICATE KEY UPDATE", update_sql
        ])

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
            tables_to_check.append("cliente")
            tables_to_check.append("usuarios")
        else:
            tables_to_check = ["usuarios", "clientes", "proveedores", "sucursales"]

        checks = [
            ("usuarios", "mantenimiento", "SELECT id FROM usuarios WHERE LOWER(email) = %s AND estado = 1", [
                (" AND id != %s", exclude.get("usuario_id")),
                (" AND cedula != %s", exclude.get("usuario_cedula")),
            ]),
            ("cliente", "transalca", "SELECT identificador_cliente FROM cliente WHERE LOWER(correo_cliente) = %s AND estado = 1", [
                (" AND identificador_cliente != %s", exclude.get("cliente_cedula")),
            ]),
            ("proveedores", "transalca", "SELECT rif_proveedor FROM proveedores WHERE LOWER(email_proveedor) = %s AND estado = 1", [
                (" AND rif_proveedor != %s", exclude.get("proveedor_rif")),
            ]),
            ("sucursales", "transalca", "SELECT id_sucursal FROM sucursales WHERE LOWER(email_sucursal) = %s AND estado = 1", [
                (" AND id_sucursal != %s", exclude.get("sucursal_id")),
            ]),
        ]
        for table, db, base_sql, optional_filters in checks:
            if table not in tables_to_check:
                continue
            row = None
            try:
                sql = base_sql
                params = [normalized]
                for clause, value in optional_filters:
                    if value not in (None, ''):
                        sql += clause
                        params.append(value)
                row = self.fetch_one(db, sql + " LIMIT 1", tuple(params))
            except Exception:
                logger.warning("No se pudo validar email duplicado en %s.", table, exc_info=True)
            if row:
                return True
        return False
