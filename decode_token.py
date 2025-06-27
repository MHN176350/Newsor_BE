#!/usr/bin/env python
"""
Script to decode and check JWT token
"""

import base64
import json
from datetime import datetime

def decode_jwt_payload(token):
    """Decode JWT token payload"""
    try:
        # Split the token
        parts = token.split('.')
        if len(parts) != 3:
            print("Invalid JWT token format")
            return
        
        # Decode the payload (second part)
        payload = parts[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        
        # Decode from base64
        decoded = base64.b64decode(payload)
        payload_data = json.loads(decoded)
        
        print("Token payload:")
        print(json.dumps(payload_data, indent=2))
        
        # Check expiration
        if 'exp' in payload_data:
            exp_time = datetime.fromtimestamp(payload_data['exp'])
            current_time = datetime.now()
            print(f"\nToken expires at: {exp_time}")
            print(f"Current time: {current_time}")
            
            if current_time > exp_time:
                print("❌ TOKEN IS EXPIRED!")
            else:
                remaining = exp_time - current_time
                print(f"✅ Token is valid for {remaining}")
        
        return payload_data
        
    except Exception as e:
        print(f"Error decoding token: {e}")

if __name__ == "__main__":
    # Your token from the console
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzUxMDE0Mzg0LCJvcmlnSWF0IjoxNzUxMDE0MDg0fQ.XYlNFQrXl0UmH5xxx-c_PRv2i1acPkDtUFwVmBbG19E"
    decode_jwt_payload(token)
