#!/usr/bin/env python3
"""
Debug script to check if AWS credentials are loaded correctly
"""
import os
from dotenv import load_dotenv

print("=" * 50)
print("AWS Credentials Debug Check")
print("=" * 50)

# Load .env file
load_dotenv()

print("\n1. Checking .env file location:")
env_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(env_path):
    print(f"   ✓ .env file found at: {env_path}")
else:
    print(f"   ✗ .env file NOT found at: {env_path}")
    print("   Make sure .env is in the same folder where you run this script")

print("\n2. Checking environment variables:")
access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region = os.getenv('AWS_REGION')

if access_key:
    print(f"   ✓ AWS_ACCESS_KEY_ID: {access_key[:8]}... (showing first 8 chars)")
else:
    print("   ✗ AWS_ACCESS_KEY_ID: NOT SET")

if secret_key:
    print(f"   ✓ AWS_SECRET_ACCESS_KEY: {secret_key[:8]}... (showing first 8 chars)")
else:
    print("   ✗ AWS_SECRET_ACCESS_KEY: NOT SET")

if region:
    print(f"   ✓ AWS_REGION: {region}")
else:
    print("   ✗ AWS_REGION: NOT SET")

print("\n3. Checking .env file format:")
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        lines = f.readlines()
    print(f"   .env has {len(lines)} lines")
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#'):
            if '=' in line:
                key = line.split('=')[0]
                # Check for common mistakes
                if ' ' in key:
                    print(f"   ✗ Line {i}: Key has spaces: '{key}'")
                elif line.count('=') > 1:
                    print(f"   ✗ Line {i}: Multiple = signs")
                else:
                    print(f"   ✓ Line {i}: {key}")
            else:
                print(f"   ✗ Line {i}: No = sign found")

print("\n4. Testing AWS connection:")
if access_key and secret_key and region:
    try:
        import boto3
        client = boto3.client(
            'sts',  # STS just checks if credentials work
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        identity = client.get_caller_identity()
        print(f"   ✓ Credentials are VALID!")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
    except Exception as e:
        print(f"   ✗ Credentials are INVALID")
        print(f"   Error: {e}")
else:
    print("   ✗ Cannot test - credentials not loaded from .env")

print("\n" + "=" * 50)
print("Next steps:")
print("=" * 50)
if not access_key or not secret_key:
    print("1. Open your .env file")
    print("2. Make sure format is exactly:")
    print("   AWS_ACCESS_KEY_ID=your_key_here")
    print("   (no spaces, no quotes)")
    print("3. Save the file")
    print("4. Run this script again")
print("=" * 50)