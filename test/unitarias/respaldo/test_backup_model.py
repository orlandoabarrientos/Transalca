import pytest
from unittest.mock import patch, MagicMock
from model.backup_model import BackupModel


class TestBackupModelHelpers:
    """Pruebas unitarias con Data Provider (@pytest.mark.parametrize) para validaciones de seguridad de respaldos."""

    # DATA PROVIDER: Identificadores SQL seguros para nombres de tablas y bases de datos
    @pytest.mark.parametrize("identifier, is_safe", [
        ("db_transalca", True),
        ("mantenimiento_2026", True),
        ("tabla_usuarios", True),
        ("table; DROP TABLE", False),
        ("db-name", False),
        ("select * from", False),
        ("", False),
    ])
    def test_is_safe_identifier_data_provider(self, identifier, is_safe):
        model = BackupModel()
        assert model._is_safe_identifier(identifier) == is_safe

    # DATA PROVIDER: Formato y seguridad de nombres de archivos de respaldo (.sql)
    @pytest.mark.parametrize("filename, is_valid", [
        ("transalca_20260822_120000.sql", True),
        ("mantenimiento_backup.sql", True),
        ("../etc/passwd.sql", False),       # Path traversal
        ("malicioso.exe", False),           # Extensión no .sql
        ("invalido.txt", False),            # Extensión no .sql
        ("", False),                        # Nombre vacío
    ])
    def test_safe_backup_path_data_provider(self, filename, is_valid):
        model = BackupModel()
        if is_valid:
            path = model._safe_backup_path(filename)
            assert path.endswith(filename)
        else:
            with pytest.raises(ValueError):
                model._safe_backup_path(filename)

    # DATA PROVIDER: Cabecera obligatoria de archivos de respaldo importados
    @pytest.mark.parametrize("header_text, is_valid", [
        ("-- Transalca backup\n-- Database: db_transalca", True),
        ("  -- Transalca backup\n-- Created: 2026", True),
        ("SELECT * FROM usuarios;\nDROP TABLE clientes;", False), # Script sin cabecera oficial
        ("DOCUMENTO DE TEXTO CUALQUIERA", False),
    ])

    def test_read_validated_backup_header_data_provider(self, tmp_path, header_text, is_valid):
        model = BackupModel()
        test_file = tmp_path / "test_backup.sql"
        test_file.write_text(header_text, encoding="utf-8")

        if is_valid:
            content = model._read_validated_backup(str(test_file))
            assert "-- Transalca backup" in content
        else:
            with pytest.raises(ValueError) as exc_info:
                model._read_validated_backup(str(test_file))
            assert "no es un respaldo valido" in str(exc_info.value)


class TestBackupModelOperations:
    """Pruebas unitarias con mocks de sistema de archivos para creación y gestión de respaldos."""

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["transalca_20260822_120000.sql"])
    @patch("os.path.getsize", return_value=1024)
    @patch("os.path.getmtime", return_value=1700000000)
    def test_list_backups(self, mock_mtime, mock_size, mock_listdir, mock_exists):
        model = BackupModel()
        backups = model.ejecutar("list_backups")

        assert len(backups) == 1
        assert backups[0]["filename"] == "transalca_20260822_120000.sql"
        assert backups[0]["size"] == 1024

    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_delete_backup_success(self, mock_remove, mock_exists):
        model = BackupModel()
        result = model.ejecutar("delete_backup", "transalca_20260822_120000.sql")

        assert result is True
        mock_remove.assert_called_once()

    @patch.object(BackupModel, "insert")
    def test_log_event(self, mock_insert):
        mock_insert.return_value = 50
        model = BackupModel()
        log_id = model.ejecutar("log_event", 1, "CREAR", "RESPALDOS", "Respaldo manual creado", "127.0.0.1", 1)

        assert log_id == 50
        mock_insert.assert_called_once()

    def test_ejecutar_invalid_action(self):
        model = BackupModel()
        with pytest.raises(ValueError) as exc_info:
            model.ejecutar("accion_inexistente")

        assert "Accion no permitida" in str(exc_info.value)
