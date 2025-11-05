# Atlas Engine Deployment Guide

Complete guide to deploy Atlas Engine in under 30 minutes.

## Prerequisites (5 minutes)

### Required Tools
```bash
# AWS CLI
aws --version  # Requires 2.x

# SAM CLI
sam --version  # Requires 1.100+

# Python
python3 --version  # Requires 3.13+
```

### AWS Account Requirements
- AWS account with admin access
- Bedrock model access enabled (us-west-2 recommended)
- Salesforce Connected App configured for JWT authentication

### Cost Estimate
**Monthly costs for dev environment (low usage):**
- Lambda: $5-10 (1M requests)
- DynamoDB: $2-5 (PAY_PER_REQUEST)
- Step Functions: $1-3 (1K executions)
- Bedrock: $10-50 (varies by usage)
- **Total: ~$20-70/month**

**Production environment (moderate usage):**
- Lambda: $50-100
- DynamoDB: $20-50
- Step Functions: $10-20
- Bedrock: $100-500
- Amazon Connect: $50-200
- **Total: ~$230-870/month**

## Quick Start (15 minutes)

### Option 1: Automated Script (Recommended)
```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh

# Follow prompts for:
# - Environment (dev/staging/prod)
# - AWS Region
# - Salesforce secret name
```

### Option 2: Manual Deployment
```bash
# 1. Build Lambda layers
mkdir -p layers/python-libraries/python layers/salesforce-libraries/python
pip install requests phonenumbers wrapt -t layers/python-libraries/python/
pip install simple-salesforce PyJWT cryptography -t layers/salesforce-libraries/python/

# 2. Create Salesforce secret
aws secretsmanager create-secret \
    --name AtlasEngine/SalesforceCreds \
    --secret-string '{
        "username":"your-sf-user@company.com",
        "client_id":"YOUR_CONNECTED_APP_CLIENT_ID",
        "private_key":"-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----"
    }'

# 3. Build and deploy
sam build --parallel
sam deploy --guided
```

### Option 3: One-Click CloudFormation
```bash
# Deploy infrastructure only
aws cloudformation create-stack \
    --stack-name AtlasEngine-Infrastructure \
    --template-body file://quick-start.yaml \
    --parameters \
        ParameterKey=SalesforceUsername,ParameterValue=user@company.com \
        ParameterKey=SalesforceClientId,ParameterValue=YOUR_CLIENT_ID \
        ParameterKey=SalesforcePrivateKey,ParameterValue=BASE64_ENCODED_KEY \
    --capabilities CAPABILITY_IAM

# Then deploy application
sam build && sam deploy
```

## Post-Deployment Configuration (10 minutes)

### 1. Enable Bedrock Access
```bash
# Request model access in AWS Console
# Navigate to: Bedrock > Model access > Manage model access
# Enable: Claude 3.5 Sonnet
```

### 2. Configure Amazon Lex Bot
```bash
# Get Lambda ARN
LEX_HANDLER=$(aws cloudformation describe-stacks \
    --stack-name AtlasEngine-dev \
    --query "Stacks[0].Outputs[?OutputKey=='LexFulfillmentHandlerArn'].OutputValue" \
    --output text)

echo "Configure Lex bot with fulfillment Lambda: $LEX_HANDLER"
```

**Manual steps in Lex Console:**
1. Create new bot or use existing
2. Add fulfillment Lambda: Use ARN from above
3. Configure intents and slots
4. Build and test bot

### 3. Set Up Amazon Connect (Optional)
1. Create Connect instance in AWS Console
2. Claim phone number
3. Update stack parameters:
```bash
sam deploy \
    --parameter-overrides \
        ConnectInstanceId=YOUR_INSTANCE_ID \
        SourcePhoneNumber=+1234567890
```

### 4. Test Deployment
```bash
# Test Step Functions workflow
aws stepfunctions start-execution \
    --state-machine-arn $(aws cloudformation describe-stacks \
        --stack-name AtlasEngine-dev \
        --query "Stacks[0].Outputs[?OutputKey=='WorkflowArn'].OutputValue" \
        --output text) \
    --input '{
        "firstName": "Test",
        "lastName": "User",
        "phone": "+15555551234"
    }'
```

## Customization Guide

### Multi-Environment Deployment
```bash
# Deploy to staging
sam deploy --config-env staging

# Deploy to production
sam deploy --config-env prod
```

### Custom Bedrock Models
Edit `sam-template/template.yaml`:
```yaml
Parameters:
  BedrockModelId:
    Default: anthropic.claude-3-opus-20240229-v1:0  # Change model
```

### Custom DynamoDB Capacity
For high-traffic production:
```yaml
InteractionsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    BillingMode: PROVISIONED
    ProvisionedThroughput:
      ReadCapacityUnits: 100
      WriteCapacityUnits: 100
```

### Add Custom Lambda Functions
```yaml
MyCustomHandler:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub ${ProjectName}-MyCustomHandler-${Environment}
    CodeUri: ../lambda/MyCustomHandler_code/
    Handler: lambda_function.lambda_handler
    Policies:
      - DynamoDBCrudPolicy:
          TableName: !Ref InteractionsTable
```

## Troubleshooting

### Issue: SAM build fails
```bash
# Clear cache and rebuild
rm -rf .aws-sam
sam build --use-container
```

### Issue: Lambda timeout
```bash
# Increase timeout in template.yaml
Timeout: 300  # 5 minutes
MemorySize: 1024  # More memory = faster execution
```

### Issue: Bedrock access denied
```bash
# Check model access
aws bedrock list-foundation-models --region us-west-2

# Request access in Console if needed
```

### Issue: Salesforce authentication fails
```bash
# Verify secret format
aws secretsmanager get-secret-value \
    --secret-id AtlasEngine/SalesforceCreds \
    --query SecretString \
    --output text | jq .

# Test JWT authentication manually
```

### Issue: Step Functions execution fails
```bash
# View execution logs
aws stepfunctions describe-execution \
    --execution-arn YOUR_EXECUTION_ARN

# Check CloudWatch logs
aws logs tail /aws/vendedlogs/states/AtlasEngine-Workflow-dev --follow
```

### Issue: High costs
```bash
# Check resource usage
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=AtlasEngine-LexFulfillmentHandler-dev \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-31T23:59:59Z \
    --period 86400 \
    --statistics Sum

# Reduce costs:
# 1. Lower Lambda memory
# 2. Use DynamoDB on-demand pricing
# 3. Set CloudWatch log retention to 7 days
# 4. Use Bedrock batch inference
```

## Monitoring

### CloudWatch Dashboards
```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
    --dashboard-name AtlasEngine-dev \
    --dashboard-body file://monitoring/dashboard.json
```

### Alarms
```bash
# Lambda errors
aws cloudwatch put-metric-alarm \
    --alarm-name AtlasEngine-LambdaErrors \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold

# DynamoDB throttles
aws cloudwatch put-metric-alarm \
    --alarm-name AtlasEngine-DynamoDBThrottles \
    --metric-name UserErrors \
    --namespace AWS/DynamoDB \
    --statistic Sum \
    --period 300 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold
```

## Cleanup

### Remove All Resources
```bash
# Automated cleanup
chmod +x cleanup.sh
./cleanup.sh dev

# Manual cleanup
aws cloudformation delete-stack --stack-name AtlasEngine-dev
aws cloudformation wait stack-delete-complete --stack-name AtlasEngine-dev
```

### Partial Cleanup (Keep Data)
```bash
# Delete compute resources only
aws cloudformation delete-stack --stack-name AtlasEngine-dev --retain-resources InteractionsTable,TaskTokensTable
```

## Security Best Practices

1. **Secrets Management**: Never commit credentials to Git
2. **IAM Policies**: Use least-privilege access
3. **Encryption**: Enable encryption at rest for DynamoDB
4. **VPC**: Deploy Lambda in VPC for production
5. **Logging**: Enable CloudTrail for audit logs
6. **Scanning**: Run security scans before deployment

## Support

- **Documentation**: See README.md and DIRECTORY_STRUCTURE.md
- **Issues**: Check SECURITY_AUDIT_REPORT.md for known issues
- **AWS Support**: https://console.aws.amazon.com/support/
- **Bedrock Docs**: https://docs.aws.amazon.com/bedrock/

## Next Steps

1. Review DEPLOYMENT_ARCHITECTURE.md for system design
2. Customize Lambda functions for your use case
3. Set up CI/CD pipeline (see ci-cd/ folder)
4. Configure monitoring and alerting
5. Plan for disaster recovery
