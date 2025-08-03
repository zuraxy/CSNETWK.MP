#!/usr/bin/env python3
"""
Create a simple test avatar image for demonstration
"""
import base64
import os

# Minimal 1x1 pixel PNG image (red pixel)
png_data = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AB2AA/2c7WfkAAAAASUVORK5CYII='
)

# Write to file in the root directory (one level up from testing)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
avatar_path = os.path.join(root_dir, 'test_avatar.png')

with open(avatar_path, 'wb') as f:
    f.write(png_data)

print(f"Created {avatar_path} - a 1x1 red pixel image for testing")
print("You can use this file when testing the PROFILE avatar functionality")
