import base64
import os

def write_b64(path, b64_content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(b64_content))
    print(f"Written {path}")

print("Base64 writer ready")
