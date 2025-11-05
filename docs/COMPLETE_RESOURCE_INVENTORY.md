# Atlas Engine - Complete Resource Inventory

**Export Date:** 2025-10-29  
**Purpose:** Documentation reference for Atlas Engine AWS infrastructure

---

## 📋 Export Summary

This export contains a complete snapshot of all AWS resources used in the Atlas Engine project, including:

- ✅ 8 Lambda Functions (with source code)
- ✅ 7 Lambda Layers
- ✅ 1 Step Functions State Machine
- ✅ 9 IAM Roles with policies
- ✅ 2 DynamoDB Tables
- ✅ 1 Amazon Lex Bot
- ✅ 1 Amazon Connect Instance
- ✅ 2 CloudFormation Stacks
- ✅ 2 CloudFront Distributions
- ✅ 3 S3 Buckets
- ✅ 1 SQS Queue
- ✅ 1 SNS Topic
- ✅ 1 EventBridge Rule
- ✅ 1 Secrets Manager Secret
- ✅ 9 CloudWatch Log Groups

---

## 🔧 Lambda Functions

### Core Functions

| Function Name | Runtime | Memory | Timeout | Purpose |
|--------------|---------|--------|---------|---------|
| **LexFulfillmentHandler** | Python 3.13 | 512 MB | 30s | Handles Lex bot intents and orchestrates workflow |
| **CreateLeadHandler** | Python 3.13 | 128 MB | 15s | Creates leads in Salesforce |
| **GenerateDynamicScenarioHandler** | Python 3.13 | TBD | TBD | Generates AI-powered conversation scenarios |
| **InvokeOutboundCallHandler** | Python 3.13 | TBD | TBD | Initiates outbound calls via Amazon Connect |
| **InitiateCallHandler** | Python 3.13 | TBD | TBD | Handles call initiation logic |
| **StartTranscriptionHandler** | Python 3.13 | TBD | TBD | Starts transcription jobs for call recordings |
| **SummarizeAndResumeHandler** | Python 3.13 | TBD | TBD | Summarizes conversations and resumes workflow |
| **UpdateLeadHandler** | Python 3.13 | TBD | TBD | Updates Salesforce leads with call summaries |

### Lambda Layers

All functions use Python 3.13 compatible layers:

1. **LexBotDependencies-v4-FIXED** (v2) - 13.9 MB
   - Core dependencies for Lex bot functionality

2. **PythonLibraries-Minimal-v6** (v1) - Size TBD
   - Minimal libraries: requests, phonenumbers, wrapt

3. **RequestsAndSalesforceLibrary** (v1) - Size TBD
   - Libraries: requests, PyJWT, simple-salesforce

4. **RequestsLibrary** (v4) - 1.1 MB
   - HTTP requests library

5. **SalesforceDependenciesLayer** (v1) - 14.0 MB
   - Salesforce integration dependencies

6. **SimpleSalesforceLibrary** (v5) - Size TBD
   - Salesforce API client

7. **phonenumbers** (v2) - 16.1 MB
   - Phone number parsing and validation

**Location:** `/lambda_layers/`

---

## 🔄 Step Functions

### AtlasEngineWorkflow

**Type:** EXPRESS  
**Purpose:** Orchestrates the four-phase customer engagement process

**Workflow Phases:**
1. **CreateLeadAndScenario** (Parallel)
   - Create Salesforce Lead
   - Generate Dynamic Scenario (AI-powered)

2. **CombineParallelResults**
   - Merges results from parallel execution

3. **Invoke Outbound Voice Contact**
   - Uses callback pattern (waitForTaskToken)
   - Timeout: 1800 seconds (30 minutes)

4. **Update Lead with Summary**
   - Updates Salesforce with call summary

**Configuration:**
- Logging: ALL (includes execution data)
- Tracing: Enabled (X-Ray)
- Encryption: AWS_OWNED_KEY

**Location:** `/stepfunctions/AtlasEngineWorkflow.json`

---

## 🔐 IAM Roles & Policies

### Lambda Execution Roles

1. **CreateLeadHandler-role-sduo9h9n**
   - Salesforce Secrets access
   - DynamoDB write permissions
   - CloudWatch Logs

2. **GenerateDynamicScenarioHandler-role-vbv9ftg1**
   - Bedrock model invocation
   - DynamoDB read/write
   - CloudWatch Logs

3. **InitiateCallHandler-role-iwcl0yhb**
   - Amazon Connect permissions
   - DynamoDB access
   - CloudWatch Logs

4. **InvokeOutboundCallHandler-role-p7ou5zno**
   - Amazon Connect outbound calls
   - Step Functions task token
   - DynamoDB access

5. **LexFulfillmentHandler-role-gf8r6bq2**
   - Step Functions execution
   - Bedrock model access
   - DynamoDB read/write
   - Secrets Manager read
   - SNS publish

6. **StartTranscriptionHandler-role-k0h94r1f**
   - Amazon Transcribe permissions
   - S3 access for recordings
   - DynamoDB access

7. **SummarizeAndResumeHandler-role-ogn1ngtx**
   - Bedrock model invocation
   - Step Functions task token
   - DynamoDB access

8. **UpdateLeadHandler-role** (Missing from original export - NOW INCLUDED)
   - Salesforce API access
   - Secrets Manager read
   - CloudWatch Logs

### Step Functions Role

9. **StepFunctions-AtlasEngineWorkflow-role-46ivk0793**
   - Lambda invoke permissions
   - CloudWatch Logs
   - X-Ray tracing

**Location:** `/iam/`

---

## 💾 DynamoDB Tables

### 1. AtlasEngineInteractions
**Purpose:** Stores conversation interactions and dynamic scenarios

**Key Schema:**
- Partition Key: `PK` (String) - Format: `LEAD#<phone>`
- Sort Key: `SK` (String) - Format: `INTERACTION#<timestamp>`

**Attributes:**
- DynamicScenario (String) - AI-generated conversation script
- FirstName, LastName, Phone
- Timestamps, Status

### 2. AtlasEngineTaskTokens
**Purpose:** Stores Step Functions task tokens for callback pattern

**Key Schema:**
- Partition Key: `PK` (String)
- Sort Key: `SK` (String)

**Attributes:**
- TaskToken (String)
- ExpirationTime (Number)
- Status (String)

**Location:** `/dynamodb/`

---

## 🤖 Amazon Lex

### AtlasEngineBot

**Purpose:** Conversational AI for customer interactions

**Intents:**
- ScheduleCallIntent - Captures customer information
- AboutTechnologyIntent - Answers technology questions
- AboutDemoIntent - Provides demo information
- FallbackIntent - Handles unrecognized inputs

**Locales:** en_US

**Integration:** Connected to LexFulfillmentHandler Lambda

**Location:** `/lex/`

---

## 📞 Amazon Connect

### Instance: intrepidlyintrepid
**Instance ID:** <CONNECT_INSTANCE_ID>

**Components:**
- Contact Flows (exported)
- Phone Numbers (exported)
- Hours of Operations (exported)
- Queues (exported)

**Integration:** Triggers Lambda functions for call handling

**Location:** `/connect/`

---

## ☁️ CloudFormation Stacks

### 1. atlas-engine-dynamodb
**Purpose:** Provisions DynamoDB tables

**Resources:**
- AtlasEngineInteractions table
- AtlasEngineTaskTokens table

### 2. AtlasEngine-LexWebUI
**Purpose:** Deploys Lex Web UI for testing

**Resources:**
- S3 buckets for web hosting
- CloudFront distribution
- CodeBuild project for deployment

**Location:** `/cloudformation/`

---

## 🌐 CloudFront Distributions

### 1. E2I21H2PCFYG9J
**Purpose:** CDN for Lex Web UI

### 2. E3785MV35RHIXR
**Purpose:** Additional distribution (likely for assets)

**Location:** `/cloudfront/`

---

## 🪣 S3 Buckets

### 1. atlasengine-lexwebui-code-lexwebuicloudfrontdistri-r189yvixe251
**Purpose:** Lex Web UI code storage

### 2. atlasengine-lexwebui-codebuildd-s3serveraccesslogs-ybsdbnzymrrx
**Purpose:** Server access logs

### 3. atlasengine-lexwebui-codebuilddeploy--webappbucket-k2kfa9imz0kf
**Purpose:** Web application deployment

**Location:** `/s3/`

---

## 📬 Messaging Services

### SQS Queue
**Name:** SmsQuickStartStack-d9558817-SmsSQSQueue-OS81qC9lMJrV  
**Purpose:** SMS message queuing

**Location:** `/sqs/`

### SNS Topic
**Name:** SmsQuickStartSnsDestination  
**Purpose:** SMS notifications to sales team

**Location:** `/sns/`

---

## 🔔 EventBridge

### TranscribeJobStatusRule
**Purpose:** Monitors Amazon Transcribe job completion  
**Target:** StartTranscriptionHandler Lambda

**Location:** `/eventbridge/`

---

## 🔒 Secrets Manager

### AtlasEngine/SalesforceCreds
**Purpose:** Stores Salesforce API credentials

**Used By:**
- CreateLeadHandler
- UpdateLeadHandler
- LexFulfillmentHandler

**Note:** Only metadata exported (no actual secrets)

**Location:** `/secrets/`

---

## 📊 CloudWatch Log Groups

All Lambda functions and Step Functions have dedicated log groups:

1. `/aws/lambda/CreateLeadHandler`
2. `/aws/lambda/GenerateDynamicScenarioHandler`
3. `/aws/lambda/InitiateCallHandler`
4. `/aws/lambda/InvokeOutboundCallHandler`
5. `/aws/lambda/LexFulfillmentHandler`
6. `/aws/lambda/StartTranscriptionHandler`
7. `/aws/lambda/SummarizeAndResumeHandler`
8. `/aws/lambda/UpdateLeadHandler`
9. `/aws/vendedlogs/states/AtlasEngineWorkflow-Logs`

**Location:** `/cloudwatch/`

---

## 🎯 Amazon Transcribe

**Purpose:** Converts call recordings to text

**Integration:** Triggered by EventBridge rule when recordings are available

**Location:** `/transcribe/`

---

## 📁 Directory Structure

```
aws_org_export/
├── cloudformation/          # CloudFormation stacks and templates
├── cloudfront/             # CloudFront distribution configs
├── cloudwatch/             # Log group configurations
├── connect/                # Amazon Connect instance and flows
├── dynamodb/               # DynamoDB table schemas and data
├── eventbridge/            # EventBridge rules
├── iam/                    # IAM roles and policies
├── lambda/                 # Lambda function code and configs
├── lambda_layers/          # Lambda layer details (NEW)
├── lex/                    # Lex bot configuration
├── s3/                     # S3 bucket configurations
├── secrets/                # Secrets Manager metadata
├── sns/                    # SNS topic configurations
├── sqs/                    # SQS queue configurations (NEW)
├── stepfunctions/          # Step Functions state machines
└── transcribe/             # Transcribe job information
```

---

## 🔄 What Was Added in This Export

### Previously Missing Resources (NOW INCLUDED):

1. **Lambda Layers** (7 layers)
   - Complete version history and details
   - Compatible runtimes and architectures
   - Size information

2. **SQS Queue**
   - Queue attributes and configuration
   - Message retention settings

3. **Missing IAM Role**
   - UpdateLeadHandler role with inline policies

4. **Fresh Lambda Code Pull**
   - All 8 Lambda functions re-exported
   - Latest code versions

5. **Step Functions Execution History**
   - Last 10 executions for debugging

6. **Step Functions CloudWatch Logs**
   - Log group configuration

7. **Amazon Connect Details**
   - Phone numbers
   - Hours of operations
   - Queues

8. **Secrets Manager Re-export**
   - Updated metadata

---

## 🚀 Usage for Documentation

This export provides everything needed to document:

1. **Architecture Diagrams**
   - Service interactions from Step Functions definition
   - Data flow from Lambda environment variables

2. **API Documentation**
   - Lambda function signatures from code
   - Input/output schemas from Step Functions

3. **Deployment Guides**
   - IAM permissions from role policies
   - Environment variables from Lambda configs
   - Layer dependencies from Lambda configs

4. **Security Documentation**
   - Encryption settings
   - Secret management patterns
   - IAM least privilege examples

5. **Operational Runbooks**
   - CloudWatch log locations
   - Monitoring and alerting setup
   - Troubleshooting guides

---

## 📝 Notes

- All Lambda functions use Python 3.13 runtime
- Step Functions uses EXPRESS workflow type for low latency
- X-Ray tracing enabled for distributed tracing
- All resources tagged with Project: AtlasEngine
- Region: us-west-2 (Oregon)

---

## 🔍 Verification Checklist

- [x] All 8 Lambda functions exported with code
- [x] All 7 Lambda layers documented
- [x] Step Functions state machine definition
- [x] All 9 IAM roles with policies
- [x] DynamoDB table schemas
- [x] Lex bot configuration
- [x] Amazon Connect instance details
- [x] CloudFormation templates
- [x] S3 bucket configurations
- [x] SQS queue configuration
- [x] SNS topic configuration
- [x] EventBridge rules
- [x] Secrets Manager metadata
- [x] CloudWatch log groups

**Export Status:** ✅ COMPLETE

---

*Generated by export_missing_resources.sh on 2025-10-29*
