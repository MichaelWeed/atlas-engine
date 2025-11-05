# Atlas Engine - Quick Start Guide

Deploy Atlas Engine in **under 30 minutes**.

## Prerequisites Checklist

- [ ] AWS account with admin access
- [ ] AWS CLI installed and configured
- [ ] SAM CLI installed (v1.100+)
- [ ] Python 3.13+ installed
- [ ] Salesforce Connected App credentials

## 5-Minute Setup

### Step 1: Validate Environment (2 min)
```bash
chmod +x validate.sh
./validate.sh
```

### Step 2: Configure Salesforce (1 min)
Create `salesforce-creds.json`:
```json
{
  "username": "your-user@company.com",
  "client_id": "YOUR_CONNECTED_APP_CLIENT_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----"
}
```

### Step 3: Deploy (2 min)
```bash
chmod +x deploy.sh
./deploy.sh
```

**That's it!** The script handles everything:
- ✓ Builds Lambda layers
- ✓ Creates Salesforce secret
- ✓ Deploys infrastructure
- ✓ Configures permissions

## What Gets Deployed

| Resource | Count | Purpose |
|----------|-------|---------|
| Lambda Functions | 8 | Core business logic |
| Lambda Layers | 2 | Shared dependencies |
| DynamoDB Tables | 2 | Data storage |
| Step Functions | 1 | Workflow orchestration |
| SNS Topic | 1 | Notifications |
| IAM Roles | 8 | Permissions |
| CloudWatch Logs | 9 | Monitoring |

## Post-Deployment (5 min)

### 1. Get Lambda ARN
```bash
aws cloudformation describe-stacks \
    --stack-name AtlasEngine-dev \
    --query "Stacks[0].Outputs[?OutputKey=='LexFulfillmentHandlerArn'].OutputValue" \
    --output text
```

### 2. Configure Lex Bot
1. Go to Amazon Lex Console
2. Create or select bot
3. Add fulfillment Lambda (ARN from above)
4. Build and test

### 3. Test Workflow
```bash
aws stepfunctions start-execution \
    --state-machine-arn $(aws cloudformation describe-stacks \
        --stack-name AtlasEngine-dev \
        --query "Stacks[0].Outputs[?OutputKey=='WorkflowArn'].OutputValue" \
        --output text) \
    --input '{
        "firstName": "John",
        "lastName": "Doe",
        "phone": "+15555551234"
    }'
```

## Customization

### Change Environment
```bash
# Deploy to staging
ENVIRONMENT=staging ./deploy.sh

# Deploy to production
ENVIRONMENT=prod ./deploy.sh
```

### Change Region
```bash
REGION=us-east-1 ./deploy.sh
```

### Use Different Bedrock Model
Edit `sam-template/template.yaml`:
```yaml
BedrockModelId:
  Default: anthropic.claude-3-opus-20240229-v1:0
```

## Troubleshooting

### Deployment fails
```bash
# Check logs
sam logs --stack-name AtlasEngine-dev --tail

# Retry deployment
sam deploy --no-confirm-changeset
```

### Lambda timeout
```bash
# Increase timeout in template.yaml
Timeout: 300
MemorySize: 1024
```

### Bedrock access denied
```bash
# Enable model access in Console
# Bedrock > Model access > Manage model access
```

## Cleanup

```bash
chmod +x cleanup.sh
./cleanup.sh dev
```

## Cost Estimate

**Development:** ~$24/month
**Production:** ~$1,138/month (50K conversations)

See [COST_ESTIMATION.md](COST_ESTIMATION.md) for details.

## Next Steps

1. ✓ Deployed successfully
2. [ ] Configure Amazon Connect (optional)
3. [ ] Set up monitoring dashboards
4. [ ] Enable CI/CD pipeline
5. [ ] Customize for your use case

## Support

- **Full Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Architecture**: [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
- **Costs**: [COST_ESTIMATION.md](COST_ESTIMATION.md)
- **Security**: [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md)

## One-Click Alternative

Use CloudFormation Quick Start:
```bash
aws cloudformation create-stack \
    --stack-name AtlasEngine-Infrastructure \
    --template-body file://quick-start.yaml \
    --parameters file://parameters.json \
    --capabilities CAPABILITY_IAM
```

See [quick-start.yaml](quick-start.yaml) for details.
