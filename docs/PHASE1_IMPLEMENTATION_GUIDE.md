# Phase 1 Implementation Guide: Quick Wins
## Target: Reduce latency by 4-6 seconds in 3-4 hours

---

## Overview

Phase 1 focuses on LOW-COMPLEXITY, HIGH-IMPACT changes that can be implemented in a single day.

**Expected Results:**
- Current: 9+ seconds
- After Phase 1: 3-5 seconds ✅ **MEETS TARGET**
- Time Investment: 3-4 hours
- Risk Level: LOW

---

## Task 1: Point Lex to Lambda Version 28 (Provisioned Concurrency)
**Impact:** -3 to -4 seconds  
**Time:** 15 minutes  
**Risk:** LOW

### Problem
Lex bot is currently invoking `$LATEST` version of LexFulfillmentHandler, which has cold starts. Version 28 has provisioned concurrency configured but is not being used.

### Solution

#### Step 1: Verify Provisioned Concurrency
```bash
aws lambda get-provisioned-concurrency-config \
  --function-name LexFulfillmentHandler \
  --qualifier 28 \
  --region us-west-2
```

Expected output:
```json
{
  "RequestedProvisionedConcurrentExecutions": 1,
  "AllocatedProvisionedConcurrentExecutions": 1,
  "Status": "READY"
}
```

#### Step 2: Update Lex Bot Alias
```bash
# Get current bot alias configuration
aws lexv2-models describe-bot-alias \
  --bot-id <BOT_ID> \
  --bot-alias-id <ALIAS_ID> \
  --region us-west-2

# Update Lambda function version in bot alias
aws lexv2-models update-bot-alias \
  --bot-id <BOT_ID> \
  --bot-alias-id <ALIAS_ID> \
  --bot-alias-name Production \
  --bot-version <VERSION> \
  --bot-alias-locale-settings '{
    "en_US": {
      "enabled": true,
      "codeHookSpecification": {
        "lambdaCodeHook": {
          "lambdaARN": "arn:aws:lambda:us-west-2:<AWS_ACCOUNT_ID>:function:LexFulfillmentHandler:28",
          "codeHookInterfaceVersion": "1.0"
        }
      }
    }
  }' \
  --region us-west-2
```

#### Step 3: Verify Change
```bash
# Test invocation
aws lambda invoke \
  --function-name LexFulfillmentHandler:28 \
  --payload '{"sessionState":{"intent":{"name":"GreetingIntent"}}}' \
  --region us-west-2 \
  response.json

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=LexFulfillmentHandler Name=Resource,Value=LexFulfillmentHandler:28 \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average \
  --region us-west-2
```

### Validation
- Cold start metrics should drop to 0
- Average duration should decrease by 3-4 seconds
- No errors in CloudWatch Logs

---

## Task 2: Implement Secrets Manager Caching
**Impact:** -300 to -500ms  
**Time:** 45 minutes  
**Risk:** LOW

### Problem
Every invocation of `get_sf_connection()` calls Secrets Manager API, adding 300ms latency.

### Solution

#### Step 1: Update LexFulfillmentHandler Code

**File:** `lambda/LexFulfillmentHandler_code/lambda_function.py`

**BEFORE:**
```python
def get_sf_connection():
    secret_arn = os.environ['SALESFORCE_SECRET_ARN']
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(SecretId=secret_arn)
    creds = json.loads(secret['SecretString'])
    # ... rest of function ...
```

**AFTER:**
```python
import time

# Global cache
_sf_credentials_cache = None
_sf_credentials_cache_time = 0
CACHE_TTL = 300  # 5 minutes

def get_sf_credentials():
    """Get Salesforce credentials with caching."""
    global _sf_credentials_cache, _sf_credentials_cache_time
    
    current_time = time.time()
    if _sf_credentials_cache and (current_time - _sf_credentials_cache_time < CACHE_TTL):
        logger.info("[CACHE] Using cached Salesforce credentials")
        return _sf_credentials_cache
    
    logger.info("[CACHE] Fetching fresh Salesforce credentials")
    secret_arn = os.environ['SALESFORCE_SECRET_ARN']
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(SecretId=secret_arn)
    creds = json.loads(secret['SecretString'])
    
    _sf_credentials_cache = creds
    _sf_credentials_cache_time = current_time
    return creds

def get_sf_connection():
    creds = get_sf_credentials()  # Now uses cache
    
    # Determine the OAuth endpoint
    is_sandbox = creds.get('is_sandbox', False)
    endpoint = 'https://test.salesforce.com' if is_sandbox else 'https://login.salesforce.com'
    
    # Create JWT
    now = datetime.utcnow()
    payload = {
        'iss': creds['client_id'],
        'sub': creds['username'],
        'aud': endpoint,
        'exp': now + timedelta(minutes=5)
    }
    
    private_key = creds['private_key']
    jwt_token = encode(payload, private_key, algorithm='RS256')
    
    # Exchange JWT for access token
    result = requests.post(
        endpoint + '/services/oauth2/token',
        data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': jwt_token
        }
    )
    
    body = result.json()
    
    if result.status_code != 200:
        logger.error(f"[SF AUTH] JWT exchange failed: {body}")
        raise SalesforceAuthenticationFailed(body.get('error', 'Unknown'), 
                                            body.get('error_description', 'JWT token exchange failed'))
    
    logger.info(f"[SF AUTH] Successfully authenticated. Instance: {body['instance_url']}")
    return Salesforce(instance_url=body['instance_url'], session_id=body['access_token'])
```

#### Step 2: Update CreateLeadHandler Code

**File:** `lambda/CreateLeadHandler_code/lambda_function.py`

**Add at top of file:**
```python
import time

# Global cache
_sf_credentials_cache = None
_sf_credentials_cache_time = 0
CACHE_TTL = 300  # 5 minutes
```

**Replace `get_salesforce_credentials` function:**
```python
def get_salesforce_credentials(secret_arn):
    """
    Retrieve Salesforce JWT credentials from AWS Secrets Manager with caching.
    """
    global _sf_credentials_cache, _sf_credentials_cache_time
    
    current_time = time.time()
    if _sf_credentials_cache and (current_time - _sf_credentials_cache_time < CACHE_TTL):
        logger.info("Using cached Salesforce credentials")
        return _sf_credentials_cache
    
    try:
        logger.info(f"Retrieving credentials from secret: {secret_arn}")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_string = response['SecretString']
        credentials = json.loads(secret_string)
        
        # Validate required credentials
        required_keys = ['username', 'client_id', 'private_key']
        for key in required_keys:
            if key not in credentials:
                raise ValueError(f"Missing required credential for JWT flow: {key}")
        
        _sf_credentials_cache = credentials
        _sf_credentials_cache_time = current_time
        
        logger.info("Successfully retrieved Salesforce JWT credentials")
        return credentials
    
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving credentials: {e}")
        raise
```

#### Step 3: Deploy Changes
```bash
cd /Users/johndoe/Downloads/aws_org_export/lambda/LexFulfillmentHandler_code
zip -r function.zip lambda_function.py

aws lambda update-function-code \
  --function-name LexFulfillmentHandler \
  --zip-file fileb://function.zip \
  --region us-west-2

# Publish new version
aws lambda publish-version \
  --function-name LexFulfillmentHandler \
  --region us-west-2

# Update provisioned concurrency to new version (e.g., 29)
aws lambda put-provisioned-concurrency-config \
  --function-name LexFulfillmentHandler \
  --qualifier 29 \
  --provisioned-concurrent-executions 1 \
  --region us-west-2

# Update Lex to use new version
# (Repeat Step 2 from Task 1 with version 29)
```

### Validation
```bash
# Check CloudWatch Logs for cache hits
aws logs filter-log-events \
  --log-group-name /aws/lambda/LexFulfillmentHandler \
  --filter-pattern "[CACHE]" \
  --start-time $(date -u -d '5 minutes ago' +%s)000 \
  --region us-west-2
```

Expected: "Using cached Salesforce credentials" messages

---

## Task 3: Cache DynamoDB Scenario in Session Attributes
**Impact:** -100 to -300ms per turn  
**Time:** 30 minutes  
**Risk:** LOW

### Problem
On every phone call turn, LexFulfillmentHandler queries DynamoDB to retrieve the dynamic scenario.

### Solution

**File:** `lambda/LexFulfillmentHandler_code/lambda_function.py`

**BEFORE:**
```python
if interaction_key:
    # Retrieve scenario from DynamoDB
    try:
        # ... parse interaction_key ...
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'PK': pk, 'SK': sk})
        if 'Item' in response:
            dynamodb_item = response['Item']
            dynamic_scenario = dynamodb_item.get('DynamicScenario')
            # Store in session for subsequent turns
            session_attributes['dynamicScenario'] = dynamic_scenario
```

**AFTER:**
```python
if interaction_key:
    # Check if scenario is already in session (cached from previous turn)
    dynamic_scenario = session_attributes.get('dynamicScenario')
    
    if not dynamic_scenario:
        # First turn - retrieve from DynamoDB
        logger.info(f"[CACHE MISS] Retrieving scenario from DynamoDB for key: {interaction_key}")
        try:
            # ... parse interaction_key ...
            table = dynamodb.Table(table_name)
            response = table.get_item(Key={'PK': pk, 'SK': sk})
            if 'Item' in response:
                dynamodb_item = response['Item']
                dynamic_scenario = dynamodb_item.get('DynamicScenario')
                # Cache in session for subsequent turns
                session_attributes['dynamicScenario'] = dynamic_scenario
                logger.info(f"[CACHE] Stored scenario in session. Length: {len(dynamic_scenario)}")
            else:
                logger.warning(f"[CACHE MISS] No DynamoDB item found for key: {interaction_key}")
        except Exception as e:
            logger.error(f"[CACHE ERROR] Error retrieving scenario from DynamoDB: {e}")
    else:
        logger.info(f"[CACHE HIT] Using cached scenario from session. Length: {len(dynamic_scenario)}")
```

### Deploy
```bash
cd /Users/johndoe/Downloads/aws_org_export/lambda/LexFulfillmentHandler_code
zip -r function.zip lambda_function.py

aws lambda update-function-code \
  --function-name LexFulfillmentHandler \
  --zip-file fileb://function.zip \
  --region us-west-2
```

### Validation
Check CloudWatch Logs for cache hit/miss messages during phone calls.

---

## Task 4: Reduce Bedrock max_tokens
**Impact:** -500ms to -1s  
**Time:** 15 minutes  
**Risk:** LOW

### Problem
Bedrock is configured to generate up to 512 tokens, but most responses are 50-100 tokens. Generating unused tokens wastes time.

### Solution

**File:** `lambda/LexFulfillmentHandler_code/lambda_function.py`

**Find all occurrences of:**
```python
body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 512,  # ← CHANGE THIS
    # ...
})
```

**Replace with:**
```python
body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 150,  # Reduced from 512
    "temperature": 0.7,  # Add for consistency
    # ...
})
```

**Locations to update:**
1. `generate_dynamic_response()` function
2. `handle_general_ai_conversation()` function

**Also update GenerateDynamicScenarioHandler:**

**File:** `lambda/GenerateDynamicScenarioHandler_code/lambda_function.py`

```python
body = json.dumps({
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 200,  # Reduced from 500 (greeting needs to be short)
    "temperature": 0.8,
    # ...
})
```

### Deploy
```bash
# LexFulfillmentHandler
cd /Users/johndoe/Downloads/aws_org_export/lambda/LexFulfillmentHandler_code
zip -r function.zip lambda_function.py
aws lambda update-function-code \
  --function-name LexFulfillmentHandler \
  --zip-file fileb://function.zip \
  --region us-west-2

# GenerateDynamicScenarioHandler
cd /Users/johndoe/Downloads/aws_org_export/lambda/GenerateDynamicScenarioHandler_code
zip -r function.zip lambda_function.py
aws lambda update-function-code \
  --function-name GenerateDynamicScenarioHandler \
  --zip-file fileb://function.zip \
  --region us-west-2
```

### Validation
- Test responses are still complete and coherent
- Check CloudWatch Logs for Bedrock response times
- Verify no truncated responses

---

## Task 5: Enable X-Ray Tracing
**Impact:** 0ms (visibility only)  
**Time:** 15 minutes  
**Risk:** NONE

### Problem
No visibility into actual performance bottlenecks. X-Ray tracing is set to `PassThrough`.

### Solution

```bash
# Enable X-Ray on all Lambda functions
for FUNCTION in LexFulfillmentHandler GenerateDynamicScenarioHandler CreateLeadHandler InvokeOutboundCallHandler UpdateLeadHandler
do
  aws lambda update-function-configuration \
    --function-name $FUNCTION \
    --tracing-config Mode=Active \
    --region us-west-2
  echo "Enabled X-Ray for $FUNCTION"
done

# Enable X-Ray on Step Functions
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow \
  --tracing-configuration enabled=true \
  --region us-west-2
```

### Add X-Ray SDK to Lambda Code (Optional but Recommended)

**File:** `lambda/LexFulfillmentHandler_code/lambda_function.py`

**Add at top:**
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch all supported libraries
patch_all()
```

**Wrap critical functions:**
```python
@xray_recorder.capture('generate_dynamic_response')
def generate_dynamic_response(base_context, history, user_input):
    # ... existing code ...
    pass

@xray_recorder.capture('get_sf_connection')
def get_sf_connection():
    # ... existing code ...
    pass
```

**Add to requirements.txt:**
```
aws-xray-sdk==2.12.0
```

### Validation
```bash
# View X-Ray traces
aws xray get-trace-summaries \
  --start-time $(date -u -d '10 minutes ago' +%s) \
  --end-time $(date -u +%s) \
  --region us-west-2

# Open X-Ray console
open "https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/traces"
```

---

## Task 6: Increase GenerateDynamicScenarioHandler Memory
**Impact:** -200 to -500ms  
**Time:** 5 minutes  
**Risk:** NONE

### Problem
GenerateDynamicScenarioHandler has only 128MB memory, which allocates minimal CPU. Bedrock SDK benefits from more CPU.

### Solution

```bash
aws lambda update-function-configuration \
  --function-name GenerateDynamicScenarioHandler \
  --memory-size 512 \
  --region us-west-2
```

### Cost Impact
- Current: 128MB × 2.5s × 1000 invocations/month = $0.05
- New: 512MB × 2s × 1000 invocations/month = $0.17
- Increase: $0.12/month (negligible)

### Validation
Check CloudWatch metrics for reduced duration.

---

## Deployment Checklist

### Pre-Deployment
- [ ] Backup current Lambda code
- [ ] Document current Lex bot configuration
- [ ] Create CloudWatch dashboard for monitoring
- [ ] Notify team of deployment window

### Deployment Steps
- [ ] Task 1: Update Lex to use Lambda version 28
- [ ] Task 2: Deploy secrets caching code
- [ ] Task 3: Deploy session caching code
- [ ] Task 4: Deploy reduced max_tokens
- [ ] Task 5: Enable X-Ray tracing
- [ ] Task 6: Increase memory allocation

### Post-Deployment Validation
- [ ] Test web chat flow (5 test conversations)
- [ ] Test phone call flow (3 test calls)
- [ ] Check CloudWatch Logs for errors
- [ ] Verify X-Ray traces show improvements
- [ ] Monitor for 1 hour
- [ ] Compare before/after metrics

---

## Monitoring Dashboard

### CloudWatch Dashboard JSON
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Duration", {"stat": "Average", "label": "Avg Duration"}],
          ["...", {"stat": "p99", "label": "p99 Duration"}]
        ],
        "view": "timeSeries",
        "region": "us-west-2",
        "title": "LexFulfillmentHandler Duration",
        "period": 60
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/Lambda", "ConcurrentExecutions", {"stat": "Maximum"}]
        ],
        "view": "timeSeries",
        "region": "us-west-2",
        "title": "Concurrent Executions",
        "period": 60
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/LexFulfillmentHandler'\n| fields @timestamp, @message\n| filter @message like /CACHE/\n| stats count() by bin(5m)",
        "region": "us-west-2",
        "title": "Cache Hit Rate"
      }
    }
  ]
}
```

---

## Rollback Plan

If issues occur:

```bash
# Rollback Lex to previous Lambda version
aws lexv2-models update-bot-alias \
  --bot-id <BOT_ID> \
  --bot-alias-id <ALIAS_ID> \
  --bot-alias-locale-settings '{
    "en_US": {
      "codeHookSpecification": {
        "lambdaCodeHook": {
          "lambdaARN": "arn:aws:lambda:us-west-2:<AWS_ACCOUNT_ID>:function:LexFulfillmentHandler:$LATEST"
        }
      }
    }
  }' \
  --region us-west-2

# Rollback Lambda code
aws lambda update-function-code \
  --function-name LexFulfillmentHandler \
  --s3-bucket <BACKUP_BUCKET> \
  --s3-key backups/LexFulfillmentHandler-backup.zip \
  --region us-west-2
```

---

## Success Metrics

### Before Phase 1
- Average response time: 9+ seconds
- p99 response time: 12+ seconds
- Cold start rate: 30%
- Secrets Manager calls: 100% of invocations

### After Phase 1 (Target)
- Average response time: 3-5 seconds ✅
- p99 response time: 6-7 seconds ✅
- Cold start rate: 0% ✅
- Secrets Manager calls: <5% of invocations ✅

### Measurement
```bash
# Get average duration over last hour
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=LexFulfillmentHandler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average,Maximum \
  --region us-west-2
```

---

## Next Steps

After Phase 1 is complete and validated:
1. Monitor for 24-48 hours
2. Collect performance metrics
3. Proceed to Phase 2 (response caching, Haiku model)
4. Document lessons learned

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-29  
**Estimated Completion Time:** 3-4 hours  
**Risk Level:** LOW  
**Expected Impact:** -4 to -6 seconds
