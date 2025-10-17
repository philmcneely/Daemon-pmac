import importlib
import json
import unittest
from typing import Any, cast

from hypothesis import given  # type: ignore
from hypothesis import strategies as st  # type: ignore

try:
    import_endpoint_data = importlib.import_module("app.utils").import_endpoint_data
except Exception:  # pragma: no cover
    import_endpoint_data = None  # type: ignore


class TestImportEndpointDataProperty(unittest.TestCase):
    """Test import_endpoint_data property"""

    @given(
        st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.one_of(
                    st.integers(),
                    st.floats(allow_nan=False, allow_infinity=False),
                    st.text(),
                    st.booleans(),
                    st.none(),
                ),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=3,
        )
    )
    def test_import_json_array(self, data_list: list[dict[str, Any]]) -> None:
        # Build a JSON array payload
        payload = json.dumps(data_list)

        # Use a dummy session that satisfies the Session protocol
        class DummySession:
            def __init__(self) -> None:
                self.added: list[Any] = []

            class _Query:
                def filter(self, *args: Any, **kwargs: Any) -> "DummySession._Query":
                    return self

                def first(self) -> Any:
                    class Endpoint:
                        id = 1
                        name = "test_endpoint"
                        is_active = True
                        schema: dict[str, Any] = {}

                    return Endpoint()

            def query(self, model: Any) -> "_Query":
                return self._Query()

            def add(self, obj: Any) -> None:
                self.added.append(obj)

            def commit(self) -> None:
                pass

            def rollback(self) -> None:
                pass

        if import_endpoint_data is None:
            self.fail("import_endpoint_data not available")
        result: Any = import_endpoint_data(
            cast(Any, DummySession()), "test_endpoint", payload, format="json"
        )
        # Ensure the result reports the correct number of imported items
        self.assertEqual(result["imported_count"], len(data_list))
        self.assertEqual(result["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
