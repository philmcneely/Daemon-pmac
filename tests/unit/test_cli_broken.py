"""
Test CLI functionality
"""

import json
import os
import tempfile
from io import StringIO
from unittest.mock import MagicMock, call, patch

import pytest
from click.testing import CliRunner

from app.cli import cli


@pytest.fixture
def mock_db_session():
    """Create a mock database session for CLI tests"""
    session = MagicMock()
    session.commit.return_value = None
    session.rollback.return_value = None
    session.close.return_value = None
    return session


class TestCLIBasicCommands:
    """Test basic CLI functionality"""

    def test_cli_help(self):
        """Test CLI help command"""
        runner = CliRunner()

        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "Commands:" in result.output

    def test_invalid_command(self):
        """Test invalid command handling"""
        runner = CliRunner()

        result = runner.invoke(cli, ["invalid-command"])

        assert result.exit_code != 0
        assert "No such command" in result.output


class TestResumeCommands:
    """Test resume-related CLI commands"""

    def test_resume_group_help(self):
        """Test resume command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["resume", "--help"])

        assert result.exit_code == 0
        assert "Resume management commands" in result.output

    @patch("app.resume_loader.load_resume_from_file")
    @patch("app.resume_loader.check_resume_file_exists")
    def test_resume_check_command(self, mock_check, mock_load):
        """Test resume check command"""
        runner = CliRunner()
        mock_check.return_value = {
            "success": True,
            "exists": True,
            "file_path": "/path/to/resume.json",
            "readable": True,
            "size_bytes": 1024,
            "last_modified": 1640995200.0,
            "default_location": False,
        }
        mock_load.return_value = {
            "success": True,
            "data": {
                "name": "Test User",
                "title": "Software Engineer",
                "experience": [{"company": "Test Corp"}],
                "education": [{"school": "Test University"}],
            },
        }

        result = runner.invoke(cli, ["resume", "check"])

        assert result.exit_code == 0
        mock_check.assert_called_once()

    @patch("app.resume_loader.load_resume_from_file")
    @patch("app.resume_loader.check_resume_file_exists")
    def test_resume_check_with_file(self, mock_check, mock_load):
        """Test resume check command with specific file"""
        runner = CliRunner()
        mock_check.return_value = {
            "success": True,
            "exists": True,
            "file_path": "custom_resume.json",
            "readable": True,
            "size_bytes": 2048,
            "last_modified": 1640995200.0,
            "default_location": False,
        }
        mock_load.return_value = {
            "success": True,
            "data": {
                "name": "Custom User",
                "title": "Senior Engineer",
                "experience": [{"company": "Custom Corp"}],
                "education": [{"school": "Custom University"}],
            },
        }

        result = runner.invoke(cli, ["resume", "check", "--file", "custom_resume.json"])

        assert result.exit_code == 0
        mock_check.assert_called_with("custom_resume.json")

    @patch("app.resume_loader.import_resume_to_database")
    def test_resume_import_command(self, mock_import):
        """Test resume import command"""
        runner = CliRunner()
        mock_import.return_value = {
            "success": True,
            "message": "Resume imported successfully",
            "file_path": "resume.json",
            "entry_id": 123,
        }

        result = runner.invoke(cli, ["resume", "import-file", "--file", "resume.json"])

        assert result.exit_code == 0
        assert "successfully" in result.output

    @patch("app.resume_loader.import_resume_to_database")
    def test_resume_import_with_replace(self, mock_import):
        """Test resume import with replace flag"""
        runner = CliRunner()
        mock_import.return_value = {
            "success": True,
            "file_path": "resume.json",
            "entry_id": 124,
            "replaced_entries": 2,
        }

        result = runner.invoke(
            cli, ["resume", "import-file", "--file", "resume.json", "--replace"]
        )

        assert result.exit_code == 0
        mock_import.assert_called_with(
            file_path="resume.json", user_id=None, replace_existing=True
        )

    @patch("app.resume_loader.get_resume_from_database")
    def test_resume_show_command(self, mock_get):
        """Test resume show command"""
        runner = CliRunner()
        mock_get.return_value = {
            "success": True,
            "count": 1,
            "entries": [{"id": 1, "created_at": "2024-01-01 12:00:00"}],
            "data": [
                {
                    "name": "Test User",
                    "title": "Engineer",
                    "experience": [{"company": "Test Corp"}],
                    "education": [{"school": "Test University"}],
                    "updated_at": "2024-01-01 12:00:00",
                }
            ],
        }

        result = runner.invoke(cli, ["resume", "show"])

        assert result.exit_code == 0
        assert "Test User" in result.output


class TestDatabaseCommands:
    """Test database-related CLI commands"""

    def test_db_group_help(self):
        """Test database command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["db", "--help"])

        assert result.exit_code == 0
        assert "Database management commands" in result.output

    @patch("app.cli.create_default_endpoints")
    @patch("app.cli.SessionLocal")
    @patch("app.cli.init_db")
    def test_db_init_command(
        self, mock_init, mock_session_local, mock_create_endpoints
    ):
        """Test database initialization command"""
        runner = CliRunner()
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        result = runner.invoke(cli, ["db", "init"])

        assert result.exit_code == 0
        mock_init.assert_called_once()
        mock_create_endpoints.assert_called_once_with(mock_db)
        mock_db.close.assert_called_once()

    @patch("app.cli.create_default_endpoints")
    @patch("app.cli.SessionLocal")
    @patch("app.cli.init_db")
    @patch("os.remove")
    @patch("os.path.exists")
    def test_db_reset_command_with_confirmation(
        self,
        mock_exists,
        mock_remove,
        mock_init,
        mock_session_local,
        mock_create_endpoints,
    ):
        """Test database reset with confirmation"""
        runner = CliRunner()
        mock_exists.return_value = True
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        # Simulate user typing 'yes'
        result = runner.invoke(cli, ["db", "reset"], input="yes\n")

        assert result.exit_code == 0
        assert "successfully" in result.output
        mock_remove.assert_called_once()
        mock_init.assert_called_once()
        mock_create_endpoints.assert_called_once_with(mock_db)

    @patch("app.cli.init_db")
    def test_db_reset_command_cancelled(self, mock_init):
        """Test database reset cancelled"""
        runner = CliRunner()

        # Simulate user typing 'no'
        result = runner.invoke(cli, ["db", "reset"], input="no\n")

        assert result.exit_code == 1
        assert "Aborted" in result.output
        mock_init.assert_not_called()


class TestUserCommands:
    """Test user management CLI commands"""

    def test_user_group_help(self):
        """Test user command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["user", "--help"])

        assert result.exit_code == 0
        assert "User management commands" in result.output

    @patch("app.cli.SessionLocal")
    @patch("app.cli.get_password_hash")
    def test_user_create_command(self, mock_hash, mock_session_factory):
        """Test user creation command"""
        runner = CliRunner()

        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session
        mock_hash.return_value = "hashed_password"

        # Mock the User query to return None (no existing user)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = runner.invoke(
            cli,
            [
                "user",
                "create",
                "testuser",
                "test@example.com",
                "--password",
                "testpass123",
            ],
        )

        assert result.exit_code == 0

    @patch("app.cli.SessionLocal")
    @patch("app.cli.get_password_hash")
    def test_user_create_admin(self, mock_hash, mock_session_factory):
        """Test admin user creation"""
        runner = CliRunner()

        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session
        mock_hash.return_value = "hashed_password"

        # Mock the User query to return None (no existing user)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = runner.invoke(
            cli,
            [
                "user",
                "create",
                "admin",
                "admin@example.com",
                "--password",
                "adminpass123",
                "--admin",
            ],
        )

        assert result.exit_code == 0

    @patch("app.cli.SessionLocal")
    def test_user_list_command(self, mock_session_factory):
        """Test user listing command"""
        runner = CliRunner()

        mock_session = MagicMock()
        mock_user1 = MagicMock(
            id=1,
            username="user1",
            email="user1@example.com",
            is_admin=False,
            is_active=True,
        )
        mock_user2 = MagicMock(
            id=2,
            username="admin",
            email="admin@example.com",
            is_admin=True,
            is_active=True,
        )
        mock_session.query.return_value.all.return_value = [mock_user1, mock_user2]
        mock_session_factory.return_value = mock_session

        result = runner.invoke(cli, ["user", "list"])

        assert result.exit_code == 0
        assert "user1" in result.output


class TestEndpointCommands:
    """Test endpoint management CLI commands"""

    def test_endpoint_group_help(self):
        """Test endpoint command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["endpoint", "--help"])

        assert result.exit_code == 0
        assert "Endpoint management commands" in result.output

    @patch("app.database.SessionLocal")
    def test_endpoint_create_command(self, mock_session_factory):
        """Test endpoint creation command"""
        runner = CliRunner()

        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        result = runner.invoke(
            cli,
            [
                "endpoint",
                "create",
                "--name",
                "test_endpoint",
                "--description",
                "Test endpoint",
            ],
        )

        assert result.exit_code == 0

    @patch("app.database.SessionLocal")
    def test_endpoint_create_with_fields(self, mock_session_factory):
        """Test endpoint creation with field definitions"""
        runner = CliRunner()

        mock_session = MagicMock()
        mock_session_factory.return_value = mock_session

        result = runner.invoke(
            cli,
            [
                "endpoint",
                "create",
                "--name",
                "test_endpoint",
                "--description",
                "Test endpoint",
                "--field",
                "name:string",
                "--field",
                "value:integer",
            ],
        )

        assert result.exit_code == 0

    @patch("app.database.SessionLocal")
    def test_endpoint_list_command(self, mock_session_factory):
        """Test endpoint listing command"""
        runner = CliRunner()

        mock_session = MagicMock()
        mock_endpoint1 = MagicMock(name="endpoint1", description="Test endpoint 1")
        mock_endpoint2 = MagicMock(name="endpoint2", description="Test endpoint 2")
        mock_session.query.return_value.all.return_value = [
            mock_endpoint1,
            mock_endpoint2,
        ]
        mock_session_factory.return_value = mock_session

        result = runner.invoke(cli, ["endpoint", "list"])

        assert result.exit_code == 0
        assert "endpoint1" in result.output
        assert "endpoint2" in result.output


class TestBackupCommands:
    """Test backup management CLI commands"""

    def test_backup_group_help(self):
        """Test backup command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["backup", "--help"])

        assert result.exit_code == 0

    @patch("app.utils.create_backup")
    def test_backup_create_command(self, mock_backup):
        """Test backup creation command"""
        runner = CliRunner()

        mock_backup.return_value = {
            "success": True,
            "backup_file": "backup_20240101_120000.db",
        }

        result = runner.invoke(cli, ["backup", "create"])

        assert result.exit_code == 0
        assert "backup_20240101_120000.db" in result.output

    @patch("os.listdir")
    def test_backup_list_command(self, mock_listdir):
        """Test backup listing command"""
        runner = CliRunner()

        mock_listdir.return_value = [
            "daemon_backup_20240101_120000.db",
            "daemon_backup_20240102_130000.db",
            "other_file.txt",
        ]

        result = runner.invoke(cli, ["backup", "list"])

        assert result.exit_code == 0
        assert "daemon_backup_20240101_120000.db" in result.output

    @patch("shutil.copy2")
    @patch("os.path.exists")
    def test_backup_restore_command(self, mock_exists, mock_copy):
        """Test backup restore command"""
        runner = CliRunner()

        mock_exists.return_value = True

        result = runner.invoke(cli, ["backup", "restore", "backup_test.db"])

        assert result.exit_code == 0

    @patch("app.utils.cleanup_old_backups")
    def test_backup_cleanup_command(self, mock_cleanup):
        """Test backup cleanup command"""
        runner = CliRunner()

        mock_cleanup.return_value = {
            "success": True,
            "deleted_count": 3,
            "deleted_files": ["old1.db", "old2.db", "old3.db"],
        }

        result = runner.invoke(cli, ["backup", "cleanup"])

        assert result.exit_code == 0
        assert "✓ Old backups cleaned up" in result.output


class TestDataCommands:
    """Test data management CLI commands"""

    def test_data_group_help(self):
        """Test data command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["data", "--help"])

        assert result.exit_code == 0

    @patch("app.utils.export_endpoint_data")
    def test_data_export_command(self, mock_export):
        """Test data export command"""
        runner = CliRunner()

        mock_export.return_value = {
            "success": True,
            "data": [{"test": "data"}],
            "count": 1,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "export.json")

            result = runner.invoke(
                cli, ["data", "export", "test_endpoint", "--output", output_file]
            )

            assert result.exit_code == 0

    @patch("app.utils.export_endpoint_data")
    def test_data_export_csv_format(self, mock_export):
        """Test data export in CSV format"""
        runner = CliRunner()

        mock_export.return_value = {
            "success": True,
            "data": [{"name": "Item", "value": 100}],
            "count": 1,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "export.csv")

            result = runner.invoke(
                cli,
                [
                    "data",
                    "export",
                    "test_endpoint",
                    "--format",
                    "csv",
                    "--output",
                    output_file,
                ],
            )

            assert result.exit_code == 0


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_missing_required_arguments(self):
        """Test handling of missing required arguments"""
        runner = CliRunner()

        result = runner.invoke(cli, ["user", "create"])

        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_invalid_options(self):
        """Test handling of invalid options"""
        runner = CliRunner()

        result = runner.invoke(cli, ["resume", "check", "--invalid-option"])

        assert result.exit_code != 0
        assert "No such option" in result.output

    @patch("app.database.SessionLocal")
    def test_database_connection_error(self, mock_session_factory):
        """Test handling of database connection errors"""
        runner = CliRunner()

        mock_session_factory.side_effect = Exception("Database connection failed")

        result = runner.invoke(cli, ["user", "list"])

        # Should handle gracefully
        assert result.exit_code != 0
