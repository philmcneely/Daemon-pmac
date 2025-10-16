import json
import os
import sys
import unittest
from typing import cast
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.utils import export_endpoint_data, import_endpoint_data  # type: ignore

# Ensure the project root is in the import path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class DummyEndpoint:
    def __init__(
        self, name="test_endpoint", description="Test endpoint", is_active=True, id=1
    ):
        self.name = name
        self.description = description
        self.is_active = is_active
        self.id = id
        self.schema = {}


class DummyDataEntry:
    def __init__(self, endpoint_id, data, created_by_id=None):
        self.endpoint_id = endpoint_id
        self.data = data
        self.created_by_id = created_by_id


class DummySession:
    def __init__(self):
        self._entries = []

    def query(self, model):
        # Simple mock for Endpoint and DataEntry queries
        mock = MagicMock()
        if model.__name__ == "Endpoint":
            mock.filter.return_value.first.return_value = DummyEndpoint()
        elif model.__name__ == "DataEntry":
            mock.filter.return_value.all.return_value = []
        return mock

    def add(self, obj):
        self._entries.append(obj)

    def commit(self):
        pass

    def rollback(self):
        pass


class TestImportExport(unittest.TestCase):
    def setUp(self):
        self.session = DummySession()
        self.endpoint_name = "test_endpoint"

    def test_export_json_empty(self):
        result = export_endpoint_data(
            cast(Session, self.session), self.endpoint_name, format="json"
        )
        data = json.loads(result)
        self.assertEqual(data["endpoint"], self.endpoint_name)
        self.assertEqual(data["count"], 0)
        self.assertIsInstance(data["data"], list)

    def test_import_json_single_object(self):
        payload = json.dumps({"field": "value"})
        result = import_endpoint_data(
            cast(Session, self.session), self.endpoint_name, payload, format="json"
        )
        self.assertEqual(result["imported_count"], 1)
        self.assertEqual(result["error_count"], 0)

    def test_import_json_array(self):
        payload = json.dumps([{"field": "value1"}, {"field": "value2"}])
        result = import_endpoint_data(
            cast(Session, self.session), self.endpoint_name, payload, format="json"
        )
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(result["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
