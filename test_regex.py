import re

data = '### Problem: HTML & JavaScript Issues\n\n<script> tags are being escaped incorrectly\n\n**Code example:**\n```html\n<div class="problem">\n  <p>User input: "special characters"</p>\n</div>\n```'

# Find and temporarily replace HTML entities
entities = {}


def replace_entity(match):
    entity = match.group(0)
    placeholder = f"__ENTITY_{len(entities)}__"
    entities[placeholder] = entity
    print(f"Replacing entity: {entity} with placeholder: {placeholder}")
    return placeholder


# Replace HTML entities with placeholders
text_with_placeholders = re.sub(
    r"&[a-zA-Z]+;|&#\d+;|&#x[0-9a-fA-F]+;|&", replace_entity, data
)
print(f"Text with placeholders: {text_with_placeholders}")
print(f"Entities found: {entities}")

# Remove HTML tags
sanitized = re.sub(r"<[^>]*>", "", text_with_placeholders)
print(f"Text after removing HTML tags: {sanitized}")

# Restore HTML entities
for placeholder, entity in entities.items():
    sanitized = sanitized.replace(placeholder, entity)
print(f"Text after restoring entities: {sanitized}")
