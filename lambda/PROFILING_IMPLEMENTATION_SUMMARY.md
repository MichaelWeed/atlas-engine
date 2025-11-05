# Atlas Engine Profiling Implementation Summary

## Overview

This implementation adds comprehensive X-Ray tracing and structured CloudWatch logging to identify the 9-10 second latency bottleneck in your serverless application.

---

## What Was Implemented

### 1. X-Ray Instrumentation

All four Lambda functions now include:

- **aws-xray-sdk** integration with `patch_all()` to automatically instrument boto3 clients
- **Custom subsegments** around critical external calls:
  - **LexFulfillmentHandler:** Bedrock.InvokeModel, SecretsManager.GetSecret, Salesforce.OAuth
  - **GenerateDynamicScenarioHandler:** Bedrock.InvokeModel
  - **InvokeOutboundCallHandler:** DynamoDB.PutItem, Connect.StartOutboundCall, DynamoDB.UpdateItem
  - **UpdateLeadHandler:** Salesforce.Authenticate, Salesforce.UpdateLead

### 2. Structured CloudWatch Logging

Each function logs in JSON format:

```json
// Function start
{"level": "INFO", "event_type": "START", "function_name": "GDSH", "message": "Function started"}

// Individual operation timing
{"level": "INFO", "event_type": "TIMING", "function_name": "GDSH", "metric": "BedrockCallDuration", "value_sec": 2.847}

// Function end
{"level": "INFO", "event_type": "END", "function_name": "GDSH", "message": "Function completed", "total_function_duration": 3.125}
```

### 3. Key Metrics Tracked

| Function | Metrics |
|----------|---------|
| **LexFulfillmentHandler (LFH)** | BedrockCallDuration, SecretsManagerDuration, SalesforceAuthDuration, total_function_duration |
| **GenerateDynamicScenarioHandler (GDSH)** | BedrockCallDuration, total_function_duration |
| **InvokeOutboundCallHandler (IOCH)** | DynamoDBPutDuration, ConnectCallDuration, DynamoDBUpdateDuration, total_function_duration |
| **UpdateLeadHandler (ULH)** | SalesforceAuthDuration, SalesforceUpdateDuration, total_function_duration |

---

## Files Created

### Updated Lambda Functions (with X-Ray)
- `LexFulfillmentHandler_code/lambda_function_dev.py`
- `GenerateDynamicScenarioHandler_code/lambda_function_dev.py`
- `InvokeOutboundCallHandler_code/lambda_function_dev.py`
- `UpdateLeadHandler_code/lambda_function_dev.py`

### Deployment Files
- `requirements_xray.txt` - X-Ray SDK dependency
- `iam_xray_policy.json` - IAM policy for X-Ray permissions
- `deploy_dev_alias.sh` - Automated deployment script
- `DEPLOYMENT_COMMANDS.md` - Comprehensive CLI commands guide
- `PROFILING_IMPLEMENTATION_SUMMARY.md` - This file

---

## Deployment Options

### Option 1: Automated (Recommended)

```bash
cd /Users/johndoe/Downloads/aws_org_export/lambda
chmod +x deploy_dev_alias.sh
./deploy_dev_alias.sh
```

### Option 2: Manual

Follow the step-by-step commands in `DEPLOYMENT_COMMANDS.md`

---

## What Happens During Deployment

1. **IAM Permissions:** Adds X-Ray permissions to all Lambda execution roles
2. **Code Update:** Deploys X-Ray instrumented code to each function
3. **Version Publishing:** Creates new Lambda versions
4. **Alias Creation:** Creates/updates "Dev" alias pointing to new versions
5. **Tracing Enabled:** Sets `TracingConfig.Mode=Active` on all functions
6. **Step Function:** Enables X-Ray tracing on AtlasEngineWorkflow

**Your "PROD" alias remains unchanged** - it continues to use the original code without X-Ray.

---

## How to Find the Bottleneck

### Method 1: X-Ray Service Map (Visual)

1. Go to: https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/service-map
2. Trigger a workflow execution using the Dev alias
3. Look for:
   - Red/orange nodes (errors or high latency)
   - Thick lines between services (high traffic)
   - Response time distribution on each node

### Method 2: X-Ray Traces (Detailed)

1. Go to: https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/traces
2. Filter by time range when you ran the test
3. Sort by "Duration" (descending)
4. Click on the longest trace
5. Examine the timeline:
   - Each subsegment shows exact duration
   - Look for subsegments taking 9-10 seconds
   - Common culprits:
     - Bedrock model invocation (cold start or large prompts)
     - Connect outbound call initiation
     - Salesforce API calls
     - DynamoDB operations

### Method 3: CloudWatch Logs Insights

```sql
-- Find slowest operations across all functions
fields @timestamp, function_name, metric, value_sec
| filter event_type = "TIMING"
| sort value_sec desc
| limit 20

-- Find slowest total function durations
fields @timestamp, function_name, total_function_duration
| filter event_type = "END"
| sort total_function_duration desc
| limit 20

-- Analyze specific metric (e.g., Bedrock calls)
fields @timestamp, function_name, value_sec
| filter metric = "BedrockCallDuration"
| stats avg(value_sec), max(value_sec), min(value_sec) by function_name
```

### Method 4: Step Functions Execution History

1. Go to Step Functions console
2. Find an execution using Dev functions
3. Look at the "Execution event history"
4. Check the duration of each state
5. The state with 9-10 seconds is your bottleneck

---

## Common Bottleneck Scenarios

### Scenario 1: Bedrock Model Invocation (Most Likely)

**Symptoms:**
- `BedrockCallDuration` shows 8-10 seconds
- X-Ray shows long duration in Bedrock subsegment

**Causes:**
- Large prompt size
- Model cold start
- Model selection (Sonnet vs Haiku)
- Token generation limits

**Solutions:**
- Use faster model (Haiku instead of Sonnet)
- Reduce prompt size
- Implement prompt caching
- Use provisioned throughput

### Scenario 2: Amazon Connect Call Initiation

**Symptoms:**
- `ConnectCallDuration` shows 8-10 seconds
- X-Ray shows long duration in Connect.StartOutboundCall

**Causes:**
- Contact flow complexity
- Queue wait time
- Network latency to phone carrier

**Solutions:**
- Simplify contact flow
- Pre-warm connections
- Use callback pattern instead of synchronous wait

### Scenario 3: Salesforce API Calls

**Symptoms:**
- `SalesforceAuthDuration` or `SalesforceUpdateDuration` shows high latency
- X-Ray shows long duration in Salesforce subsegments

**Causes:**
- JWT token generation
- Salesforce API rate limits
- Network latency to Salesforce

**Solutions:**
- Cache Salesforce connections (already implemented)
- Use bulk API for multiple updates
- Implement retry with exponential backoff

### Scenario 4: Step Function Wait States

**Symptoms:**
- Individual Lambda functions are fast
- Total workflow takes 9-10 seconds
- Step Function execution history shows long gaps

**Causes:**
- Explicit wait states in workflow
- Task token callback pattern waiting for external event

**Solutions:**
- Review Step Function definition for wait states
- Optimize callback pattern
- Use parallel states where possible

---

## Testing the Dev Alias

### Test Individual Functions

```bash
# Test LexFulfillmentHandler:Dev
aws lambda invoke \
  --function-name LexFulfillmentHandler:Dev \
  --payload '{"sessionState":{"intent":{"name":"GreetingIntent"}},"inputTranscript":"hello"}' \
  --region us-west-2 \
  response.json

# Test GenerateDynamicScenarioHandler:Dev
aws lambda invoke \
  --function-name GenerateDynamicScenarioHandler:Dev \
  --payload '{"firstName":"John","lastName":"Doe","chat_transcript":"User asked about pricing"}' \
  --region us-west-2 \
  response.json
```

### Test Full Workflow

1. Update Step Function to use Dev aliases (or create AtlasEngineWorkflow-Dev)
2. Trigger workflow through your application
3. Monitor X-Ray traces in real-time
4. Check CloudWatch Logs for structured timing data

---

## Interpreting Results

### X-Ray Trace Timeline Example

```
AtlasEngineWorkflow (12.5s total)
├─ LexFulfillmentHandler:Dev (0.8s)
│  └─ Bedrock.InvokeModel (0.6s)
├─ GenerateDynamicScenarioHandler:Dev (9.2s) ← BOTTLENECK
│  └─ Bedrock.InvokeModel (9.0s) ← ROOT CAUSE
├─ InvokeOutboundCallHandler:Dev (1.5s)
│  ├─ DynamoDB.PutItem (0.2s)
│  ├─ Connect.StartOutboundCall (1.0s)
│  └─ DynamoDB.UpdateItem (0.1s)
└─ UpdateLeadHandler:Dev (0.5s)
   └─ Salesforce.UpdateLead (0.3s)
```

In this example, the bottleneck is clearly the Bedrock call in GenerateDynamicScenarioHandler taking 9 seconds.

### CloudWatch Logs Example

```json
{"level": "INFO", "event_type": "TIMING", "function_name": "GDSH", "metric": "BedrockCallDuration", "value_sec": 9.234}
```

This confirms the Bedrock invocation is the issue.

---

## Next Steps After Identifying Bottleneck

1. **Document the finding** - Note which service/operation is slow
2. **Analyze the root cause** - Why is it slow? (cold start, large payload, etc.)
3. **Implement optimization** - Apply appropriate solution from scenarios above
4. **Re-test with Dev alias** - Verify improvement
5. **Promote to PROD** - Update PROD alias once satisfied

---

## Rollback Plan

If Dev alias has issues:

```bash
# List versions
aws lambda list-versions-by-function \
  --function-name LexFulfillmentHandler \
  --region us-west-2

# Rollback Dev alias to previous version
aws lambda update-alias \
  --function-name LexFulfillmentHandler \
  --name Dev \
  --function-version <PREVIOUS_VERSION> \
  --region us-west-2
```

Your PROD alias is never affected.

---

## Cost Considerations

- **X-Ray:** First 100,000 traces/month free, then $5 per 1M traces
- **CloudWatch Logs:** $0.50 per GB ingested
- **Lambda:** No additional cost for X-Ray instrumentation

For profiling/debugging, costs should be minimal (< $5/month).

---

## Support & Troubleshooting

### X-Ray Not Showing Traces

1. Verify IAM permissions: `xray:PutTraceSegments`, `xray:PutTelemetryRecords`
2. Check Lambda configuration: `TracingConfig.Mode=Active`
3. Ensure X-Ray SDK is installed: `pip list | grep xray`
4. Check CloudWatch Logs for X-Ray errors

### Structured Logs Not Appearing

1. Verify function is using `lambda_function_dev.py`
2. Check CloudWatch Log Group exists
3. Use CloudWatch Logs Insights to query JSON logs
4. Ensure `print(json.dumps(...))` statements are present

### Dev Alias Not Working

1. Verify alias exists: `aws lambda get-alias --function-name <NAME> --name Dev`
2. Check alias points to correct version
3. Ensure Step Function uses `:Dev` suffix in ARNs
4. Test alias directly with `aws lambda invoke`

---

## Summary

You now have:
- ✅ X-Ray tracing on all 4 Lambda functions
- ✅ Structured timing logs in CloudWatch
- ✅ Dev alias for safe testing
- ✅ PROD alias unchanged
- ✅ Deployment automation
- ✅ Comprehensive monitoring

**Run the deployment script and trigger a test execution to identify your 9-10 second bottleneck!**
