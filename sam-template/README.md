# Atlas Engine - SAM Deployment Guide

AI-Powered Sales Acceleration Platform built with AWS Serverless

## 🏗️ Architecture

- **8 Lambda Functions** - Python 3.13
- **2 Lambda Layers** - Shared dependencies
- **1 Step Functions** - Workflow orchestration
- **2 DynamoDB Tables** - Data storage
- **Amazon Lex** - Conversational AI
- **Amazon Connect** - Contact center
- **Amazon Bedrock** - AI generation (Claude 3.5 Sonnet)

## 📋 Prerequisites

### 1. Install AWS SAM CLI

```bash
# macOS
brew install aws-sam-cli

# Linux
pip install aws-sam-cli

# Verify installation
sam --version
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-west-2
```

### 3. Create Salesforce Secret

```bash
# Create secret JSON file
cat > salesforce-creds.json << EOF
{
  "username": "your-sf-username@example.com",
  "client_id": "your-connected-app-client-id",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
}
EOF

# Create secret in AWS
aws secretsmanager create-secret \
  --name AtlasEngine/SalesforceCreds \
  --secret-string file://salesforce-creds.json \
  --region us-west-2

# Clean up
rm salesforce-creds.json
```

### 4. Enable Bedrock Model Access

```bash
# Go to AWS Console > Bedrock > Model access
# Request access to: Claude 3.5 Sonnet
```

## 🚀 Quick Start

### Deploy to Dev Environment

```bash
# Navigate to SAM template directory
cd sam-template

# Build the application
sam build

# Deploy with guided prompts
sam deploy --guided

# Or deploy directly
sam deploy --config-env dev
```

### Deploy to Production

```bash
sam deploy --config-env prod \
  --parameter-overrides \
    Environment=prod \
    ConnectInstanceId=<your-connect-instance-id> \
    SourcePhoneNumber=+18664212740
```

## 📦 Project Structure

```
atlas-engine/
├── sam-template/
│   ├── template.yaml           # Main SAM template
│   ├── samconfig.toml          # Deployment configuration
│   └── README.md               # This file
├── lambda/
│   ├── CreateLeadHandler_code/
│   ├── GenerateDynamicScenarioHandler_code/
│   ├── InvokeOutboundCallHandler_code/
│   ├── LexFulfillmentHandler_code/
│   └── UpdateLeadHandler_code/
├── layers/
│   ├── python-libraries/
│   └── salesforce-libraries/
└── stepfunctions/
    └── workflow-definition.asl.json
```

## ⚙️ Configuration Parameters

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `Environment` | Deployment environment | dev, staging, prod |
| `ProjectName` | Project name prefix | AtlasEngine |

### Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `SalesforceSecretName` | Secrets Manager secret name | AtlasEngine/SalesforceCreds |
| `BedrockModelId` | Bedrock model ID | anthropic.claude-3-5-sonnet-20240620-v1:0 |
| `ConnectInstanceId` | Amazon Connect instance ID | (empty) |
| `SourcePhoneNumber` | Outbound call source number | (empty) |

## 🔧 Development Workflow

### Local Testing

```bash
# Start API locally
sam local start-api

# Invoke function locally
sam local invoke CreateLeadHandler -e events/test-event.json

# Generate sample event
sam local generate-event apigateway aws-proxy > events/test-event.json
```

### Validate Template

```bash
sam validate --lint
```

### Build Layers

```bash
# Build Python libraries layer
cd layers/python-libraries
pip install -r requirements.txt -t python/
cd ../..

# Build Salesforce libraries layer
cd layers/salesforce-libraries
pip install simple-salesforce -t python/
cd ../..
```

### Sync Changes (Fast Deployment)

```bash
# Watch for changes and auto-deploy
sam sync --watch --stack-name atlas-engine-dev
```

## 📊 Deployment Commands

### Full Deployment

```bash
# Build
sam build --parallel

# Package (optional - SAM does this automatically)
sam package --output-template-file packaged.yaml

# Deploy
sam deploy \
  --template-file template.yaml \
  --stack-name atlas-engine-dev \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=dev \
    ProjectName=AtlasEngine
```

### Update Single Function

```bash
# Build and deploy specific function
sam build CreateLeadHandler
sam deploy --no-confirm-changeset
```

### Delete Stack

```bash
sam delete --stack-name atlas-engine-dev
```

## 🔍 Monitoring & Debugging

### View Logs

```bash
# Tail logs for a function
sam logs -n CreateLeadHandler --stack-name atlas-engine-dev --tail

# View logs for specific time range
sam logs -n CreateLeadHandler --stack-name atlas-engine-dev \
  --start-time '10min ago' --end-time '5min ago'
```

### View Stack Resources

```bash
aws cloudformation describe-stack-resources \
  --stack-name atlas-engine-dev
```

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name atlas-engine-dev \
  --query 'Stacks[0].Outputs'
```

## 🎯 Post-Deployment Setup

### 1. Configure Amazon Lex Bot

```bash
# Get Lambda ARN from outputs
LEX_HANDLER_ARN=$(aws cloudformation describe-stacks \
  --stack-name atlas-engine-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`LexFulfillmentHandlerArn`].OutputValue' \
  --output text)

# Create Lex bot (manual or via AWS CLI)
# Set fulfillment Lambda to: $LEX_HANDLER_ARN
```

### 2. Configure Amazon Connect

```bash
# Manual steps required:
# 1. Create Connect instance in AWS Console
# 2. Import contact flows from connect/contact_flows.json
# 3. Claim phone numbers
# 4. Update stack with ConnectInstanceId parameter
```

### 3. Test the Workflow

```bash
# Invoke Step Functions
aws stepfunctions start-execution \
  --state-machine-arn $(aws cloudformation describe-stacks \
    --stack-name atlas-engine-dev \
    --query 'Stacks[0].Outputs[?OutputKey==`WorkflowArn`].OutputValue' \
    --output text) \
  --input '{"firstName":"Test","lastName":"User","phone":"+15555551234"}'
```

## 🔐 Security Best Practices

1. **Secrets Management**
   - Never commit secrets to Git
   - Use AWS Secrets Manager for credentials
   - Rotate secrets regularly

2. **IAM Permissions**
   - Use least privilege policies
   - Review generated IAM roles
   - Enable CloudTrail logging

3. **Network Security**
   - Consider VPC deployment for production
   - Use security groups appropriately
   - Enable encryption at rest and in transit

## 🐛 Troubleshooting

### Build Failures

```bash
# Clean build artifacts
sam build --use-container --debug

# Check Python dependencies
pip install -r lambda/CreateLeadHandler_code/requirements.txt
```

### Deployment Failures

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name atlas-engine-dev \
  --max-items 20

# Validate template
sam validate --lint
```

### Lambda Errors

```bash
# Check function logs
sam logs -n CreateLeadHandler --stack-name atlas-engine-dev --tail

# Test function locally
sam local invoke CreateLeadHandler -e events/test-event.json
```

## 📚 Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Connect Documentation](https://docs.aws.amazon.com/connect/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `sam local`
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

For issues and questions:
- GitHub Issues: [your-repo/issues]
- Documentation: [your-docs-url]
- Email: support@example.com
