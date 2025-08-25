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

    def test_resume_check_command(self):
        """Test resume check command"""
        runner = CliRunner()

        with patch("app.resume_loader.check_resume_file_exists") as mock_check:
            mock_check.return_value = {
                "success": True,
                "exists": True,
                "file_path": "/path/to/resume.json",
            }

            result = runner.invoke(cli, ["resume", "check"])

            assert result.exit_code == 0
            mock_check.assert_called_once()

    def test_resume_check_with_file(self):
        """Test resume check command with specific file"""
        runner = CliRunner()

        with patch("app.resume_loader.check_resume_file_exists") as mock_check:
            mock_check.return_value = {
                "success": True,
                "exists": True,
                "file_path": "custom_resume.json",
            }

            result = runner.invoke(
                cli, ["resume", "check", "--file", "custom_resume.json"]
            )

            assert result.exit_code == 0
            mock_check.assert_called_with("custom_resume.json")

    def test_resume_import_command(self):
        """Test resume import command"""
        runner = CliRunner()

        with patch("app.resume_loader.import_resume_to_database") as mock_import:
            mock_import.return_value = {
                "success": True,
                "message": "Resume imported successfully",
            }

            result = runner.invoke(cli, ["resume", "import", "resume.json"])

            assert result.exit_code == 0
            assert "successfully" in result.output

    def test_resume_import_with_replace(self):
        """Test resume import with replace flag"""
        runner = CliRunner()

        with patch("app.resume_loader.import_resume_to_database") as mock_import:
            mock_import.return_value = {"success": True}

            result = runner.invoke(
                cli, ["resume", "import", "resume.json", "--replace"]
            )

            assert result.exit_code == 0
            mock_import.assert_called_with("resume.json", replace_existing=True)

    def test_resume_show_command(self):
        """Test resume show command"""
        runner = CliRunner()

        with patch("app.resume_loader.get_resume_from_database") as mock_get:
            mock_get.return_value = {
                "success": True,
                "data": {"personal": {"name": "Test User"}, "experience": []},
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

    def test_db_init_command(self):
        """Test database initialization command"""
        runner = CliRunner()

        with patch("app.database.init_db") as mock_init:
            mock_init.return_value = None

            result = runner.invoke(cli, ["db", "init"])

            assert result.exit_code == 0
            mock_init.assert_called_once()

    def test_db_reset_command_with_confirmation(self):
        """Test database reset with confirmation"""
        runner = CliRunner()

        with patch("app.database.init_db") as mock_init:
            mock_init.return_value = None

            # Simulate user typing 'yes'
            result = runner.invoke(cli, ["db", "reset"], input="yes\n")

            assert result.exit_code == 0
            assert "initialized" in result.output

    def test_db_reset_command_cancelled(self):
        """Test database reset cancelled"""
        runner = CliRunner()

        with patch("app.database.init_db") as mock_init:
            # Simulate user typing 'no'
            result = runner.invoke(cli, ["db", "reset"], input="no\n")

            assert result.exit_code == 0
            assert "cancelled" in result.output
            mock_init.assert_not_called()


class TestUserCommands:
    """Test user management CLI commands"""

    def test_user_group_help(self):
        """Test user command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["user", "--help"])

        assert result.exit_code == 0
        assert "User management commands" in result.output

    def test_user_create_command(self):
        """Test user creation command"""
        runner = CliRunner()

        with patch("app.database.SessionLocal") as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session

            result = runner.invoke(
                cli,
                [
                    "user",
                    "create",
                    "--username",
                    "testuser",
                    "--email",
                    "test@example.com",
                    "--password",
                    "testpass123",
                ],
            )

            assert result.exit_code == 0

    def test_user_create_admin(self):
        """Test admin user creation"""
        runner = CliRunner()

        with patch("app.database.SessionLocal") as mock_session_factory:
            mock_session = MagicMock()
            mock_session_factory.return_value = mock_session

            result = runner.invoke(
                cli,
                [
                    "user",
                    "create",
                    "--username",
                    "admin",
                    "--email",
                    "admin@example.com",
                    "--password",
                    "adminpass123",
                    "--admin",
                ],
            )

            assert result.exit_code == 0

    def test_user_list_command(self):
        """Test user listing command"""
        runner = CliRunner()

        with patch("app.database.SessionLocal") as mock_session_factory:
            mock_session = MagicMock()
            mock_user1 = MagicMock(
                username="user1", email="user1@example.com", is_admin=False
            )
            mock_user2 = MagicMock(
                username="admin", email="admin@example.com", is_admin=True
            )
            mock_session.query.return_value.all.return_value = [mock_user1, mock_user2]
            mock_session_factory.return_value = mock_session

            result = runner.invoke(cli, ["user", "list"])

            assert result.exit_code == 0
            assert "user1" in result.output
            assert "admin" in result.output


class TestEndpointCommands:
    """Test endpoint management CLI commands"""

    def test_endpoint_group_help(self):
        """Test endpoint command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["endpoint", "--help"])

        assert result.exit_code == 0
        assert "Endpoint management commands" in result.output

    def test_endpoint_create_command(self):
        """Test endpoint creation command"""
        runner = CliRunner()

        with patch("app.database.SessionLocal") as mock_session_factory:
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

    def test_endpoint_create_with_fields(self):
        """Test endpoint creation with field definitions"""
        runner = CliRunner()

        with patch("app.database.SessionLocal") as mock_session_factory:
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

    def test_endpoint_list_command(self):
        """Test endpoint listing command"""
        runner = CliRunner()

        with patch("app.database.SessionLocal") as mock_session_factory:
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

    def test_backup_create_command(self):
        """Test backup creation command"""
        runner = CliRunner()

        with patch("app.utils.create_backup") as mock_backup:
            mock_backup.return_value = {
                "success": True,
                "backup_file": "backup_20240101_120000.db",
            }

            result = runner.invoke(cli, ["backup", "create"])

            assert result.exit_code == 0
            assert "backup_20240101_120000.db" in result.output

    def test_backup_list_command(self):
        """Test backup listing command"""
        runner = CliRunner()

        with patch("app.utils.list_backups") as mock_list:
            mock_list.return_value = {
                "success": True,
                "backups": [
                    {
                        "filename": "backup1.db",
                        "created": "2024-01-01",
                        "size": "1.2MB",
                    },
                    {
                        "filename": "backup2.db",
                        "created": "2024-01-02",
                        "size": "1.3MB",
                    },
                ],
            }

            result = runner.invoke(cli, ["backup", "list"])

            assert result.exit_code == 0
            assert "backup1.db" in result.output
            assert "backup2.db" in result.output

    def test_backup_restore_command(self):
        """Test backup restore command"""
        runner = CliRunner()

        with patch("app.utils.restore_backup") as mock_restore:
            mock_restore.return_value = {"success": True}

            result = runner.invoke(cli, ["backup", "restore", "backup_test.db"])

            assert result.exit_code == 0
            mock_restore.assert_called_with("backup_test.db")

    def test_backup_cleanup_command(self):
        """Test backup cleanup command"""
        runner = CliRunner()

        with patch("app.utils.cleanup_old_backups") as mock_cleanup:
            mock_cleanup.return_value = {
                "success": True,
                "deleted_count": 3,
                "deleted_files": ["old1.db", "old2.db", "old3.db"],
            }

            result = runner.invoke(cli, ["backup", "cleanup"])

            assert result.exit_code == 0
            assert "3" in result.output


class TestDataCommands:
    """Test data management CLI commands"""

    def test_data_group_help(self):
        """Test data command group help"""
        runner = CliRunner()

        result = runner.invoke(cli, ["data", "--help"])

        assert result.exit_code == 0

    def test_data_export_command(self):
        """Test data export command"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "export.json")

            with patch("app.utils.export_endpoint_data") as mock_export:
                mock_export.return_value = {
                    "success": True,
                    "data": [{"test": "data"}],
                    "count": 1,
                }

                result = runner.invoke(
                    cli, ["data", "export", "test_endpoint", "--output", output_file]
                )

                assert result.exit_code == 0

    def test_data_export_csv_format(self):
        """Test data export in CSV format"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "export.csv")

            with patch("app.utils.export_endpoint_data") as mock_export:
                mock_export.return_value = {
                    "success": True,
                    "data": [{"name": "Item", "value": 100}],
                    "count": 1,
                }

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
        assert "Missing option" in result.output

    def test_invalid_options(self):
        """Test handling of invalid options"""
        runner = CliRunner()

        result = runner.invoke(cli, ["resume", "check", "--invalid-option"])

        assert result.exit_code != 0
        assert "No such option" in result.output

    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        runner = CliRunner()

        with patch(
            "app.database.SessionLocal",
            side_effect=Exception("Database connection failed"),
        ):
            result = runner.invoke(cli, ["user", "list"])

            # Should handle gracefully
            assert result.exit_code != 0
