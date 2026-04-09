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

    def execute_query(self, db, sql, params=None):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        cursor = conn.cursor()
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
        cursor.execute(sql, params or ())
        conn.commit()
        return cursor.lastrowid

    def update(self, db, sql, params=None):
        conn = self.con_mantenimiento() if db == "mantenimiento" else self.con_transalca()
        cursor = conn.cursor()
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
