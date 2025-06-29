#!/usr/bin/env python3
"""
Deploy updated scrapers to AWS Lambda.
"""

import boto3
import zipfile
import os
import io
from pathlib import Path
from loguru import logger

def create_deployment_package():
    """Create a deployment package with all scraper code."""
    logger.info("Creating deployment package...")
    
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all scraper files
        scrapers_dir = Path('scrapers')
        for file_path in scrapers_dir.glob('*.py'):
            arcname = f"scrapers/{file_path.name}"
            logger.info(f"Adding {arcname}")
            zipf.write(file_path, arcname)
        
        # Add requirements
        if Path('scrapers/requirements.txt').exists():
            zipf.write('scrapers/requirements.txt', 'requirements.txt')
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def update_lambda_function(function_name: str, zip_bytes: bytes):
    """Update a Lambda function with new code."""
    client = boto3.client('lambda', region_name='us-east-2')
    
    try:
        response = client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_bytes
        )
        logger.success(f"Updated {function_name} - CodeSha256: {response['CodeSha256']}")
        return True
    except Exception as e:
        logger.error(f"Failed to update {function_name}: {e}")
        return False

def main():
    """Deploy scrapers to Lambda."""
    logger.info("Deploying scrapers to AWS Lambda...")
    
    # Create deployment package
    zip_bytes = create_deployment_package()
    logger.info(f"Package size: {len(zip_bytes) / 1024 / 1024:.2f} MB")
    
    # Lambda function names
    functions = [
        'wildlife-daily-scraper'
    ]
    
    # Update each function
    success_count = 0
    for function_name in functions:
        if update_lambda_function(function_name, zip_bytes):
            success_count += 1
    
    logger.info(f"Successfully updated {success_count}/{len(functions)} Lambda functions")
    
    # Also update the environment variable for the model
    client = boto3.client('lambda', region_name='us-east-2')
    for function_name in functions:
        try:
            response = client.get_function_configuration(FunctionName=function_name)
            env_vars = response.get('Environment', {}).get('Variables', {})
            
            # Update OPENAI_MODEL if needed
            if env_vars.get('OPENAI_MODEL') != 'gpt-4.1-nano-2025-04-14':
                env_vars['OPENAI_MODEL'] = 'gpt-4.1-nano-2025-04-14'
                
                client.update_function_configuration(
                    FunctionName=function_name,
                    Environment={'Variables': env_vars}
                )
                logger.info(f"Updated {function_name} to use GPT-4.1 nano model")
        except Exception as e:
            logger.error(f"Failed to update environment for {function_name}: {e}")

if __name__ == "__main__":
    main()