"""
Configuration for Lambda environment.
Sets appropriate paths for AWS Lambda's read-only filesystem.
"""
import os

# Detect if running in Lambda
IS_LAMBDA = os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

# Set cache directory
if IS_LAMBDA:
    CACHE_DIR = "/tmp/cache"
else:
    CACHE_DIR = "data/cache"

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)