import logging
import os
import re
from datetime import datetime

from config.config import BACKUP_FOLDER, DB_CONFIG_MANTENIMIENTO, DB_CONFIG_TRANSALCA
from model.connection import Connection


logger = logging.getLogger(__name__)
BACKUP_FILENAME_RE = re.compile(r'^[A-Za-z0-9_.-]+\.sql$')
SQL_IDENTIFIER_RE = re.compile(r'^[A-Za-z0-9_]+$')


class BackupModel(Connection):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        configured_folder = BACKUP_FOLDER if os.path.isabs(BACKUP_FOLDER) else os.path.join(base_dir, BACKUP_FOLDER)
        self.backup_folder = os.path.abspath(configured_folder)

    def create_backup(self):
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
            cursor.execute("SHOW TABLES")
            tables = [next(iter(row.values())) for row in cursor.fetchall()]
            safe_tables = [table for table in tables if self._is_safe_identifier(table)]
            for table in safe_tables:
                quoted_table = self._quote_identifier(table)
                show_create_query = "SHOW CREATE TABLE " + quoted_table
                cursor.execute(show_create_query)
                create_row = cursor.fetchone()
                create_values = list(create_row.values()) if create_row else []
                create_sql = create_values[1] if len(create_values) > 1 else ''
                dump.write("DROP TABLE IF EXISTS " + quoted_table + ";\n")
                dump.write(create_sql + ";\n\n")

                # B608 falso positivo: tabla obtenida de SHOW TABLES y validada con SQL_IDENTIFIER_RE antes de citarse.
                select_query = "SELECT * FROM " + quoted_table  # nosec B608
                cursor.execute(select_query)
                rows = cursor.fetchall()
                if not rows:
                    continue
                columns = [self._quote_identifier(column[0]) for column in cursor.description]
                column_sql = ", ".join(columns)
                for row in rows:
                    values = ", ".join(conn.escape(value) for value in row.values())
                    # B608 falso positivo: solo escribe SQL de respaldo con identificadores citados y valores escapados.
                    dump.write("INSERT INTO " + quoted_table + " (" + column_sql + ") VALUES (" + values + ");\n")  # nosec B608
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

    def list_backups(self):
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

    def delete_backup(self, filename):
        filepath = self._safe_backup_path(filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def get_backup_path(self, filename):
        filepath = self._safe_backup_path(filename)
        if os.path.exists(filepath):
            return filepath
        return None
