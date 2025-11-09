# Atlas Engine - AI-Powered Sales Acceleration Platform

![Atlas Engine](flag.jpg)

Deploy an AI-powered sales automation system to AWS in 30 minutes.

## 🚀 One-Click Deployment

**Deploy directly to your AWS account:**

[![Deploy to AWS](https://img.shields.io/badge/Deploy%20to-AWS-orange?style=for-the-badge&logo=amazon-aws)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://atlas-engine.s3.us-west-2.amazonaws.com/atlas-engine/template.yaml&stackName=AtlasEngine)

*Note: This button uses the manually uploaded template. Lambda code must be deployed separately using `./deploy.sh`*

# About Atlas Engine

What if you could engage a new web lead not in hours, but in seconds?

The Atlas Engine is a serverless, AI-powered B2B sales accelerator built on AWS. It's a high-impact, interactive demo that solves the "immediate contact" problem by turning a simple web chat into a real-time, AI-driven, outbound phone call. It's a "silent salesperson" that demonstrates a sophisticated, event-driven architecture in real-time.

The Journey (Web Chat to Phone Call in < 60 Seconds) goes as follows:
1. A user interacts with an Amazon Lex chatbot on the web.

2. Their info triggers an AWS Step Functions workflow, which creates a lead in Salesforce.

3. Amazon Bedrock (Claude 3.5 Sonnet) dynamically generates a contextual greeting based on the user's chat.

4. Amazon Connect is triggered, placing an immediate outbound, AI-powered voice call to the user.

5. The user talks to the AI-driven IVR, which can answer questions live (using Bedrock) or handle requests.

6. After the call, Amazon Transcribe and Bedrock create a summary, and the Step Function resumes to post it to the Salesforce lead record.

### Prerequisites for One-Click Deploy

Before clicking the deploy button, ensure you have:

1. **AWS Account** with admin permissions
2. **Bedrock Model Access** - Enable Claude 3.5 Sonnet in [Bedrock Console](https://console.aws.amazon.com/bedrock/)
3. **Salesforce Connected App** - Create credentials following [SALESFORCE_INTEGRATION.md](SALESFORCE_INTEGRATION.md)
4. **AWS Secrets Manager Secret** - Store Salesforce credentials:
   ```bash
   aws secretsmanager create-secret \
       --name AtlasEngine/SalesforceCreds \
       --secret-string '{"username":"your-email@company.com","client_id":"YOUR_CLIENT_ID","private_key":"-----BEGIN PRIVATE KEY-----\nYOUR_KEY\n-----END PRIVATE KEY-----"}'
   ```

### Expected Costs

| Environment | Monthly Cost | Use Case |
|-------------|--------------|----------|
| Development | **~$24/month** | Testing, 1K conversations |
| Staging | **~$214/month** | QA, 10K conversations |
| Production | **~$1,138/month** | Live, 50K conversations |

See [COST_ESTIMATION.md](COST_ESTIMATION.md) for detailed breakdown and optimization strategies.

### Post-Deployment Steps

After CloudFormation completes:

1. **Configure Amazon Lex Bot**
   - Go to [Amazon Lex Console](https://console.aws.amazon.com/lexv2/)
   - Create a new bot named "AtlasEngineBot"
   - Add the Lambda fulfillment ARN from CloudFormation Outputs
   - Build and publish the bot

2. **Optional: Set Up Amazon Connect** (for voice calls)
   - Go to [Amazon Connect Console](https://console.aws.amazon.com/connect/)
   - Create or use existing instance
   - Update stack parameters with ConnectInstanceId and SourcePhoneNumber
   - Configure contact flow to use the deployed Lambda functions

3. **Test the System**
   ```bash
   # Test Step Functions workflow
   aws stepfunctions start-execution \
       --state-machine-arn <WORKFLOW_ARN_FROM_OUTPUTS> \
       --input '{"firstName":"John","lastName":"Doe","phone":"+15555551234"}'
   ```

---

> **👉 CONFUSED? Pick your guide:**
> - **Never done this before?** → [START_HERE.md](START_HERE.md)
> - **Just want commands?** → [CHEAT_SHEET.txt](CHEAT_SHEET.txt)
> - **Want full details?** → Keep reading below

## 🚀 How to Deploy (Step-by-Step)

### Step 1: Open Terminal
1. Open Terminal on your Mac
2. Navigate to this folder:
   ```bash
   cd /Users/johndoe/Downloads/aws_org_export
   ```

### Step 2: Configure AWS
The scripts will use your AWS CLI configuration. To set region:
```bash
# Check current region
aws configure get region

# Change region (if needed)
aws configure set region us-west-2
```

**Note:** You don't need to manually add account ID - AWS automatically detects it from your credentials.

### Step 3: Set Up Salesforce Credentials
Create a file with your Salesforce credentials:
```bash
cat > salesforce-creds.json << 'EOF'
{
  "username": "your-email@company.com",
  "client_id": "YOUR_SALESFORCE_CLIENT_ID",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----"
}
EOF
```

### Step 4: Run Deployment
```bash
# Make scripts executable (one-time setup)
chmod +x *.sh

# Run deployment
./deploy.sh
```

The script will:
- Ask you questions (environment, region, etc.)
- Build everything automatically
- Deploy to AWS
- Show you what to do next

**That's it!** Takes 15-20 minutes.

### Step 5: Test (Optional)
```bash
./test-deployment.sh dev
```

## Common Questions

**Q: Do I need to edit any files with my account ID?**
A: No! The scripts automatically detect your AWS account from your credentials.

**Q: How do I change the region?**
A: Either set it before deployment (`aws configure set region us-west-2`) or the script will ask you.

**Q: What if I don't have Salesforce credentials yet?**
A: The script creates a placeholder secret. You can update it later.

**Q: How much will this cost?**
A: Development environment: ~$24/month. See [COST_ESTIMATION.md](COST_ESTIMATION.md).

**Q: How do I remove everything?**
A: Run `./cleanup.sh dev`

## 📋 What's Included

### Core Components
- **8 Lambda Functions**: CreateLead, GenerateScenario, InvokeCall, LexFulfillment, UpdateLead, StartTranscription, SummarizeAndResume
- **2 Lambda Layers**: Python libraries (requests, phonenumbers) and Salesforce libraries (simple-salesforce, PyJWT)
- **2 DynamoDB Tables**: Interactions storage and task token management
- **1 Step Functions Workflow**: Orchestrates lead creation → scenario generation → outbound call → lead update
- **Amazon Bedrock Integration**: Claude 3.5 Sonnet for AI-powered conversations
- **Salesforce Integration**: JWT authentication for CRM sync
- **Amazon Connect**: Outbound voice contact capability

### Deployment Tools
- **deploy.sh**: Automated deployment with validation
- **cleanup.sh**: Complete resource removal
- **validate.sh**: Pre-deployment checks
- **test-deployment.sh**: Post-deployment validation
- **build-layers.sh**: Lambda layer builder

### Documentation
- **QUICK_START.md**: 30-minute deployment guide
- **DEPLOYMENT_GUIDE.md**: Comprehensive deployment documentation
- **COST_ESTIMATION.md**: Detailed cost breakdown and optimization
- **DEPLOYMENT_ARCHITECTURE.md**: System architecture and dependencies
- **SECURITY_AUDIT_REPORT.md**: Security findings and remediation

### Templates
- **sam-template/template.yaml**: Main SAM template
- **quick-start.yaml**: One-click CloudFormation deployment
- **parameters-example.json**: Configuration examples

## 💰 Cost Estimate

| Environment | Monthly Cost | Use Case |
|-------------|--------------|----------|
| Development | ~$24 | Testing, 1K conversations |
| Staging | ~$214 | QA, 10K conversations |
| Production | ~$1,138 | Live, 50K conversations |

See [COST_ESTIMATION.md](COST_ESTIMATION.md) for detailed breakdown.

## 🏗️ Architecture

```
User → Amazon Lex → Lambda (Fulfillment)
                         ↓
                   Step Functions
                         ↓
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
   Salesforce      Amazon Bedrock   Amazon Connect
   (CRM Sync)      (AI Scenarios)   (Voice Calls)
        ↓                ↓                ↓
        └────────────────┼────────────────┘
                         ↓
                    DynamoDB
                  (Interactions)
```

## 📦 Project Structure

```
aws_org_export/
├── deploy.sh                    # Main deployment script
├── cleanup.sh                   # Resource cleanup
├── validate.sh                  # Pre-deployment validation
├── test-deployment.sh           # Post-deployment tests
├── build-layers.sh              # Lambda layer builder
├── requirements.txt             # Python dependencies
├── parameters-example.json      # Configuration template
├── quick-start.yaml             # One-click CloudFormation
├── QUICK_START.md              # 30-min deployment guide
├── DEPLOYMENT_GUIDE.md         # Full documentation
├── COST_ESTIMATION.md          # Cost analysis
├── lambda/                     # Lambda function code
│   ├── CreateLeadHandler_code/
│   ├── GenerateDynamicScenarioHandler_code/
│   ├── InvokeOutboundCallHandler_code/
│   ├── LexFulfillmentHandler_code/
│   ├── UpdateLeadHandler_code/
│   ├── StartTranscriptionHandler_code/
│   └── SummarizeAndResumeHandler_code/
├── sam-template/
│   ├── template.yaml           # SAM template
│   └── samconfig.toml          # SAM configuration
└── stepfunctions/
    └── workflow-definition.asl.json  # Step Functions definition
```

## 🔧 Prerequisites

- AWS CLI 2.x
- SAM CLI 1.100+
- Python 3.13+
- AWS account with:
  - Admin IAM permissions
  - Bedrock model access (Claude 3.5 Sonnet)
  - Salesforce Connected App credentials

## 📖 Deployment Options

### Option 1: Automated Script (Recommended)
```bash
./deploy.sh
```

### Option 2: Manual SAM Deployment
```bash
./build-layers.sh
sam build --parallel
sam deploy --guided
```

### Option 3: One-Click CloudFormation
```bash
aws cloudformation create-stack \
    --stack-name AtlasEngine-Infrastructure \
    --template-body file://quick-start.yaml \
    --parameters file://parameters.json \
    --capabilities CAPABILITY_IAM
```

## 🧪 Testing

```bash
# Validate environment
./validate.sh

# Deploy to dev
./deploy.sh

# Run tests
./test-deployment.sh dev

# Test Step Functions
aws stepfunctions start-execution \
    --state-machine-arn <WORKFLOW_ARN> \
    --input '{"firstName":"John","lastName":"Doe","phone":"+15555551234"}'
```

## 🔐 Security

- Secrets stored in AWS Secrets Manager
- IAM least-privilege policies
- Encryption at rest for DynamoDB
- VPC deployment supported
- No hardcoded credentials

See [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) for audit results.

## 🎯 Customization

### Change Bedrock Model
Edit `sam-template/template.yaml`:
```yaml
BedrockModelId:
  Default: anthropic.claude-3-opus-20240229-v1:0
```

### Add Custom Lambda
```yaml
MyCustomHandler:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: ../lambda/MyCustomHandler_code/
    Handler: lambda_function.lambda_handler
```

### Multi-Environment
```bash
# Deploy to staging
ENVIRONMENT=staging ./deploy.sh

# Deploy to production
ENVIRONMENT=prod ./deploy.sh
```

## 🗑️ Cleanup

```bash
# Remove all resources
./cleanup.sh dev

# Or manually
aws cloudformation delete-stack --stack-name AtlasEngine-dev
```

## 📊 Monitoring

```bash
# View Lambda logs
sam logs --stack-name AtlasEngine-dev --tail

# View Step Functions executions
aws stepfunctions list-executions \
    --state-machine-arn <WORKFLOW_ARN>

# View DynamoDB metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB \
    --metric-name ConsumedReadCapacityUnits \
    --dimensions Name=TableName,Value=AtlasEngineInteractions-dev
```

## 🐛 Troubleshooting

### Deployment fails
```bash
# Check SAM logs
sam logs --stack-name AtlasEngine-dev

# Validate template
sam validate

# Clean and rebuild
rm -rf .aws-sam && sam build
```

### Lambda timeout
Increase timeout in `template.yaml`:
```yaml
Timeout: 300
MemorySize: 1024
```

### Bedrock access denied
Enable model access in AWS Console:
Bedrock → Model access → Manage model access

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for more troubleshooting.

## 📚 Documentation

- [QUICK_START.md](QUICK_START.md) - 30-minute deployment
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete guide
- [COST_ESTIMATION.md](COST_ESTIMATION.md) - Cost analysis
- [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) - Architecture
- [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) - Security audit

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Test changes with `./validate.sh`
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

- AWS Documentation: https://docs.aws.amazon.com/
- Bedrock Docs: https://docs.aws.amazon.com/bedrock/
- SAM Docs: https://docs.aws.amazon.com/serverless-application-model/
- Issues: Create GitHub issue

## 🎉 Success Metrics

After deployment, you should see:
- ✅ 8 Lambda functions deployed
- ✅ 2 DynamoDB tables created
- ✅ 1 Step Functions workflow active
- ✅ Salesforce integration working
- ✅ Bedrock models accessible
- ✅ All tests passing

**Ready to deploy? Run `./deploy.sh` now!**
