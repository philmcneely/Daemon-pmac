#!/bin/bash
# Fix MyPy issues systematically

echo "Starting mypy fixes..."

# First pass - fix simple missing return type annotations
echo "Fixing missing return type annotations..."

# Update functions that should return None
find app/ -name "*.py" -not -path "app/cli.py" -exec sed -i '' 's/def \([^(]*\)(\([^)]*\)):$/def \1(\2) -> None:/g' {} \;

# Fix UserCreate schema issue
echo "Fixing UserCreate schema..."
cat > /tmp/usercreate_fix.py << 'EOF'
import re

# Read the file
with open('app/schemas.py', 'r') as f:
    content = f.read()

# Find UserCreate class and add is_admin field
pattern = r'(class UserCreate\(BaseModel\):.*?password: str = Field\([^)]+\))'
replacement = r'\1\n    is_admin: bool = Field(default=False, description="Whether the user should be an admin")'

if 'is_admin: bool' not in content:
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('app/schemas.py', 'w') as f:
    f.write(content)

print("UserCreate schema updated")
EOF

python /tmp/usercreate_fix.py

echo "MyPy fixes phase 1 complete. Run mypy to see remaining issues."
