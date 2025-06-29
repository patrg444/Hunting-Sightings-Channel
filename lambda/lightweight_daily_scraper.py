"""
Lightweight AWS Lambda function for daily wildlife sighting scraping.
Uses AWS Step Functions or ECS for the actual scraping to avoid Lambda limitations.
"""

import os
import json
import boto3
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
ecs_client = boto3.client('ecs', region_name='us-east-2')
sns_client = boto3.client('sns', region_name='us-east-2')

def lambda_handler(event, context):
    """
    Lambda handler that triggers ECS task for daily scraping.
    This avoids Lambda's 15-minute timeout for long-running scrapers.
    """
    
    lookback_days = event.get('lookback_days', 1)
    
    logger.info(f"Triggering daily scrape with {lookback_days} day lookback")
    
    try:
        # Option 1: Trigger ECS task (recommended for long-running tasks)
        if os.environ.get('USE_ECS', 'false').lower() == 'true':
            response = trigger_ecs_task(lookback_days)
            logger.info(f"Started ECS task: {response['taskArn']}")
        
        # Option 2: Direct HTTP trigger to backend endpoint
        else:
            response = trigger_backend_endpoint(lookback_days)
            logger.info(f"Triggered backend scraping endpoint: {response}")
        
        # Send notification
        send_notification(f"Daily wildlife scraping started with {lookback_days} day lookback")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Daily scraping triggered successfully',
                'lookback_days': lookback_days,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error triggering daily scrape: {e}")
        send_notification(f"Daily scraping failed: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }

def trigger_ecs_task(lookback_days):
    """Trigger ECS task for scraping."""
    
    cluster = os.environ.get('ECS_CLUSTER', 'wildlife-scraper-cluster')
    task_definition = os.environ.get('ECS_TASK_DEFINITION', 'wildlife-scraper-task')
    subnet_ids = os.environ.get('SUBNET_IDS', '').split(',')
    security_group = os.environ.get('SECURITY_GROUP_ID', '')
    
    response = ecs_client.run_task(
        cluster=cluster,
        taskDefinition=task_definition,
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': subnet_ids,
                'securityGroups': [security_group],
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'scraper',
                    'environment': [
                        {
                            'name': 'LOOKBACK_DAYS',
                            'value': str(lookback_days)
                        }
                    ]
                }
            ]
        }
    )
    
    return response['tasks'][0]

def trigger_backend_endpoint(lookback_days):
    """Trigger scraping via backend API endpoint."""
    
    import requests
    
    backend_url = os.environ.get(
        'BACKEND_URL', 
        'https://wildlife-backend-final.eba-xhs2xrpi.us-east-2.elasticbeanstalk.com'
    )
    api_key = os.environ.get('API_KEY', '')
    
    response = requests.post(
        f"{backend_url}/api/v1/admin/trigger-scrape",
        json={'lookback_days': lookback_days},
        headers={'X-API-Key': api_key} if api_key else {},
        timeout=30
    )
    
    response.raise_for_status()
    return response.json()

def send_notification(message):
    """Send SNS notification about scraping status."""
    
    topic_arn = os.environ.get('SNS_TOPIC_ARN')
    if not topic_arn:
        return
    
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject='Wildlife Scraper Status',
            Message=message
        )
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")