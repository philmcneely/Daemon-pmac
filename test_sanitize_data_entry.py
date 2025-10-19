import html
import re
from typing import Any

# Test the sanitize_data_entry function
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


def sanitize_data_entry(data: Any) -> Any:
    """Sanitize data entry by removing HTML tags while preserving entities."""
    if isinstance(data, str):
        # Remove HTML tags but preserve HTML entities
        # First, temporarily replace HTML entities with placeholders
        import html
        import re

        # Process HTML entities: unescape outside code fences, keep code fences unchanged
        def process_entities(text: str) -> str:
            # Split on markdown code fences and process each segment.
            parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
            print("Parts:", parts)
            for i, part in enumerate(parts):
                print(f"Part {i}: {repr(part)}")
                if i % 2 == 0:
                    # Outside code fences: do not unescape HTML entities to preserve them as-is.
                    # Find and temporarily replace HTML entities
                    entities = {}

                    def replace_entity(match):
                        entity = match.group(0)
                        placeholder = f"__ENTITY_{len(entities)}__"
                        entities[placeholder] = entity
                        return placeholder

                    # Replace HTML entities with placeholders
                    part_with_placeholders = re.sub(
                        r"&[a-zA-Z]+;|&#\d+;|&#x[0-9a-fA-F]+;|&", replace_entity, part
                    )
                    print(f"Part with placeholders: {repr(part_with_placeholders)}")
                    print(f"Entities: {entities}")

                    # Remove HTML tags
                    sanitized_part = re.sub(r"<[^>]*>", "", part_with_placeholders)
                    print(f"Sanitized part: {repr(sanitized_part)}")

                    # Restore HTML entities
                    for placeholder, entity in entities.items():
                        sanitized_part = sanitized_part.replace(placeholder, entity)
                    print(f"Restored part: {repr(sanitized_part)}")

                    parts[i] = sanitized_part
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
        sanitized = process_entities(data)
        print("Sanitized:", repr(sanitized))

        # Only escape quotes to prevent XSS, don't escape other HTML entities
        sanitized = sanitized.replace('"', '"').replace("'", "'")
        print("Final sanitized:", repr(sanitized))
        return sanitized
    if isinstance(data, dict):
        return {key: sanitize_data_entry(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_data_entry(item) for item in data]
    return data


# Apply processing
value = sanitize_data_entry(data)
print("Result:", repr(value))
