import html
import re

# Test the process_entities function
text = """## Code Analysis

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
value = process_entities(text)
print("Result:", repr(value))
