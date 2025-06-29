#!/usr/bin/env python3
"""
Deploy Lambda function for daily wildlife scraping to AWS.
"""

import boto3
import json
import os
from pathlib import Path

# AWS clients
lambda_client = boto3.client('lambda', region_name='us-east-2')
iam_client = boto3.client('iam', region_name='us-east-2')
events_client = boto3.client('events', region_name='us-east-2')

FUNCTION_NAME = 'wildlife-daily-scraper'
ROLE_NAME = 'wildlife-scraper-lambda-role'
RULE_NAME = 'wildlife-daily-scrape-schedule'

def create_lambda_role():
    """Create IAM role for Lambda function."""
    
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # Create role
        iam_client.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for wildlife scraper Lambda function'
        )
        
        # Attach basic Lambda execution policy
        iam_client.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        print(f"Created IAM role: {ROLE_NAME}")
        
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"IAM role {ROLE_NAME} already exists")
    
    # Get role ARN
    role = iam_client.get_role(RoleName=ROLE_NAME)
    return role['Role']['Arn']

def create_lambda_function(role_arn):
    """Create or update Lambda function."""
    
    # Read deployment package
    with open('wildlife_scraper_lambda.zip', 'rb') as f:
        zip_data = f.read()
    
    # Environment variables
    environment = {
        'Variables': {
            'SUPABASE_DB_URL': 'postgresql://postgres.rvrdbtrxwndeerqmziuo:huntingsightingschannel@aws-0-us-east-2.pooler.supabase.com:6543/postgres',
            'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
            'REDDIT_CLIENT_ID': os.environ.get('REDDIT_CLIENT_ID', ''),
            'REDDIT_CLIENT_SECRET': os.environ.get('REDDIT_CLIENT_SECRET', ''),
            'REDDIT_USER_AGENT': 'Wildlife Sightings Scraper/1.0',
            'GOOGLE_PLACES_API_KEY': os.environ.get('GOOGLE_PLACES_API_KEY', '')
        }
    }
    
    try:
        # Create function
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.11',
            Role=role_arn,
            Handler='daily_scraper.lambda_handler',
            Code={'ZipFile': zip_data},
            Description='Daily wildlife sightings scraper',
            Timeout=900,  # 15 minutes
            MemorySize=1024,  # 1GB
            Environment=environment,
            Architectures=['x86_64']
        )
        print(f"Created Lambda function: {FUNCTION_NAME}")
        return response['FunctionArn']
        
    except lambda_client.exceptions.ResourceConflictException:
        # Update existing function
        lambda_client.update_function_code(
            FunctionName=FUNCTION_NAME,
            ZipFile=zip_data
        )
        
        lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.11',
            Handler='daily_scraper.lambda_handler',
            Timeout=900,
            MemorySize=1024,
            Environment=environment
        )
        
        print(f"Updated Lambda function: {FUNCTION_NAME}")
        
        # Get function ARN
        response = lambda_client.get_function(FunctionName=FUNCTION_NAME)
        return response['Configuration']['FunctionArn']

def create_daily_schedule(function_arn):
    """Create EventBridge rule for daily execution."""
    
    # Create rule (runs at 2 AM UTC = 8 PM Mountain Time)
    try:
        events_client.put_rule(
            Name=RULE_NAME,
            ScheduleExpression='cron(0 2 * * ? *)',  # Daily at 2 AM UTC
            State='ENABLED',
            Description='Daily trigger for wildlife sightings scraper'
        )
        print(f"Created EventBridge rule: {RULE_NAME}")
    except Exception as e:
        print(f"Rule might already exist: {e}")
    
    # Add Lambda permission for EventBridge
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId='EventBridgeInvoke',
            Action='lambda:InvokeFunction',
            Principal='events.amazonaws.com',
            SourceArn=f'arn:aws:events:us-east-2:723595141930:rule/{RULE_NAME}'
        )
    except lambda_client.exceptions.ResourceConflictException:
        print("Permission already exists")
    
    # Add Lambda as target
    events_client.put_targets(
        Rule=RULE_NAME,
        Targets=[
            {
                'Id': '1',
                'Arn': function_arn,
                'Input': json.dumps({'lookback_days': 1})  # Daily lookback
            }
        ]
    )
    
    print("Daily schedule configured successfully!")

def main():
    """Deploy Lambda function with daily schedule."""
    
    print("Deploying wildlife scraper Lambda function...")
    
    # Check if deployment package exists
    if not Path('wildlife_scraper_lambda.zip').exists():
        print("Error: deployment package not found. Run create_deployment_package.sh first.")
        return
    
    # Create IAM role
    role_arn = create_lambda_role()
    
    # Wait for role to propagate
    import time
    print("Waiting for IAM role to propagate...")
    time.sleep(10)
    
    # Create/update Lambda function
    function_arn = create_lambda_function(role_arn)
    
    # Create daily schedule
    create_daily_schedule(function_arn)
    
    print("\nDeployment complete!")
    print(f"Function: {FUNCTION_NAME}")
    print(f"Schedule: Daily at 2 AM UTC (8 PM Mountain Time)")
    print("\nTo test manually, run:")
    print(f"aws lambda invoke --function-name {FUNCTION_NAME} --payload '{{\"lookback_days\": 1}}' output.json --region us-east-2")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()