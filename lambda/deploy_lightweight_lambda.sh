#!/bin/bash
# Deploy lightweight Lambda function for daily scraping trigger

echo "Deploying lightweight daily scraper Lambda..."

# Create deployment package
zip lightweight_lambda.zip lightweight_daily_scraper.py

# Create Lambda function
aws lambda create-function \
  --function-name wildlife-daily-scraper-trigger \
  --runtime python3.11 \
  --role arn:aws:iam::723595141930:role/lambda-basic-execution \
  --handler lightweight_daily_scraper.lambda_handler \
  --zip-file fileb://lightweight_lambda.zip \
  --timeout 60 \
  --memory-size 256 \
  --environment Variables="{
    BACKEND_URL='https://wildlife-backend-final.eba-xhs2xrpi.us-east-2.elasticbeanstalk.com',
    USE_ECS='false'
  }" \
  --region us-east-2 \
  2>/dev/null || \
aws lambda update-function-code \
  --function-name wildlife-daily-scraper-trigger \
  --zip-file fileb://lightweight_lambda.zip \
  --region us-east-2

# Update configuration
aws lambda update-function-configuration \
  --function-name wildlife-daily-scraper-trigger \
  --timeout 60 \
  --memory-size 256 \
  --environment Variables="{
    BACKEND_URL='https://wildlife-backend-final.eba-xhs2xrpi.us-east-2.elasticbeanstalk.com',
    USE_ECS='false'
  }" \
  --region us-east-2

# Create EventBridge rule for daily execution at 2 AM UTC
aws events put-rule \
  --name wildlife-daily-scrape-trigger \
  --schedule-expression "cron(0 2 * * ? *)" \
  --description "Daily trigger for wildlife scraping" \
  --region us-east-2

# Get Lambda function ARN
FUNCTION_ARN=$(aws lambda get-function \
  --function-name wildlife-daily-scraper-trigger \
  --query 'Configuration.FunctionArn' \
  --output text \
  --region us-east-2)

# Add permission for EventBridge to invoke Lambda
aws lambda add-permission \
  --function-name wildlife-daily-scraper-trigger \
  --statement-id EventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:us-east-2:723595141930:rule/wildlife-daily-scrape-trigger \
  --region us-east-2 \
  2>/dev/null

# Add Lambda as target for EventBridge rule
aws events put-targets \
  --rule wildlife-daily-scrape-trigger \
  --targets "Id"="1","Arn"="$FUNCTION_ARN","Input"="{\"lookback_days\": 1}" \
  --region us-east-2

echo "Deployment complete!"
echo "Function: wildlife-daily-scraper-trigger"
echo "Schedule: Daily at 2 AM UTC (8 PM Mountain Time)"
echo ""
echo "To test manually:"
echo "aws lambda invoke --function-name wildlife-daily-scraper-trigger --payload '{\"lookback_days\": 1}' output.json --region us-east-2"