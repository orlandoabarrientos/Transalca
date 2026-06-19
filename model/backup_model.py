import logging
import os
import re
import threading
from datetime import datetime

import pymysql
from pymysql.constants import CLIENT

from config.config import BACKUP_FOLDER, DB_CONFIG_MANTENIMIENTO, DB_CONFIG_TRANSALCA
from model.connection import Connection


logger = logging.getLogger(__name__)
BACKUP_FILENAME_RE = re.compile(r'^[A-Za-z0-9_.-]+\.sql$')
SQL_IDENTIFIER_RE = re.compile(r'^[A-Za-z0-9_]+$')
BACKUP_HEADER = "-- Transalca backup"
MAX_BACKUP_BYTES = 50 * 1024 * 1024
BACKUP_MAX_AGE_DAYS = 60


class BackupModel(Connection):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        configured_folder = BACKUP_FOLDER if os.path.isabs(BACKUP_FOLDER) else os.path.join(base_dir, BACKUP_FOLDER)
        self.backup_folder = os.path.abspath(configured_folder)

    def _create_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        files = []
        os.makedirs(self.backup_folder, exist_ok=True)
        for db_key, db_config in (('mantenimiento', DB_CONFIG_MANTENIMIENTO), ('transalca', DB_CONFIG_TRANSALCA)):
            db_name = db_config["database"]
            if not self._is_safe_identifier(db_name):
                logger.error("Nombre de base de datos invalido para respaldo: %s", db_name)
                continue
            filename = f"{db_name}_{timestamp}.sql"
            filepath = self._safe_backup_path(filename)
            try:
                self._write_database_dump(db_key, db_name, filepath)
                files.append({"filename": filename, "path": filepath, "size": os.path.getsize(filepath)})
            except Exception:
                logger.exception("Error creando respaldo de %s.", db_name)
                if os.path.exists(filepath):
                    os.remove(filepath)
        return files

    def _write_database_dump(self, db_key, db_name, filepath):
        conn = self.con_mantenimiento() if db_key == 'mantenimiento' else self.con_transalca()
        cursor = conn.cursor()
        with open(filepath, 'w', encoding='utf-8') as dump:
            dump.write(f"-- Transalca backup\n-- Database: {db_name}\n-- Created: {datetime.now().isoformat(timespec='seconds')}\n\n")
            dump.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            safe_tables = [table for table in tables if self._is_safe_identifier(table)]
            for table in safe_tables:
                quoted_table = self._quote_identifier(table)
                show_create_query = " ".join(("SHOW", "CREATE", "TABLE", quoted_table))
                cursor.execute(show_create_query)
                create_row = cursor.fetchone()
                create_values = list(create_row.values()) if create_row else []
                create_sql = create_values[1] if len(create_values) > 1 else ''
                dump.write("".join(("DROP TABLE IF EXISTS ", quoted_table, ";\n")))
                dump.write(create_sql + ";\n\n")

                select_query = " ".join(("SELECT", "*", "FROM", quoted_table))
                cursor.execute(select_query)
                rows = cursor.fetchall()
                if not rows:
                    continue
                columns = [self._quote_identifier(column[0]) for column in cursor.description]
                column_sql = ", ".join(columns)
                for row in rows:
                    values = ", ".join(conn.escape(value) for value in row.values())
                    dump.write("".join(("INSERT INTO ", quoted_table, " (", column_sql, ") VALUES (", values, ");\n")))
                dump.write("\n")
            dump.write("SET FOREIGN_KEY_CHECKS=1;\n")

    def _is_safe_identifier(self, value):
        return bool(SQL_IDENTIFIER_RE.fullmatch(str(value or '')))

    def _quote_identifier(self, value):
        if not self._is_safe_identifier(value):
            raise ValueError("Identificador SQL invalido.")
        return f"`{value}`"

    def _safe_backup_path(self, filename):
        if not BACKUP_FILENAME_RE.fullmatch(filename) or os.path.basename(filename) != filename:
            raise ValueError("Nombre de respaldo invalido.")
        filepath = os.path.abspath(os.path.join(self.backup_folder, filename))
        if os.path.commonpath([self.backup_folder, filepath]) != self.backup_folder:
            raise ValueError("Ruta de respaldo invalida.")
        return filepath

    def _list_backups(self):
        files = []
        if os.path.exists(self.backup_folder):
            for filename in os.listdir(self.backup_folder):
                if BACKUP_FILENAME_RE.fullmatch(filename):
                    filepath = self._safe_backup_path(filename)
                    files.append({
                        "filename": filename,
                        "size": os.path.getsize(filepath),
                        "date": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    })
        files.sort(key=lambda x: x['date'], reverse=True)
        return files

    def _delete_backup(self, filename):
        filepath = self._safe_backup_path(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def _get_backup_path(self, filename):
        filepath = self._safe_backup_path(filename)
        if os.path.exists(filepath):
            return filepath
        return None

    def _db_config_for_file(self, filename):
        base = os.path.basename(filename)
        for db_config in (DB_CONFIG_MANTENIMIENTO, DB_CONFIG_TRANSALCA):
            db_name = db_config["database"]
            if self._is_safe_identifier(db_name) and base.startswith(db_name + "_"):
                return db_config
        return None

    def _read_validated_backup(self, filepath):
        if not os.path.exists(filepath):
            raise ValueError("El respaldo no existe.")
        size = os.path.getsize(filepath)
        if size == 0 or size > MAX_BACKUP_BYTES:
            raise ValueError("El archivo de respaldo no tiene un tamaño valido.")
        with open(filepath, 'r', encoding='utf-8') as handle:
            script = handle.read()
        if not script.lstrip().startswith(BACKUP_HEADER):
            raise ValueError("El archivo no es un respaldo valido del sistema.")
        return script

    def _restore_backup(self, filename):
        filepath = self._safe_backup_path(filename)
        db_config = self._db_config_for_file(filename)
        if not db_config:
            raise ValueError("El respaldo no corresponde a una base de datos del sistema.")
        script = self._read_validated_backup(filepath)
        safety = self._create_backup()
        conn = pymysql.connect(
            host=db_config["host"], port=db_config["port"], user=db_config["user"],
            password=db_config["password"], database=db_config["database"],
            charset=db_config["charset"], autocommit=True,
            client_flag=CLIENT.MULTI_STATEMENTS)
        try:
            cursor = conn.cursor()
            cursor.execute(script)
            while cursor.nextset():
                pass
        finally:
            conn.close()
        return {
            "database": db_config["database"],
            "safety_backup": [item["filename"] for item in safety],
        }

    def _save_uploaded_backup(self, filename, content):
        if not content or len(content) > MAX_BACKUP_BYTES:
            raise ValueError("El archivo de respaldo no tiene un tamaño valido.")
        base = os.path.basename(str(filename or ''))
        if not BACKUP_FILENAME_RE.fullmatch(base):
            raise ValueError("Nombre de respaldo invalido. Debe terminar en .sql")
        if self._db_config_for_file(base) is None:
            raise ValueError("El respaldo no corresponde a una base de datos del sistema.")
        try:
            text = content.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            raise ValueError("El archivo no es un respaldo valido del sistema.")
        if not text.lstrip().startswith(BACKUP_HEADER):
            raise ValueError("El archivo no es un respaldo valido del sistema.")
        filepath = self._safe_backup_path(base)
        os.makedirs(self.backup_folder, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as handle:
            handle.write(text)
        return base

    def _cleanup_old_backups(self, max_age_days=BACKUP_MAX_AGE_DAYS):
        removed = []
        if not os.path.exists(self.backup_folder):
            return removed
        cutoff = datetime.now().timestamp() - max_age_days * 86400
        for filename in os.listdir(self.backup_folder):
            if not BACKUP_FILENAME_RE.fullmatch(filename):
                continue
            try:
                filepath = self._safe_backup_path(filename)
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    removed.append(filename)
            except (OSError, ValueError):
                continue
        return removed

    def _log_event(self, usuario_id, accion, modulo, descripcion, ip, respaldo=0):
        return self.insert("mantenimiento",
            "INSERT INTO bitacora (usuario_id, accion, modulo, descripcion, ip, respaldo) VALUES (%s, %s, %s, %s, %s, %s)",
            (usuario_id, accion, modulo, descripcion, ip, int(respaldo)))

    def _has_backup_this_week(self):
        row = self.fetch_one("mantenimiento",
            "SELECT 1 FROM bitacora WHERE respaldo = 1 AND YEARWEEK(fecha, 3) = YEARWEEK(CURDATE(), 3) LIMIT 1")
        return row is not None

    def ejecutar(self, accion, *args, **kwargs):
        acciones = {
            "create_backup": self._create_backup,
            "list_backups": self._list_backups,
            "delete_backup": self._delete_backup,
            "get_backup_path": self._get_backup_path,
            "restore_backup": self._restore_backup,
            "save_uploaded_backup": self._save_uploaded_backup,
            "cleanup_old_backups": self._cleanup_old_backups,
            "log_event": self._log_event,
            "has_backup_this_week": self._has_backup_this_week,
        }
        if accion not in acciones:
            raise ValueError("Accion no permitida")
        return acciones[accion](*args, **kwargs)


class WeeklyBackupScheduler:
    def __init__(self, interval_seconds=3600):
        self.interval_seconds = max(60, int(interval_seconds))
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._model = BackupModel()

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name='weekly-backup', daemon=True)
            self._thread.start()
            return True

    def stop(self):
        self._stop_event.set()

    def _run_loop(self):
        while not self._stop_event.wait(self.interval_seconds):
            self._run_once()

    def _run_once(self):
        try:
            removed = self._model.ejecutar("cleanup_old_backups")
            if removed:
                self._model.ejecutar("log_event", 1, 'ELIMINAR', 'RESPALDOS',
                    f"Respaldos antiguos eliminados: {', '.join(removed)}", '127.0.0.1', 0)
                logger.info("Respaldos antiguos eliminados automaticamente: %s", ', '.join(removed))
        except Exception:
            logger.exception("Error limpiando respaldos antiguos.")
        try:
            if self._model.ejecutar("has_backup_this_week"):
                return
            files = self._model.ejecutar("create_backup")
            if files:
                nombres = ', '.join(f['filename'] for f in files)
                self._model.ejecutar("log_event", 1, 'CREAR', 'RESPALDOS', f"Respaldo creado: {nombres}", '127.0.0.1', 1)
                logger.info("Respaldo semanal automatico creado: %s", nombres)
        except Exception:
            logger.exception("Error en respaldo semanal automatico.")


_scheduler = WeeklyBackupScheduler()


def start_backup_scheduler():
    return _scheduler.start()
