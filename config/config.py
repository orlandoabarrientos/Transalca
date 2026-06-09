import os
import secrets


def _env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


DB_CONFIG_MANTENIMIENTO = {
    "host": os.getenv("DB_MANTENIMIENTO_HOST", "127.0.0.1"),
    "port": _env_int("DB_MANTENIMIENTO_PORT", 3306),
    "user": os.getenv("DB_MANTENIMIENTO_USER", "root"),
    "password": os.getenv("DB_MANTENIMIENTO_PASSWORD", ""),
    "database": os.getenv("DB_MANTENIMIENTO_NAME", "db_mantenimiento"),
    "charset": os.getenv("DB_MANTENIMIENTO_CHARSET", "utf8mb4")
}

DB_CONFIG_TRANSALCA = {
    "host": os.getenv("DB_TRANSALCA_HOST", "127.0.0.1"),
    "port": _env_int("DB_TRANSALCA_PORT", 3306),
    "user": os.getenv("DB_TRANSALCA_USER", "root"),
    "password": os.getenv("DB_TRANSALCA_PASSWORD", ""),
    "database": os.getenv("DB_TRANSALCA_NAME", "db_transalca"),
    "charset": os.getenv("DB_TRANSALCA_CHARSET", "utf8mb4")
}

SECRET_KEY = os.environ.get("TRANSALCA_SECRET_KEY") or secrets.token_urlsafe(32)
UPLOAD_FOLDER = os.getenv("TRANSALCA_UPLOAD_FOLDER", "public/assets")
BACKUP_FOLDER = os.getenv("TRANSALCA_BACKUP_FOLDER", "respaldos")
MAIL_SERVER = os.getenv("TRANSALCA_MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = _env_int("TRANSALCA_MAIL_PORT", 587)
MAIL_USERNAME = os.getenv("TRANSALCA_MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("TRANSALCA_MAIL_PASSWORD", "")
APP_HOST = os.getenv("TRANSALCA_APP_HOST", "127.0.0.1")
APP_PORT = _env_int("TRANSALCA_APP_PORT", 5000)
