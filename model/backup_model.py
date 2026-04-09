from model.connection import Connection
import subprocess
import os
from datetime import datetime
from config.config import DB_CONFIG_MANTENIMIENTO, DB_CONFIG_TRANSALCA


class BackupModel(Connection):
    def __init__(self):
        super().__init__()
        self.backup_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'respaldos')

    def create_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mysqldump = self._find_mysqldump()
        files = []
        for db_config, db_name in [(DB_CONFIG_MANTENIMIENTO, 'db_mantenimiento'), (DB_CONFIG_TRANSALCA, 'db_transalca')]:
            filename = f"{db_name}_{timestamp}.sql"
            filepath = os.path.join(self.backup_folder, filename)
            cmd = f'"{mysqldump}" -h {db_config["host"]} -P {db_config["port"]} -u {db_config["user"]} {db_config["database"]} > "{filepath}"'
            if db_config["password"]:
                cmd = f'"{mysqldump}" -h {db_config["host"]} -P {db_config["port"]} -u {db_config["user"]} -p{db_config["password"]} {db_config["database"]} > "{filepath}"'
            os.system(cmd)
            if os.path.exists(filepath):
                files.append({"filename": filename, "path": filepath, "size": os.path.getsize(filepath)})
        return files

    def _find_mysqldump(self):
        paths = [
            r'C:\xampp\mysql\bin\mysqldump.exe',
            r'D:\xampp\mysql\bin\mysqldump.exe',
            'mysqldump'
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return 'mysqldump'

    def list_backups(self):
        files = []
        if os.path.exists(self.backup_folder):
            for f in os.listdir(self.backup_folder):
                if f.endswith('.sql'):
                    filepath = os.path.join(self.backup_folder, f)
                    files.append({
                        "filename": f,
                        "size": os.path.getsize(filepath),
                        "date": datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    })
        files.sort(key=lambda x: x['date'], reverse=True)
        return files

    def delete_backup(self, filename):
        filepath = os.path.join(self.backup_folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def get_backup_path(self, filename):
        filepath = os.path.join(self.backup_folder, filename)
        if os.path.exists(filepath):
            return filepath
        return None
