# Daily Scraping Setup Guide

This guide explains how to set up automated daily scraping of wildlife sightings on AWS.

## Overview

The daily scraping system consists of:
1. **AWS Lambda** - Lightweight trigger function
2. **EventBridge** - Schedules daily execution 
3. **Backend API** - Handles the actual scraping
4. **Supabase** - Stores the scraped data

## Architecture Options

### Option 1: Lambda Trigger + Backend API (Recommended)
- Lambda function triggers backend endpoint
- Backend runs scrapers as background task
- Works with existing Elastic Beanstalk deployment

### Option 2: Direct Lambda Execution
- Lambda runs scrapers directly
- Limited by 15-minute timeout
- Requires larger deployment package

### Option 3: ECS/Fargate
- Lambda triggers ECS task
- No timeout limitations
- More complex setup

## Implementation (Option 1)

### 1. Update Backend

Add the admin endpoint to your backend's main router:

```python
# backend/app/main.py
from app.api.v1 import admin

app.include_router(admin.router, prefix="/api/v1")
```

### 2. Set Environment Variables

Update Elastic Beanstalk configuration:
```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    ADMIN_API_KEY: "your-secure-api-key-here"
```

### 3. Deploy Lambda Function

```bash
# Create the Lambda function
cd lambda
zip lightweight_lambda.zip lightweight_daily_scraper.py

aws lambda create-function \
  --function-name wildlife-daily-scraper \
  --runtime python3.11 \
  --role arn:aws:iam::723595141930:role/wildlife-lambda-execution-role \
  --handler lightweight_daily_scraper.lambda_handler \
  --zip-file fileb://lightweight_lambda.zip \
  --timeout 60 \
  --environment Variables="{
    BACKEND_URL='https://wildlife-backend-final.eba-xhs2xrpi.us-east-2.elasticbeanstalk.com',
    API_KEY='your-secure-api-key-here'
  }" \
  --region us-east-2
```

### 4. Create Daily Schedule

```bash
# Create EventBridge rule for daily execution at 2 AM UTC (8 PM MT)
aws events put-rule \
  --name wildlife-daily-scrape \
  --schedule-expression "cron(0 2 * * ? *)" \
  --region us-east-2

# Add Lambda permission
aws lambda add-permission \
  --function-name wildlife-daily-scraper \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --region us-east-2

# Connect rule to Lambda
aws events put-targets \
  --rule wildlife-daily-scrape \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-2:723595141930:function:wildlife-daily-scraper" \
  --region us-east-2
```

## Testing

### Manual Lambda Test
```bash
aws lambda invoke \
  --function-name wildlife-daily-scraper \
  --payload '{"lookback_days": 1}' \
  output.json \
  --region us-east-2
```

### Direct API Test
```bash
curl -X POST https://wildlife-backend-final.eba-xhs2xrpi.us-east-2.elasticbeanstalk.com/api/v1/admin/trigger-scrape \
  -H "X-API-Key: your-secure-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"lookback_days": 1}'
```

## Monitoring

### CloudWatch Logs
- Lambda logs: `/aws/lambda/wildlife-daily-scraper`
- Backend logs: Check Elastic Beanstalk logs

### Set Up Alerts
```bash
# Create SNS topic for notifications
aws sns create-topic --name wildlife-scraper-alerts --region us-east-2

# Subscribe to email notifications
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-2:723595141930:wildlife-scraper-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Estimated Costs

- **Lambda**: ~$0.00 per month (minimal invocations)
- **EventBridge**: Free tier covers daily schedule
- **Elastic Beanstalk**: Already running for API
- **API calls**: OpenAI API costs for LLM validation

## Troubleshooting

### Lambda Timeout
- Increase Lambda timeout (max 15 minutes)
- Or use ECS/Fargate for longer runs

### Rate Limiting
- Scrapers include 15-20 second delays between LLM calls
- Daily scraping with 1-day lookback minimizes API usage

### Database Connection
- Ensure Supabase allows connections from AWS
- Check connection pooling settings

## Alternative: Local Cron Job

If you prefer running scrapers locally:

```bash
# Add to crontab
0 20 * * * cd /path/to/project && python scripts/fresh_scrape_to_supabase.py
```

## Next Steps

1. Deploy updated backend with admin endpoints
2. Create Lambda function
3. Set up EventBridge schedule
4. Monitor first few runs
5. Adjust schedule/lookback as needed