# Atlas Engine - Complete Deployment Package Index

## 📦 Package Overview

**Complete AWS SAM deployment package for Atlas Engine**
- ✅ Production-ready
- ✅ One-click deployment
- ✅ Under 30 minutes setup
- ✅ Comprehensive documentation
- ✅ Cost-optimized

---

## 🚀 START HERE

### New Users
1. Read [README.md](README.md) - Overview and features
2. Read [QUICK_START.md](QUICK_START.md) - 30-minute deployment
3. Run `./validate.sh` - Check prerequisites
4. Run `./deploy.sh` - Deploy everything

### Experienced Users
```bash
./validate.sh && ./deploy.sh && ./test-deployment.sh dev
```

---

## 📁 File Organization

### 🔧 Deployment Scripts (5 files)
Execute these to deploy, test, and manage your infrastructure.

| File | Purpose | Usage | Time |
|------|---------|-------|------|
| [deploy.sh](deploy.sh) | Main deployment automation | `./deploy.sh` | 20 min |
| [validate.sh](validate.sh) | Pre-deployment checks | `./validate.sh` | 1 min |
| [test-deployment.sh](test-deployment.sh) | Post-deployment validation | `./test-deployment.sh dev` | 2 min |
| [build-layers.sh](build-layers.sh) | Build Lambda layers | `./build-layers.sh` | 3 min |
| [cleanup.sh](cleanup.sh) | Remove all resources | `./cleanup.sh dev` | 5 min |

### 📋 Templates (3 files)
Infrastructure as Code definitions.

| File | Purpose | Type |
|------|---------|------|
| [sam-template/template.yaml](sam-template/template.yaml) | Complete SAM template | SAM/CloudFormation |
| [quick-start.yaml](quick-start.yaml) | One-click deployment | CloudFormation |
| [stepfunctions/workflow-definition.asl.json](stepfunctions/workflow-definition.asl.json) | Step Functions workflow | ASL JSON |

### 📚 Documentation (9 files)
Comprehensive guides for every aspect of deployment.

#### Getting Started
| File | Purpose | Read Time |
|------|---------|-----------|
| [README.md](README.md) | Main documentation and overview | 5 min |
| [QUICK_START.md](QUICK_START.md) | 30-minute deployment guide | 3 min |
| [INDEX.md](INDEX.md) | This file - navigation guide | 2 min |

#### Deployment & Architecture
| File | Purpose | Read Time |
|------|---------|-----------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete deployment documentation | 15 min |
| [DEPLOYMENT_FLOWCHART.md](DEPLOYMENT_FLOWCHART.md) | Visual deployment process | 5 min |
| [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) | System architecture and dependencies | 10 min |
| [DEPLOYMENT_PACKAGE_SUMMARY.md](DEPLOYMENT_PACKAGE_SUMMARY.md) | Package overview and features | 8 min |

#### Cost & Security
| File | Purpose | Read Time |
|------|---------|-----------|
| [COST_ESTIMATION.md](COST_ESTIMATION.md) | Detailed cost breakdown | 10 min |
| [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) | Security findings and remediation | 8 min |

#### Reference
| File | Purpose | Read Time |
|------|---------|-----------|
| [DEPLOYMENT_FILES.txt](DEPLOYMENT_FILES.txt) | Quick file reference | 1 min |

### ⚙️ Configuration (4 files)
Configuration templates and dependencies.

| File | Purpose | Usage |
|------|---------|-------|
| [requirements.txt](requirements.txt) | Python dependencies | Used by build-layers.sh |
| [sam-template/samconfig.toml](sam-template/samconfig.toml) | SAM CLI configuration | Used by sam deploy |
| [parameters-example.json](parameters-example.json) | CloudFormation parameters | Copy and customize |
| [.gitignore](sam-template/.gitignore) | Git ignore rules | Prevents committing secrets |

### 💻 Lambda Functions (8 directories)
Business logic for the application.

| Directory | Purpose | Runtime |
|-----------|---------|---------|
| lambda/CreateLeadHandler_code/ | Create/find Salesforce leads | Python 3.13 |
| lambda/GenerateDynamicScenarioHandler_code/ | Generate AI scenarios with Bedrock | Python 3.13 |
| lambda/InvokeOutboundCallHandler_code/ | Initiate Amazon Connect calls | Python 3.13 |
| lambda/LexFulfillmentHandler_code/ | Lex bot fulfillment logic | Python 3.13 |
| lambda/UpdateLeadHandler_code/ | Update Salesforce leads | Python 3.13 |
| lambda/StartTranscriptionHandler_code/ | Start call transcription | Python 3.13 |
| lambda/SummarizeAndResumeHandler_code/ | Summarize conversations | Python 3.13 |
| lambda/InitiateCallHandler_code/ | Alternative call initiator | Python 3.13 |

---

## 🎯 Common Tasks

### First-Time Deployment
```bash
# 1. Validate environment
./validate.sh

# 2. Deploy infrastructure
./deploy.sh

# 3. Test deployment
./test-deployment.sh dev

# 4. Configure Lex bot (manual)
# See QUICK_START.md for instructions
```

### Update Existing Deployment
```bash
# Build and deploy changes
sam build --parallel
sam deploy --no-confirm-changeset
```

### Deploy to Different Environment
```bash
# Staging
ENVIRONMENT=staging ./deploy.sh

# Production
ENVIRONMENT=prod ./deploy.sh
```

### View Logs
```bash
# All logs
sam logs --stack-name AtlasEngine-dev --tail

# Specific function
sam logs -n CreateLeadHandler --stack-name AtlasEngine-dev --tail
```

### Test Workflow
```bash
# Start Step Functions execution
aws stepfunctions start-execution \
    --state-machine-arn $(aws cloudformation describe-stacks \
        --stack-name AtlasEngine-dev \
        --query "Stacks[0].Outputs[?OutputKey=='WorkflowArn'].OutputValue" \
        --output text) \
    --input '{"firstName":"Test","lastName":"User","phone":"+15555551234"}'
```

### Remove Everything
```bash
./cleanup.sh dev
```

---

## 📊 What Gets Deployed

### AWS Resources (26 total)

| Resource Type | Count | Names |
|---------------|-------|-------|
| **Lambda Functions** | 8 | CreateLead, GenerateScenario, InvokeCall, LexFulfillment, UpdateLead, StartTranscription, Summarize, InitiateCall |
| **Lambda Layers** | 2 | PythonLibraries, SalesforceLibraries |
| **DynamoDB Tables** | 2 | Interactions, TaskTokens |
| **Step Functions** | 1 | AtlasEngineWorkflow |
| **SNS Topics** | 1 | SalesTeamNotifications |
| **IAM Roles** | 8 | One per Lambda function |
| **CloudWatch Log Groups** | 9 | One per Lambda + Step Functions |
| **S3 Buckets** | 1 | Deployment artifacts |

### External Integrations

| Service | Purpose | Setup Required |
|---------|---------|----------------|
| **Salesforce** | CRM integration | Connected App credentials |
| **Amazon Bedrock** | AI/LLM capabilities | Model access enabled |
| **Amazon Lex** | Chatbot interface | Manual bot configuration |
| **Amazon Connect** | Voice calls | Optional - manual setup |

---

## 💰 Cost Summary

| Environment | Monthly Cost | Use Case |
|-------------|--------------|----------|
| **Development** | ~$24 | Testing, 1K conversations |
| **Staging** | ~$214 | QA, 10K conversations |
| **Production (Low)** | ~$1,138 | Live, 50K conversations |
| **Production (High)** | ~$10,220 | Enterprise, 500K conversations |

See [COST_ESTIMATION.md](COST_ESTIMATION.md) for detailed breakdown.

---

## 🔐 Security Features

- ✅ No hardcoded credentials
- ✅ Secrets in AWS Secrets Manager
- ✅ Least-privilege IAM policies
- ✅ Encryption at rest (DynamoDB)
- ✅ Encryption in transit (HTTPS/TLS)
- ✅ VPC deployment supported
- ✅ CloudTrail audit logging
- ✅ Pre-deployment security scan

See [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) for details.

---

## 🎓 Learning Path

### Beginner (Never used AWS SAM)
1. [README.md](README.md) - Understand what Atlas Engine does
2. [QUICK_START.md](QUICK_START.md) - Follow step-by-step guide
3. [DEPLOYMENT_FLOWCHART.md](DEPLOYMENT_FLOWCHART.md) - Visualize the process
4. Run `./deploy.sh` - Let automation handle it
5. [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Troubleshooting if needed

### Intermediate (Some AWS experience)
1. [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) - Understand architecture
2. [sam-template/template.yaml](sam-template/template.yaml) - Review infrastructure code
3. [COST_ESTIMATION.md](COST_ESTIMATION.md) - Plan budget
4. Run `./deploy.sh` - Deploy with understanding
5. Customize for your use case

### Advanced (AWS expert)
1. Review [sam-template/template.yaml](sam-template/template.yaml)
2. Review Lambda function code in lambda/ directories
3. Customize templates and code
4. Run `sam build && sam deploy`
5. Integrate with existing infrastructure

---

## 🐛 Troubleshooting Quick Reference

| Issue | Solution | Documentation |
|-------|----------|---------------|
| Deployment fails | Check IAM permissions | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#troubleshooting) |
| Lambda timeout | Increase timeout/memory | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#issue-lambda-timeout) |
| Bedrock access denied | Enable model access | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#issue-bedrock-access-denied) |
| High costs | Review optimization tips | [COST_ESTIMATION.md](COST_ESTIMATION.md#cost-optimization-strategies) |
| Salesforce auth fails | Verify secret format | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md#issue-salesforce-authentication-fails) |

---

## 📞 Support Resources

### Documentation
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)

### Tools
- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Console](https://console.aws.amazon.com/)
- [SAM CLI Reference](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-command-reference.html)

### Community
- [AWS Forums](https://forums.aws.amazon.com/)
- [Stack Overflow - AWS SAM](https://stackoverflow.com/questions/tagged/aws-sam)

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] SAM CLI installed (v1.100+)
- [ ] Python 3.13+ installed
- [ ] Salesforce Connected App created
- [ ] Bedrock model access requested
- [ ] Run `./validate.sh` successfully

### Deployment
- [ ] Run `./deploy.sh`
- [ ] Wait for completion (15-20 min)
- [ ] Note Lambda ARNs from output
- [ ] Run `./test-deployment.sh dev`

### Post-Deployment
- [ ] Configure Amazon Lex bot
- [ ] Set up Amazon Connect (optional)
- [ ] Update Salesforce secret with real credentials
- [ ] Test end-to-end workflow
- [ ] Set up monitoring and alarms
- [ ] Configure billing alerts

---

## 🎉 Success Metrics

After successful deployment, you should have:
- ✅ CloudFormation stack: CREATE_COMPLETE
- ✅ 8 Lambda functions: Active
- ✅ 2 DynamoDB tables: Active
- ✅ 1 Step Functions workflow: Active
- ✅ 2 Lambda layers: Published
- ✅ All IAM roles: Created
- ✅ CloudWatch logging: Enabled
- ✅ Test execution: Successful

---

## 🚀 Quick Commands Reference

```bash
# Validate prerequisites
./validate.sh

# Deploy to dev
./deploy.sh

# Deploy to staging
ENVIRONMENT=staging ./deploy.sh

# Deploy to production
ENVIRONMENT=prod ./deploy.sh

# Test deployment
./test-deployment.sh dev

# View logs
sam logs --stack-name AtlasEngine-dev --tail

# Update deployment
sam build && sam deploy

# Remove everything
./cleanup.sh dev

# Build layers only
./build-layers.sh

# Validate template
sam validate

# Local testing
sam local invoke CreateLeadHandler -e events/test-event.json
```

---

## 📈 Deployment Timeline

```
Total Time: 25-30 minutes

├─ Validation:        2 min  ✓
├─ Parameters:        1 min  ✓
├─ Salesforce Setup:  1 min  ✓
├─ Build Layers:      3 min  ✓
├─ Workflow Def:      0.5 min ✓
├─ SAM Build:         5 min  ✓
├─ SAM Deploy:       10 min  ✓
├─ Post-Deploy:       1 min  ✓
└─ Manual Config:    10 min  (Lex, Connect)
```

---

## 🎯 Next Steps

1. **Deploy Now**: Run `./deploy.sh`
2. **Learn More**: Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
3. **Understand Costs**: Read [COST_ESTIMATION.md](COST_ESTIMATION.md)
4. **Customize**: Modify [sam-template/template.yaml](sam-template/template.yaml)
5. **Monitor**: Set up CloudWatch dashboards

---

**Ready to deploy? Start with `./validate.sh` then `./deploy.sh`**

**Questions? See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive troubleshooting.**
