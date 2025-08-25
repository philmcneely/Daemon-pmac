#!/usr/bin/env python3
import json
import os
import sys
import tempfile

sys.path.append("/Users/philmcneely/git/Daemon-pmac")

from app.resume_loader import load_resume_from_file

# Test data from the failing test
resume_data = {
    "personal": {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "555-1234",
    },
    "experience": [
        {
            "company": "Test Corp",
            "position": "Developer",
            "duration": "2020-2023",
        }
    ],
    "education": [{"institution": "Test University", "degree": "CS", "year": "2020"}],
}

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(resume_data, f)
    temp_path = f.name

try:
    result = load_resume_from_file(temp_path)
    print("Result:", result)
    if not result["success"]:
        print("Error:", result.get("error", "Unknown error"))
finally:
    os.unlink(temp_path)
