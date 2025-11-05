# Atlas Engine Dev Alias Deployment - CLI Commands

## Overview
This guide provides AWS CLI commands to deploy X-Ray instrumented Lambda functions with a new "Dev" alias while keeping your "PROD" alias unchanged.

**Region:** us-west-2  
**Functions:** LexFulfillmentHandler, GenerateDynamicScenarioHandler, InvokeOutboundCallHandler, UpdateLeadHandler

---

## Prerequisites

```bash
# Ensure AWS CLI is configured for us-west-2
aws configure get region
# Should output: us-west-2

# Navigate to the lambda directory
cd /Users/johndoe/Downloads/aws_org_export/lambda
```

---

## Option 1: Automated Deployment (Recommended)

```bash
# Make the deployment script executable
chmod +x deploy_dev_alias.sh

# Run the deployment script
./deploy_dev_alias.sh
```

This script will:
- Deploy all 4 functions with X-Ray instrumentation
- Create/update the "Dev" alias for each function
- Enable Active X-Ray tracing
- Preserve your existing "PROD" alias

---

## Option 2: Manual Deployment (Step-by-Step)

### Step 1: Add X-Ray Permissions to IAM Roles

```bash
# LexFulfillmentHandler Role
aws iam put-role-policy \
  --role-name LexFulfillmentHandler-role-gf8r6bq2 \
  --policy-name XRayAccess \
  --policy-document file://iam_xray_policy.json \
  --region us-west-2

# GenerateDynamicScenarioHandler Role
aws iam put-role-policy \
  --role-name GenerateDynamicScenarioHandler-role-vbv9ftg1 \
  --policy-name XRayAccess \
  --policy-document file://iam_xray_policy.json \
  --region us-west-2

# InvokeOutboundCallHandler Role
aws iam put-role-policy \
  --role-name InvokeOutboundCallHandler-role-p7ou5zno \
  --policy-name XRayAccess \
  --policy-document file://iam_xray_policy.json \
  --region us-west-2

# UpdateLeadHandler Role (uses CreateLeadHandler role)
aws iam put-role-policy \
  --role-name CreateLeadHandler-role-sduo9h9n \
  --policy-name XRayAccess \
  --policy-document file://iam_xray_policy.json \
  --region us-west-2
```

---

### Step 2: Deploy LexFulfillmentHandler

```bash
cd LexFulfillmentHandler_code

# Copy the Dev version to lambda_function.py
cp lambda_function_dev.py lambda_function.py

# Create deployment package
zip -r function_dev.zip lambda_function.py

# Install X-Ray SDK
pip install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/

# Update function code
aws lambda update-function-code \
  --function-name LexFulfillmentHandler \
  --zip-file fileb://function_dev.zip \
  --region us-west-2

# Wait for update to complete
aws lambda wait function-updated \
  --function-name LexFulfillmentHandler \
  --region us-west-2

# Publish new version
VERSION_LFH=$(aws lambda publish-version \
  --function-name LexFulfillmentHandler \
  --region us-west-2 \
  --query 'Version' \
  --output text)

echo "Published version: $VERSION_LFH"

# Create Dev alias (or update if exists)
aws lambda create-alias \
  --function-name LexFulfillmentHandler \
  --name Dev \
  --function-version $VERSION_LFH \
  --region us-west-2 2>/dev/null || \
aws lambda update-alias \
  --function-name LexFulfillmentHandler \
  --name Dev \
  --function-version $VERSION_LFH \
  --region us-west-2

# Enable X-Ray Active Tracing
aws lambda update-function-configuration \
  --function-name LexFulfillmentHandler \
  --tracing-config Mode=Active \
  --region us-west-2

cd ..
```

---

### Step 3: Deploy GenerateDynamicScenarioHandler

```bash
cd GenerateDynamicScenarioHandler_code

cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/

aws lambda update-function-code \
  --function-name GenerateDynamicScenarioHandler \
  --zip-file fileb://function_dev.zip \
  --region us-west-2

aws lambda wait function-updated \
  --function-name GenerateDynamicScenarioHandler \
  --region us-west-2

VERSION_GDSH=$(aws lambda publish-version \
  --function-name GenerateDynamicScenarioHandler \
  --region us-west-2 \
  --query 'Version' \
  --output text)

echo "Published version: $VERSION_GDSH"

aws lambda create-alias \
  --function-name GenerateDynamicScenarioHandler \
  --name Dev \
  --function-version $VERSION_GDSH \
  --region us-west-2 2>/dev/null || \
aws lambda update-alias \
  --function-name GenerateDynamicScenarioHandler \
  --name Dev \
  --function-version $VERSION_GDSH \
  --region us-west-2

aws lambda update-function-configuration \
  --function-name GenerateDynamicScenarioHandler \
  --tracing-config Mode=Active \
  --region us-west-2

cd ..
```

---

### Step 4: Deploy InvokeOutboundCallHandler

```bash
cd InvokeOutboundCallHandler_code

cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/

aws lambda update-function-code \
  --function-name InvokeOutboundCallHandler \
  --zip-file fileb://function_dev.zip \
  --region us-west-2

aws lambda wait function-updated \
  --function-name InvokeOutboundCallHandler \
  --region us-west-2

VERSION_IOCH=$(aws lambda publish-version \
  --function-name InvokeOutboundCallHandler \
  --region us-west-2 \
  --query 'Version' \
  --output text)

echo "Published version: $VERSION_IOCH"

aws lambda create-alias \
  --function-name InvokeOutboundCallHandler \
  --name Dev \
  --function-version $VERSION_IOCH \
  --region us-west-2 2>/dev/null || \
aws lambda update-alias \
  --function-name InvokeOutboundCallHandler \
  --name Dev \
  --function-version $VERSION_IOCH \
  --region us-west-2

aws lambda update-function-configuration \
  --function-name InvokeOutboundCallHandler \
  --tracing-config Mode=Active \
  --region us-west-2

cd ..
```

---

### Step 5: Deploy UpdateLeadHandler

```bash
cd UpdateLeadHandler_code

cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/

aws lambda update-function-code \
  --function-name UpdateLeadHandler \
  --zip-file fileb://function_dev.zip \
  --region us-west-2

aws lambda wait function-updated \
  --function-name UpdateLeadHandler \
  --region us-west-2

VERSION_ULH=$(aws lambda publish-version \
  --function-name UpdateLeadHandler \
  --region us-west-2 \
  --query 'Version' \
  --output text)

echo "Published version: $VERSION_ULH"

aws lambda create-alias \
  --function-name UpdateLeadHandler \
  --name Dev \
  --function-version $VERSION_ULH \
  --region us-west-2 2>/dev/null || \
aws lambda update-alias \
  --function-name UpdateLeadHandler \
  --name Dev \
  --function-version $VERSION_ULH \
  --region us-west-2

aws lambda update-function-configuration \
  --function-name UpdateLeadHandler \
  --tracing-config Mode=Active \
  --region us-west-2

cd ..
```

---

## Step 6: Enable X-Ray Tracing on Step Functions

```bash
# Get the current Step Function definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow \
  --region us-west-2 \
  --query 'definition' \
  --output text > current_definition.json

# Update Step Function with X-Ray tracing enabled
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow \
  --tracing-configuration enabled=true \
  --region us-west-2

echo "✓ X-Ray tracing enabled on AtlasEngineWorkflow"
```

---

## Step 7: Create Dev Version of Step Function (Optional)

If you want to test with a separate Step Function that uses the Dev aliases:

```bash
# Download the current definition
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow \
  --region us-west-2 > aew_definition.json

# Manually edit the JSON to replace function ARNs with :Dev aliases
# Example: arn:aws:lambda:us-west-2:<AWS_ACCOUNT_ID>:function:LexFulfillmentHandler
# Becomes: arn:aws:lambda:us-west-2:<AWS_ACCOUNT_ID>:function:LexFulfillmentHandler:Dev

# Create new Step Function
aws stepfunctions create-state-machine \
  --name AtlasEngineWorkflow-Dev \
  --definition file://aew_definition_dev.json \
  --role-arn arn:aws:iam::<AWS_ACCOUNT_ID>:role/service-role/StepFunctions-AtlasEngineWorkflow-role \
  --tracing-configuration enabled=true \
  --region us-west-2
```

---

## Verification Commands

### Check Alias Configuration

```bash
# Verify Dev alias for each function
aws lambda get-alias \
  --function-name LexFulfillmentHandler \
  --name Dev \
  --region us-west-2

aws lambda get-alias \
  --function-name GenerateDynamicScenarioHandler \
  --name Dev \
  --region us-west-2

aws lambda get-alias \
  --function-name InvokeOutboundCallHandler \
  --name Dev \
  --region us-west-2

aws lambda get-alias \
  --function-name UpdateLeadHandler \
  --name Dev \
  --region us-west-2
```

### Check X-Ray Tracing Status

```bash
# Check X-Ray configuration for each function
aws lambda get-function-configuration \
  --function-name LexFulfillmentHandler \
  --region us-west-2 \
  --query 'TracingConfig'

aws lambda get-function-configuration \
  --function-name GenerateDynamicScenarioHandler \
  --region us-west-2 \
  --query 'TracingConfig'

aws lambda get-function-configuration \
  --function-name InvokeOutboundCallHandler \
  --region us-west-2 \
  --query 'TracingConfig'

aws lambda get-function-configuration \
  --function-name UpdateLeadHandler \
  --region us-west-2 \
  --query 'TracingConfig'

# Check Step Function tracing
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow \
  --region us-west-2 \
  --query 'tracingConfiguration'
```

### Test Invocation with Dev Alias

```bash
# Test LexFulfillmentHandler:Dev
aws lambda invoke \
  --function-name LexFulfillmentHandler:Dev \
  --payload '{"sessionState":{"intent":{"name":"GreetingIntent"}},"inputTranscript":"hello"}' \
  --region us-west-2 \
  response.json

cat response.json
```

---

## Monitoring & Debugging

### View CloudWatch Logs with Structured Timing

```bash
# Stream logs for LexFulfillmentHandler
aws logs tail /aws/lambda/LexFulfillmentHandler --follow --region us-west-2

# Filter for timing logs only
aws logs filter-log-events \
  --log-group-name /aws/lambda/LexFulfillmentHandler \
  --filter-pattern '{ $.event_type = "TIMING" }' \
  --region us-west-2

# Get specific metric (e.g., BedrockCallDuration)
aws logs filter-log-events \
  --log-group-name /aws/lambda/LexFulfillmentHandler \
  --filter-pattern '{ $.metric = "BedrockCallDuration" }' \
  --region us-west-2
```

### View X-Ray Traces

```bash
# Get trace summaries for the last hour
START_TIME=$(date -u -v-1H +%s)
END_TIME=$(date -u +%s)

aws xray get-trace-summaries \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --region us-west-2

# Get specific trace details (replace TRACE_ID)
aws xray batch-get-traces \
  --trace-ids "TRACE_ID_HERE" \
  --region us-west-2
```

### X-Ray Console URLs

- **Service Map:** https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/service-map
- **Traces:** https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/traces

---

## Rollback Commands

If you need to rollback the Dev alias to a previous version:

```bash
# List all versions
aws lambda list-versions-by-function \
  --function-name LexFulfillmentHandler \
  --region us-west-2

# Update Dev alias to point to a specific version
aws lambda update-alias \
  --function-name LexFulfillmentHandler \
  --name Dev \
  --function-version <VERSION_NUMBER> \
  --region us-west-2
```

---

## Key Metrics to Monitor

Based on the structured logs, you can query for these metrics:

1. **LexFulfillmentHandler (LFH)**
   - `BedrockCallDuration` - Time for Bedrock AI generation
   - `SecretsManagerDuration` - Time to fetch Salesforce credentials
   - `SalesforceAuthDuration` - Time for Salesforce OAuth
   - `total_function_duration` - End-to-end function time

2. **GenerateDynamicScenarioHandler (GDSH)**
   - `BedrockCallDuration` - Time for scenario generation
   - `total_function_duration` - End-to-end function time

3. **InvokeOutboundCallHandler (IOCH)**
   - `DynamoDBPutDuration` - Time to store scenario in DynamoDB
   - `ConnectCallDuration` - Time to initiate outbound call
   - `DynamoDBUpdateDuration` - Time to update with ContactId
   - `total_function_duration` - End-to-end function time

4. **UpdateLeadHandler (ULH)**
   - `SalesforceAuthDuration` - Time for Salesforce authentication
   - `SalesforceUpdateDuration` - Time to update Lead record
   - `total_function_duration` - End-to-end function time

---

## Expected Log Format

```json
{"level": "INFO", "event_type": "START", "function_name": "GDSH", "message": "Function started"}
{"level": "INFO", "event_type": "TIMING", "function_name": "GDSH", "metric": "BedrockCallDuration", "value_sec": 2.847}
{"level": "INFO", "event_type": "END", "function_name": "GDSH", "message": "Function completed", "total_function_duration": 3.125}
```

---

## Notes

- The "PROD" alias remains unchanged and continues to use the original code
- All X-Ray traces will show subsegments for external calls (Bedrock, Connect, Salesforce, DynamoDB)
- Structured logs are in JSON format for easy parsing with CloudWatch Insights
- Each function logs start time, individual operation durations, and total duration
- X-Ray SDK automatically instruments boto3 clients for AWS service calls
