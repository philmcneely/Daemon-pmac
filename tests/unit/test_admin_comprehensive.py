"""
Admin tests with proper authentication and single status code expectations
"""

import pytest


class TestAdminUnauthorized:
    """Test admin endpoints return 403 when no authentication provided"""

    def test_list_users_unauthorized(self, unit_client):
        """Test listing users without auth returns 403"""
        response = unit_client.get("/admin/users")
        assert response.status_code == 403

    def test_create_backup_unauthorized(self, unit_client):
        """Test create backup without auth returns 403"""
        response = unit_client.post("/admin/backup")
        assert response.status_code == 403

    def test_get_system_stats_unauthorized(self, unit_client):
        """Test get system stats without auth returns 403"""
        response = unit_client.get("/admin/stats")
        assert response.status_code == 403


class TestAdminAuthorized:
    """Test admin endpoints with proper authentication"""

    def test_list_users_authorized(self, unit_client, unit_auth_headers):
        """Test listing users with auth returns 200"""
        response = unit_client.get("/admin/users", headers=unit_auth_headers)
        assert response.status_code == 200

    def test_create_backup_authorized(self, unit_client, unit_auth_headers):
        """Test create backup with auth returns 200"""
        response = unit_client.post("/admin/backup", headers=unit_auth_headers)
        assert response.status_code == 200

    def test_get_system_stats_authorized(self, unit_client, unit_auth_headers):
        """Test get system stats with auth returns 200"""
        response = unit_client.get("/admin/stats", headers=unit_auth_headers)
        assert response.status_code == 200


class TestAdminNonExistentEndpoints:
    """Test endpoints that don't exist return 404"""

    def test_get_config_endpoint_not_found(self, unit_client):
        """Test /admin/config GET returns 404"""
        response = unit_client.get("/admin/config")
        assert response.status_code == 404

    def test_get_health_endpoint_not_found(self, unit_client):
        """Test /admin/health returns 404"""
        response = unit_client.get("/admin/health")
        assert response.status_code == 404

    def test_post_endpoints_method_not_allowed(self, unit_client):
        """Test POST /admin/endpoints returns 405"""
        response = unit_client.post("/admin/endpoints", json={"name": "test"})
        assert response.status_code == 405

    def test_get_bulk_operations_endpoint_not_found(self, unit_client):
        """Test /admin/bulk-operations returns 404"""
        response = unit_client.get("/admin/bulk-operations")
        assert response.status_code == 404

    def test_get_backup_frequency_endpoint_not_found(self, unit_client):
        """Test /admin/backup-frequency returns 404"""
        response = unit_client.get("/admin/backup-frequency")
        assert response.status_code == 404
