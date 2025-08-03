# Test avatar creation utility
# This file can be used to create test avatar images for profile testing

# Example usage:
# from PIL import Image
# import base64
# import io

# def create_test_avatar():
#     """Create a simple test avatar image"""
#     # Create a simple 64x64 colored square
#     img = Image.new('RGB', (64, 64), color='blue')
#     
#     # Save to bytes
#     img_bytes = io.BytesIO()
#     img.save(img_bytes, format='PNG')
#     img_bytes.seek(0)
#     
#     # Convert to base64
#     avatar_b64 = base64.b64encode(img_bytes.read()).decode('utf-8')
#     return avatar_b64

# Uncomment above code if you have PIL/Pillow installed
# pip install pillow
