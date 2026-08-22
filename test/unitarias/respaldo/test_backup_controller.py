import pytest
from unittest.mock import patch
from app import app as flask_app
import io


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def auth_admin_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_cedula'] = 'V-10000000'
        sess['user_tipo'] = 'admin'
        sess['roles'] = ['Administrador']
    return client


@pytest.fixture
def auth_regular_client(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['user_cedula'] = 'V-12345678'
        sess['user_tipo'] = 'cliente'
    return client


class TestBackupController:
    """Pruebas de integración de rutas API para generación, restauración y descarte de respaldos."""

    def test_list_backups_unauthorized_fails(self, client):
        response = client.get('/api/backup/')
        json_data = response.get_json()

        assert response.status_code == 401
        assert json_data["status"] == "error"

    @patch("model.backup_model.BackupModel._cleanup_old_backups")
    @patch("model.backup_model.BackupModel._list_backups")
    def test_list_backups_authorized_success(self, mock_list, mock_cleanup, auth_admin_client):
        mock_list.return_value = [
            {"filename": "transalca_20260822_120000.sql", "size": 2048, "date": "2026-08-22 12:00:00"}
        ]
        response = auth_admin_client.get('/api/backup/')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert len(json_data["data"]) == 1

    def test_create_backup_regular_client_denied(self, auth_regular_client):
        response = auth_regular_client.post('/api/backup/create')
        json_data = response.get_json()

        assert response.status_code == 403
        assert json_data["status"] == "error"
        assert "no autorizado" in json_data["message"].lower()

    @patch("model.backup_model.BackupModel._log_event")
    @patch("model.backup_model.BackupModel._create_backup")
    def test_create_backup_admin_success(self, mock_create, mock_log, auth_admin_client):
        mock_create.return_value = [
            {"filename": "transalca_20260822_120000.sql", "path": "/path/file.sql", "size": 1024}
        ]
        response = auth_admin_client.post('/api/backup/create')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "respaldo creado" in json_data["message"].lower()

    @patch("model.backup_model.BackupModel._log_event")
    @patch("model.backup_model.BackupModel._delete_backup")
    def test_delete_backup_admin_success(self, mock_delete, mock_log, auth_admin_client):
        mock_delete.return_value = True
        response = auth_admin_client.delete('/api/backup/delete/transalca_20260822_120000.sql')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"

    @patch("model.backup_model.BackupModel._log_event")
    @patch("model.backup_model.BackupModel._save_uploaded_backup")
    def test_upload_backup_admin_success(self, mock_save_upload, mock_log, auth_admin_client):
        mock_save_upload.return_value = "transalca_20260822_120000.sql"
        file_content = b"-- Transalca backup\n-- Database: db_transalca\n"
        data = {
            'backup': (io.BytesIO(file_content), 'transalca_20260822_120000.sql')
        }

        response = auth_admin_client.post('/api/backup/upload', data=data, content_type='multipart/form-data')
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert json_data["filename"] == "transalca_20260822_120000.sql"

    @patch("model.backup_model.BackupModel._log_event")
    @patch("model.backup_model.BackupModel._restore_backup")
    def test_restore_backup_admin_success(self, mock_restore, mock_log, auth_admin_client):
        mock_restore.return_value = {"database": "db_transalca", "safety_backup": ["safety.sql"]}
        response = auth_admin_client.post('/api/backup/restore', json={
            "filename": "transalca_20260822_120000.sql"
        })
        json_data = response.get_json()

        assert response.status_code == 200
        assert json_data["status"] == "success"
        assert "restaurado correctamente" in json_data["message"].lower()
