#!/usr/bin/env python3
"""
Create a simple test avatar image for demonstration
"""
import base64

# Minimal 1x1 pixel PNG image (red pixel)
png_data = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AB2AA/2c7WfkAAAAASUVORK5CYII='
)

# Write to file
with open('test_avatar.png', 'wb') as f:
    f.write(png_data)

print("Created test_avatar.png - a 1x1 red pixel image for testing")
print("You can use this file when testing the PROFILE avatar functionality")
