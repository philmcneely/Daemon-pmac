# Import the function to test
import importlib
import unittest
from typing import Any, Dict, List

from hypothesis import given
from hypothesis import strategies as st

validate_json_schema = importlib.import_module("app.utils").validate_json_schema  # type: ignore


class TestValidateJsonSchema(unittest.TestCase):
    """Property‑based tests for the JSON schema validator."""

    @given(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(),
                st.booleans(),
                st.none(),
            ),
            min_size=0,
            max_size=5,
        )
    )
    def test_required_string_field(self, data: Dict[str, Any]) -> None:
        """
        Schema requires a string field called ``name``.
        The test checks that:
        * If ``name`` is missing, a required‑field error is reported.
        * If ``name`` is present but not a string, a type‑error is reported.
        * If ``name`` is a valid string, no errors are returned for that field.
        """
        schema: Dict[str, Any] = {"name": {"type": "string", "required": True}}

        errors: List[str] = validate_json_schema(data, schema)

        if "name" not in data:
            # Missing required field
            self.assertIn("Required field 'name' is missing", errors)
        else:
            # Field present – check type
            if not isinstance(data["name"], str):
                self.assertIn("Field 'name' must be a string", errors)
            else:
                # Valid case – ensure no error about ``name``
                self.assertTrue(
                    all("name" not in err for err in errors),
                    f"Unexpected error for valid name field: {errors}",
                )


if __name__ == "__main__":
    unittest.main()
