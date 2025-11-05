# Atlas Engine - Deployment Architecture & Dependency Analysis

**Analysis Date:** 2025-10-29  
**Total Resources:** 30+ AWS resources across 16 service types

---

## 📊 1. DEPENDENCY GRAPH

```
┌─────────────────────────────────────────────────────────────────┐
│                        FOUNDATION LAYER                          │
│  (No dependencies - can deploy in parallel)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Secrets Mgr  │  │  S3 Buckets  │  │  SNS Topic   │          │
│  │ (Salesforce) │  │  (4 buckets) │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  SQS Queue   │  │ Lambda Layers│  │ CloudWatch   │          │
│  │              │  │  (7 layers)  │  │ Log Groups   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATA & STORAGE LAYER                        │
│  (Depends on: Foundation)                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              DynamoDB Tables (2)                          │   │
│  │  • AtlasEngineInteractions                               │   │
│  │  • AtlasEngineTaskTokens                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      IAM POLICIES LAYER                          │
│  (Depends on: DynamoDB, S3, Secrets)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Custom Managed Policies (4)                       │   │
│  │  • AtlasEngineCorePolicy                                 │   │
│  │  • AtlasEngineLoggingPolicy                              │   │
│  │  • AtlasEngineSecretsPolicy                              │   │
│  │  • ScopedBedrockInvokePolicy                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        IAM ROLES LAYER                           │
│  (Depends on: Managed Policies)                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Lambda Execution Roles (8)                   │   │
│  │  • CreateLeadHandler-role                                │   │
│  │  • GenerateDynamicScenarioHandler-role                   │   │
│  │  • InitiateCallHandler-role                              │   │
│  │  • InvokeOutboundCallHandler-role                        │   │
│  │  • LexFulfillmentHandler-role                            │   │
│  │  • StartTranscriptionHandler-role                        │   │
│  │  • SummarizeAndResumeHandler-role                        │   │
│  │  • UpdateLeadHandler-role                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Step Functions Execution Role (1)                 │   │
│  │  • StepFunctions-AtlasEngineWorkflow-role                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      LAMBDA FUNCTIONS LAYER                      │
│  (Depends on: IAM Roles, Lambda Layers, DynamoDB)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Core Lambda Functions (8)                    │   │
│  │  1. CreateLeadHandler                                    │   │
│  │  2. GenerateDynamicScenarioHandler                       │   │
│  │  3. InitiateCallHandler                                  │   │
│  │  4. InvokeOutboundCallHandler                            │   │
│  │  5. LexFulfillmentHandler                                │   │
│  │  6. StartTranscriptionHandler                            │   │
│  │  7. SummarizeAndResumeHandler                            │   │
│  │  8. UpdateLeadHandler                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                            │
│  (Depends on: Lambda Functions, IAM Roles)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Step Functions State Machine                    │   │
│  │  • AtlasEngineWorkflow                                   │   │
│  │    - Invokes: CreateLeadHandler                          │   │
│  │    - Invokes: GenerateDynamicScenarioHandler             │   │
│  │    - Invokes: InvokeOutboundCallHandler                  │   │
│  │    - Invokes: UpdateLeadHandler                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                             │
│  (Depends on: Step Functions, Lambda Functions)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Amazon Lex Bot                               │   │
│  │  • AtlasEngineBot                                        │   │
│  │    - Fulfillment: LexFulfillmentHandler                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            Amazon Connect Instance                        │   │
│  │  • intrepidlyintrepid                                    │   │
│  │    - Contact Flows                                       │   │
│  │    - Phone Numbers                                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │            EventBridge Rule                               │   │
│  │  • TranscribeJobStatusRule                               │   │
│  │    - Target: StartTranscriptionHandler                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 2. CIRCULAR DEPENDENCIES ANALYSIS

### ⚠️ IDENTIFIED CIRCULAR DEPENDENCY:

**LexFulfillmentHandler ↔ Step Functions**

```
LexFulfillmentHandler
    ↓ (starts execution)
Step Functions (AtlasEngineWorkflow)
    ↓ (invokes via callback)
InvokeOutboundCallHandler
    ↓ (sends task token back)
Step Functions
    ↓ (continues workflow)
[Back to Lambda functions]
```

### ✅ RESOLUTION STRATEGY:

**Use Two-Phase Deployment:**

1. **Phase 1:** Deploy Step Functions with placeholder Lambda ARNs
2. **Phase 2:** Update LexFulfillmentHandler with Step Functions ARN
3. **Phase 3:** Update Step Functions with actual Lambda ARNs

**OR**

Use CloudFormation Custom Resources to handle the circular reference.

---

## 📋 3. DEPLOYMENT ORDER

### **STAGE 1: Foundation (Parallel Deployment)**
*Estimated Time: 5-10 minutes*

Deploy these resources in parallel - no dependencies:

```yaml
Group 1A - Secrets & Storage:
  - Secrets Manager: SalesforceCreds
  - S3 Buckets (4):
    • atlasengine-lexwebui-code-*
    • atlasengine-lexwebui-codebuildd-*
    • atlasengine-lexwebui-codebuilddeploy-*
    • intrepid-services-cc

Group 1B - Messaging:
  - SNS Topic: SmsQuickStartSnsDestination
  - SQS Queue: SmsSQSQueue

Group 1C - Lambda Dependencies:
  - Lambda Layers (7):
    • LexBotDependencies-v4-FIXED
    • PythonLibraries-Minimal-v6
    • RequestsAndSalesforceLibrary
    • RequestsLibrary
    • SalesforceDependenciesLayer
    • SimpleSalesforceLibrary
    • phonenumbers

Group 1D - Logging:
  - CloudWatch Log Groups (9)
```

---

### **STAGE 2: Data Layer (Sequential)**
*Estimated Time: 2-5 minutes*

```yaml
Step 2.1 - DynamoDB Tables:
  - AtlasEngineInteractions
  - AtlasEngineTaskTokens
  
  Wait for: ACTIVE status
```

---

### **STAGE 3: IAM Layer (Sequential)**
*Estimated Time: 2-3 minutes*

```yaml
Step 3.1 - Custom Managed Policies:
  - AtlasEngineCorePolicy
  - AtlasEngineLoggingPolicy
  - AtlasEngineSecretsPolicy
  - ScopedBedrockInvokePolicy

Step 3.2 - IAM Roles (Parallel):
  Lambda Roles (8):
    - CreateLeadHandler-role
    - GenerateDynamicScenarioHandler-role
    - InitiateCallHandler-role
    - InvokeOutboundCallHandler-role
    - LexFulfillmentHandler-role
    - StartTranscriptionHandler-role
    - SummarizeAndResumeHandler-role
    - UpdateLeadHandler-role
  
  Step Functions Role (1):
    - StepFunctions-AtlasEngineWorkflow-role
```

---

### **STAGE 4: Lambda Functions (Parallel)**
*Estimated Time: 5-10 minutes*

```yaml
Deploy all Lambda functions in parallel:
  - CreateLeadHandler
  - GenerateDynamicScenarioHandler
  - InitiateCallHandler
  - InvokeOutboundCallHandler
  - LexFulfillmentHandler (without Step Functions ARN initially)
  - StartTranscriptionHandler
  - SummarizeAndResumeHandler
  - UpdateLeadHandler

Note: LexFulfillmentHandler environment variable STATE_MACHINE_ARN 
      should be set to placeholder initially
```

---

### **STAGE 5: Orchestration (Sequential)**
*Estimated Time: 2-3 minutes*

```yaml
Step 5.1 - Step Functions:
  - AtlasEngineWorkflow
    • References: All 4 Lambda functions
    • Role: StepFunctions-AtlasEngineWorkflow-role

Step 5.2 - Update LexFulfillmentHandler:
  - Update environment variable STATE_MACHINE_ARN
    with actual Step Functions ARN
```

---

### **STAGE 6: Integration Layer (Sequential)**
*Estimated Time: 10-15 minutes*

```yaml
Step 6.1 - Amazon Lex:
  - AtlasEngineBot
    • Fulfillment Lambda: LexFulfillmentHandler

Step 6.2 - Amazon Connect:
  - Instance: intrepidlyintrepid
  - Contact Flows
  - Phone Numbers
  - Queues

Step 6.3 - EventBridge:
  - TranscribeJobStatusRule
    • Target: StartTranscriptionHandler
```

---

### **STAGE 7: Frontend (Optional - Parallel)**
*Estimated Time: 5-10 minutes*

```yaml
CloudFormation Stacks:
  - AtlasEngine-LexWebUI
    • CloudFront distributions
    • S3 web hosting
    • CodeBuild deployment
```

---

## ⚡ 4. PARALLEL vs SEQUENTIAL DEPLOYMENT

### **Can Deploy in PARALLEL:**

**Stage 1 - Foundation (All Groups):**
- Secrets Manager
- All S3 Buckets (4)
- SNS Topic
- SQS Queue
- All Lambda Layers (7)
- All CloudWatch Log Groups (9)

**Stage 3.2 - IAM Roles:**
- All 8 Lambda execution roles
- Step Functions execution role

**Stage 4 - Lambda Functions:**
- All 8 Lambda functions (after IAM roles exist)

---

### **Must Deploy SEQUENTIALLY:**

1. **Foundation → Data Layer**
   - Need S3, Secrets before DynamoDB

2. **Data Layer → IAM Policies**
   - Policies reference DynamoDB table ARNs

3. **IAM Policies → IAM Roles**
   - Roles attach to policies

4. **IAM Roles → Lambda Functions**
   - Functions need execution roles

5. **Lambda Functions → Step Functions**
   - Step Functions references Lambda ARNs

6. **Step Functions → Lex/Connect**
   - Integration layer needs orchestration

---

## 📦 5. CLOUDFORMATION NESTED STACKS STRATEGY

### **Recommended Stack Structure:**

```
atlas-engine-root-stack.yaml
│
├── 1-foundation-stack.yaml
│   ├── secrets-stack.yaml
│   ├── storage-stack.yaml (S3 buckets)
│   ├── messaging-stack.yaml (SNS, SQS)
│   └── lambda-layers-stack.yaml
│
├── 2-data-stack.yaml
│   └── dynamodb-tables-stack.yaml
│
├── 3-iam-stack.yaml
│   ├── managed-policies-stack.yaml
│   └── roles-stack.yaml
│
├── 4-compute-stack.yaml
│   ├── lambda-functions-stack.yaml
│   └── step-functions-stack.yaml
│
├── 5-integration-stack.yaml
│   ├── lex-bot-stack.yaml
│   ├── connect-stack.yaml
│   └── eventbridge-stack.yaml
│
└── 6-frontend-stack.yaml (optional)
    └── lex-webui-stack.yaml
```

---

### **Stack Details:**

#### **1. Foundation Stack** (`1-foundation-stack.yaml`)
```yaml
Resources:
  SecretsStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: secrets-stack.yaml
  
  StorageStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: storage-stack.yaml
  
  MessagingStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: messaging-stack.yaml
  
  LambdaLayersStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: lambda-layers-stack.yaml

Outputs:
  SecretArn:
    Value: !GetAtt SecretsStack.Outputs.SalesforceSecretArn
  SNSTopicArn:
    Value: !GetAtt MessagingStack.Outputs.SNSTopicArn
  LayerArns:
    Value: !GetAtt LambdaLayersStack.Outputs.AllLayerArns
```

#### **2. Data Stack** (`2-data-stack.yaml`)
```yaml
Parameters:
  FoundationStackName:
    Type: String

Resources:
  InteractionsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: AtlasEngineInteractions
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE

  TaskTokensTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: AtlasEngineTaskTokens
      BillingMode: PAY_PER_REQUEST
      # ... schema

Outputs:
  InteractionsTableArn:
    Value: !GetAtt InteractionsTable.Arn
  TaskTokensTableArn:
    Value: !GetAtt TaskTokensTable.Arn
```

#### **3. IAM Stack** (`3-iam-stack.yaml`)
```yaml
Parameters:
  DataStackName:
    Type: String
  FoundationStackName:
    Type: String

Resources:
  ManagedPoliciesStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: managed-policies-stack.yaml
      Parameters:
        InteractionsTableArn:
          Fn::ImportValue: !Sub "${DataStackName}-InteractionsTableArn"
        TaskTokensTableArn:
          Fn::ImportValue: !Sub "${DataStackName}-TaskTokensTableArn"

  RolesStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: ManagedPoliciesStack
    Properties:
      TemplateURL: roles-stack.yaml
      Parameters:
        CorePolicyArn: !GetAtt ManagedPoliciesStack.Outputs.CorePolicyArn
        LoggingPolicyArn: !GetAtt ManagedPoliciesStack.Outputs.LoggingPolicyArn
        SecretsPolicyArn: !GetAtt ManagedPoliciesStack.Outputs.SecretsPolicyArn
        BedrockPolicyArn: !GetAtt ManagedPoliciesStack.Outputs.BedrockPolicyArn
```

#### **4. Compute Stack** (`4-compute-stack.yaml`)
```yaml
Parameters:
  IAMStackName:
    Type: String
  FoundationStackName:
    Type: String

Resources:
  LambdaFunctionsStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: lambda-functions-stack.yaml
      Parameters:
        # Pass all role ARNs
        CreateLeadRoleArn:
          Fn::ImportValue: !Sub "${IAMStackName}-CreateLeadHandlerRoleArn"
        # ... other roles

  StepFunctionsStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: LambdaFunctionsStack
    Properties:
      TemplateURL: step-functions-stack.yaml
      Parameters:
        CreateLeadFunctionArn:
          !GetAtt LambdaFunctionsStack.Outputs.CreateLeadHandlerArn
        # ... other function ARNs
```

#### **5. Integration Stack** (`5-integration-stack.yaml`)
```yaml
Parameters:
  ComputeStackName:
    Type: String

Resources:
  LexBotStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: lex-bot-stack.yaml
      Parameters:
        FulfillmentLambdaArn:
          Fn::ImportValue: !Sub "${ComputeStackName}-LexFulfillmentHandlerArn"

  ConnectStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: connect-stack.yaml

  EventBridgeStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: eventbridge-stack.yaml
      Parameters:
        TargetLambdaArn:
          Fn::ImportValue: !Sub "${ComputeStackName}-StartTranscriptionHandlerArn"
```

---

## 🎯 6. DEPLOYMENT BEST PRACTICES

### **Pre-Deployment Checklist:**

```bash
# 1. Validate all templates
aws cloudformation validate-template --template-body file://stack.yaml

# 2. Package Lambda code
cd lambda/CreateLeadHandler_code && zip -r ../CreateLeadHandler.zip .

# 3. Upload to S3
aws s3 cp lambda/CreateLeadHandler.zip s3://deployment-bucket/

# 4. Create Lambda layers
cd layers/python && zip -r ../../layer.zip .
aws lambda publish-layer-version --layer-name MyLayer --zip-file fileb://layer.zip
```

### **Deployment Commands:**

```bash
# Deploy in order
aws cloudformation create-stack \
  --stack-name atlas-engine-foundation \
  --template-body file://1-foundation-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name atlas-engine-foundation

# Continue with next stack...
```

### **Rollback Strategy:**

```bash
# Delete in reverse order
aws cloudformation delete-stack --stack-name atlas-engine-integration
aws cloudformation delete-stack --stack-name atlas-engine-compute
aws cloudformation delete-stack --stack-name atlas-engine-iam
aws cloudformation delete-stack --stack-name atlas-engine-data
aws cloudformation delete-stack --stack-name atlas-engine-foundation
```

---

## 📊 7. DEPLOYMENT TIMELINE

| Stage | Resources | Time | Can Parallelize |
|-------|-----------|------|-----------------|
| 1. Foundation | 20+ resources | 5-10 min | ✅ Yes |
| 2. Data | 2 tables | 2-5 min | ❌ No |
| 3. IAM | 13 policies/roles | 2-3 min | ⚠️ Partial |
| 4. Compute | 8 functions | 5-10 min | ✅ Yes |
| 5. Orchestration | 1 state machine | 2-3 min | ❌ No |
| 6. Integration | 3 services | 10-15 min | ⚠️ Partial |
| **TOTAL** | **30+ resources** | **26-46 min** | |

---

## 🔍 8. DEPENDENCY MATRIX

| Resource | Depends On | Depended By |
|----------|------------|-------------|
| Secrets Manager | - | IAM Policies, Lambda |
| S3 Buckets | - | Lambda, Connect |
| Lambda Layers | - | Lambda Functions |
| DynamoDB Tables | - | IAM Policies, Lambda |
| Managed Policies | DynamoDB, S3, Secrets | IAM Roles |
| IAM Roles | Managed Policies | Lambda, Step Functions |
| Lambda Functions | IAM Roles, Layers, DynamoDB | Step Functions, Lex |
| Step Functions | Lambda, IAM Role | Lex, Lambda |
| Lex Bot | Lambda | Connect |
| Connect | Lambda, Lex | - |
| EventBridge | Lambda | - |

---

## ⚠️ 9. CRITICAL NOTES

1. **Circular Dependency:** LexFulfillmentHandler ↔ Step Functions requires two-phase deployment

2. **Amazon Connect:** Cannot be fully automated via CloudFormation - requires manual setup or AWS CLI

3. **Lambda Layers:** Must be published before Lambda function deployment

4. **IAM Propagation:** Wait 10-30 seconds after creating IAM roles before deploying Lambda

5. **DynamoDB:** Use on-demand billing to avoid capacity planning during deployment

6. **Secrets Manager:** Must be created and populated before Lambda deployment

---

## 📝 10. DEPLOYMENT SCRIPT

```bash
#!/bin/bash
# deploy-atlas-engine.sh

set -e

REGION="us-west-2"
STACK_PREFIX="atlas-engine"

echo "🚀 Deploying Atlas Engine..."

# Stage 1: Foundation
echo "📦 Stage 1: Foundation..."
aws cloudformation create-stack \
  --stack-name ${STACK_PREFIX}-foundation \
  --template-body file://stacks/1-foundation-stack.yaml \
  --region $REGION

aws cloudformation wait stack-create-complete \
  --stack-name ${STACK_PREFIX}-foundation \
  --region $REGION

# Stage 2: Data
echo "💾 Stage 2: Data Layer..."
aws cloudformation create-stack \
  --stack-name ${STACK_PREFIX}-data \
  --template-body file://stacks/2-data-stack.yaml \
  --region $REGION

aws cloudformation wait stack-create-complete \
  --stack-name ${STACK_PREFIX}-data \
  --region $REGION

# Stage 3: IAM
echo "🔐 Stage 3: IAM Layer..."
aws cloudformation create-stack \
  --stack-name ${STACK_PREFIX}-iam \
  --template-body file://stacks/3-iam-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

aws cloudformation wait stack-create-complete \
  --stack-name ${STACK_PREFIX}-iam \
  --region $REGION

# Stage 4: Compute
echo "⚡ Stage 4: Compute Layer..."
aws cloudformation create-stack \
  --stack-name ${STACK_PREFIX}-compute \
  --template-body file://stacks/4-compute-stack.yaml \
  --region $REGION

aws cloudformation wait stack-create-complete \
  --stack-name ${STACK_PREFIX}-compute \
  --region $REGION

# Stage 5: Integration
echo "🔗 Stage 5: Integration Layer..."
aws cloudformation create-stack \
  --stack-name ${STACK_PREFIX}-integration \
  --template-body file://stacks/5-integration-stack.yaml \
  --region $REGION

aws cloudformation wait stack-create-complete \
  --stack-name ${STACK_PREFIX}-integration \
  --region $REGION

echo "✅ Deployment complete!"
```

---

*Generated: 2025-10-29*  
*Total Resources Analyzed: 30+*  
*Deployment Stages: 6*
