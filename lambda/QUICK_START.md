# Quick Start - Atlas Engine Profiling

## 🚀 Deploy in 3 Steps

### 1. Navigate to Directory
```bash
cd /Users/johndoe/Downloads/aws_org_export/lambda
```

### 2. Run Deployment Script
```bash
chmod +x deploy_dev_alias.sh
./deploy_dev_alias.sh
```

### 3. Enable Step Function Tracing
```bash
aws stepfunctions update-state-machine \
  --state-machine-arn arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow \
  --tracing-configuration enabled=true \
  --region us-west-2
```

---

## 🔍 Find the Bottleneck

### View X-Ray Service Map
https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/service-map

### View X-Ray Traces (Sort by Duration)
https://us-west-2.console.aws.amazon.com/xray/home?region=us-west-2#/traces

### Query CloudWatch Logs
```sql
fields @timestamp, function_name, metric, value_sec
| filter event_type = "TIMING"
| sort value_sec desc
| limit 20
```

---

## 📊 Key Metrics to Watch

| Function | Critical Metrics |
|----------|-----------------|
| **LFH** | BedrockCallDuration, SalesforceAuthDuration |
| **GDSH** | BedrockCallDuration |
| **IOCH** | ConnectCallDuration, DynamoDBPutDuration |
| **ULH** | SalesforceUpdateDuration |

---

## 🧪 Test Dev Alias

```bash
# Test a function
aws lambda invoke \
  --function-name GenerateDynamicScenarioHandler:Dev \
  --payload '{"firstName":"Test","lastName":"User","chat_transcript":"test"}' \
  --region us-west-2 \
  response.json

# View logs
aws logs tail /aws/lambda/GenerateDynamicScenarioHandler --follow --region us-west-2
```

---

## 🎯 Most Likely Bottlenecks

1. **Bedrock Model Invocation** (8-10s) - Check `BedrockCallDuration`
2. **Connect Call Initiation** (5-8s) - Check `ConnectCallDuration`
3. **Salesforce API** (2-5s) - Check `SalesforceUpdateDuration`

---

## 📚 Full Documentation

- **Deployment Commands:** `DEPLOYMENT_COMMANDS.md`
- **Implementation Details:** `PROFILING_IMPLEMENTATION_SUMMARY.md`
- **IAM Policy:** `iam_xray_policy.json`

---

## ✅ Verify Deployment

```bash
# Check Dev alias exists
aws lambda get-alias --function-name LexFulfillmentHandler --name Dev --region us-west-2

# Check X-Ray is enabled
aws lambda get-function-configuration \
  --function-name LexFulfillmentHandler \
  --region us-west-2 \
  --query 'TracingConfig'
```

---

## 🔄 Rollback if Needed

```bash
aws lambda update-alias \
  --function-name <FUNCTION_NAME> \
  --name Dev \
  --function-version <PREVIOUS_VERSION> \
  --region us-west-2
```

**Your PROD alias is never touched!**
