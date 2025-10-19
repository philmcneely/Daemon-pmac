import html
import re
from typing import Any, Optional


# Mock validate_url function
def validate_url(url: Optional[str]) -> bool:
    return True


# Test the _sanitize_input_impl function
data = """## Code Analysis

```python
# Problematic query
users = session.query(User).filter(
    User.created_at > datetime.now() - timedelta(days=30)
).all()

# Optimized version
users = session.query(User).filter(
    User.created_at > datetime.now() - timedelta(days=30)
).options(selectinload(User.profile)).all()
```

## Root Cause Hypothesis"""


def _sanitize_input_impl(value: Any) -> Any:
    """Sanitize input while preserving HTML entities like \"\"."""
    if isinstance(value, str):
        # Prevent path traversal attempts
        print("Initial value:", repr(value))
        if any(
            pattern in value for pattern in ["../", "..\\", "%2e%2e%2f", "%2e%2e\\"]
        ):
            value = re.sub(r"\.\.[/\\]", "", value, flags=re.IGNORECASE)
            value = re.sub(r"%2e%2e[/\\]", "", value, flags=re.IGNORECASE)
        print("After path traversal patterns:", repr(value))

        # Prevent command injection attempts
        dangerous_patterns = [
            r"[;|]",
            r"\$\{.*?\}",
            r"\$\((.*?)\)",
            r"\{\{.*?\}\}",
        ]
        for pattern in dangerous_patterns:
            print(f"Before applying command injection pattern {pattern}:", repr(value))
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
            print(f"After applying command injection pattern {pattern}:", repr(value))

        # Handle backticks separately to preserve code fences
        # Remove standalone backticks but not those in code fences (``` or `.*?`)
        print("Before handling backticks:", repr(value))
        value = re.sub(
            r"(?<!`)(?<!\\)`(?!`)", "", value
        )  # Remove single backticks not part of code fences
        print("After handling backticks:", repr(value))

        # Prevent SQL injection attempts
        sql_keywords = [
            r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b",
            r'[\'"]\s*(OR|AND)\s*[\'"]',
            r"--\s*$",
            r"/\*.*?\*/",
        ]
        for pattern in sql_keywords:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        # Prevent XSS attempts
        xss_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe.*?>.*?</iframe>",
            r"<object.*?>.*?</object>",
            r"<embed.*?>.*?</embed>",
            r"<\?xml.*?\?>",
        ]
        for pattern in xss_patterns:
            print(f"Before applying pattern {pattern}:", repr(value))
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
            print(f"After applying pattern {pattern}:", repr(value))

        # Remove XML entity declarations
        value = re.sub(
            r"<!\[CDATA\[.*?\]\]>", "", value, flags=re.DOTALL | re.IGNORECASE
        )
        value = re.sub(r"<!ENTITY.*?>", "", value, flags=re.IGNORECASE)
        value = re.sub(r"<!DOCTYPE.*?>", "", value, flags=re.IGNORECASE)

        # Validate URLs
        url_pattern = r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+"
        for url in re.findall(url_pattern, value):
            if not validate_url(url):
                value = value.replace(url, "[URL_REMOVED]")

        # Remove javascript: protocol
        value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

        # Strip <script> tags (allowed elsewhere)
        print("Before stripping script tags:", repr(value))
        value = re.sub(
            r"<script.*?</script>", "", value, flags=re.DOTALL | re.IGNORECASE
        )
        print("After stripping script tags:", repr(value))

        # Process HTML entities: unescape outside code fences, keep code fences unchanged
        def process_entities(text: str) -> str:
            # Split on markdown code fences and process each segment.
            parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
            print("Parts:", parts)
            for i, part in enumerate(parts):
                print(f"Part {i}: {repr(part)}")
                if i % 2 == 0:
                    # Outside code fences: do not unescape HTML entities to preserve them as-is.
                    pass
                else:
                    # Inside code fences: unescape then re‑escape double quotes as HTML entity.
                    # But preserve the code fence markers
                    if part.startswith("```") and part.endswith("```"):
                        # Extract the content inside the code fence
                        content = part[3:-3]
                        print(f"Content: {repr(content)}")
                        # Unescape the content
                        content = html.unescape(content)
                        print(f"Unescaped content: {repr(content)}")
                        # Re-escape double quotes
                        content = content.replace('"', '"')
                        print(f"Re-escaped content: {repr(content)}")
                        # Reconstruct the code fence with preserved markers
                        parts[i] = f"```{content}```"
                    else:
                        # This shouldn't happen, but just in case
                        part = html.unescape(part)
                        part = part.replace('"', '"')
                        parts[i] = part
                print(f"Processed part {i}: {repr(parts[i])}")
            return "".join(parts)

        # Apply processing
        value = process_entities(value)
        print("After process_entities:", repr(value))

        # After processing, replace literal double quotes inside code fences with HTML entity
        def replace_quotes_in_code_fences(txt: str) -> str:
            def repl(match):
                block = match.group(0)
                # Preserve the code fence markers
                if block.startswith("```") and block.endswith("```"):
                    # Extract the content inside the code fence
                    content = block[3:-3]
                    # Replace double quotes with HTML entities
                    content = content.replace('"', '"')
                    # Reconstruct the code fence with preserved markers
                    return f"```{content}```"
                else:
                    # This shouldn't happen, but just in case
                    return block.replace('"', '"')

            return re.sub(r"```.*?```", repl, txt, flags=re.DOTALL)

        value = replace_quotes_in_code_fences(value)
        print("After replace_quotes_in_code_fences:", repr(value))

        return value
    return value


# Apply processing
value = _sanitize_input_impl(data)
print("Result:", repr(value))
