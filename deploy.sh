#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🚀 Atlas Engine Deployment Script"
echo "=================================="

# Check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found${NC}"
        exit 1
    fi
    
    if ! command -v sam &> /dev/null; then
        echo -e "${RED}❌ SAM CLI not found. Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html${NC}"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites met${NC}"
}

# Validate parameters
validate_parameters() {
    echo -e "\n${YELLOW}Validating parameters...${NC}"
    
    if [ -z "$ENVIRONMENT" ]; then
        read -p "Environment (dev/staging/prod) [dev]: " ENVIRONMENT
        ENVIRONMENT=${ENVIRONMENT:-dev}
    fi
    
    if [ -z "$REGION" ]; then
        REGION=$(aws configure get region)
        read -p "AWS Region [$REGION]: " INPUT_REGION
        REGION=${INPUT_REGION:-$REGION}
    fi
    
    if [ -z "$SALESFORCE_SECRET" ]; then
        read -p "Salesforce Secret Name [AtlasEngine/SalesforceCreds]: " SALESFORCE_SECRET
        SALESFORCE_SECRET=${SALESFORCE_SECRET:-AtlasEngine/SalesforceCreds}
    fi
    
    echo -e "${GREEN}✓ Parameters validated${NC}"
}

# Check Salesforce secret
check_salesforce_secret() {
    echo -e "\n${YELLOW}Checking Salesforce secret...${NC}"
    
    if aws secretsmanager describe-secret --secret-id "$SALESFORCE_SECRET" --region "$REGION" &> /dev/null; then
        echo -e "${GREEN}✓ Salesforce secret exists${NC}"
    else
        echo -e "${YELLOW}⚠ Salesforce secret not found. Creating placeholder...${NC}"
        aws secretsmanager create-secret \
            --name "$SALESFORCE_SECRET" \
            --secret-string '{"username":"REPLACE_ME","client_id":"REPLACE_ME","private_key":"REPLACE_ME"}' \
            --region "$REGION"
        echo -e "${YELLOW}⚠ Update secret with real credentials before testing${NC}"
    fi
}

# Build layers
build_layers() {
    echo -e "\n${YELLOW}Building Lambda layers...${NC}"
    
    mkdir -p layers/python-libraries/python
    mkdir -p layers/salesforce-libraries/python
    
    pip install -q requests phonenumbers wrapt -t layers/python-libraries/python/
    pip install -q simple-salesforce PyJWT cryptography -t layers/salesforce-libraries/python/
    
    echo -e "${GREEN}✓ Layers built${NC}"
}

# Create workflow definition
create_workflow_definition() {
    echo -e "\n${YELLOW}Creating Step Functions definition...${NC}"
    
    mkdir -p stepfunctions
    cat > stepfunctions/workflow-definition.asl.json << 'EOF'
{
  "Comment": "AtlasEngineWorkflow - Four-phase customer engagement",
  "StartAt": "Create Salesforce Lead",
  "States": {
    "Create Salesforce Lead": {
      "Type": "Task",
      "Resource": "${CreateLeadHandlerArn}",
      "ResultPath": "$.salesforce",
      "Retry": [{"ErrorEquals": ["Lambda.ServiceException"], "IntervalSeconds": 2, "MaxAttempts": 3}],
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Workflow Failed"}],
      "Next": "Generate Dynamic Scenario"
    },
    "Generate Dynamic Scenario": {
      "Type": "Task",
      "Resource": "${GenerateDynamicScenarioHandlerArn}",
      "ResultPath": "$.llm",
      "Next": "Invoke Outbound Voice Contact"
    },
    "Invoke Outbound Voice Contact": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "TimeoutSeconds": 1800,
      "Parameters": {
        "FunctionName": "${InvokeOutboundCallHandlerArn}",
        "Payload": {"Input.$": "$", "TaskToken.$": "$$.Task.Token"}
      },
      "ResultPath": "$.outboundCall",
      "Next": "Update Lead with Summary"
    },
    "Update Lead with Summary": {
      "Type": "Task",
      "Resource": "${UpdateLeadHandlerArn}",
      "Parameters": {"leadId.$": "$.salesforce.leadId", "summary.$": "$.outboundCall.summary"},
      "ResultPath": "$.summaryResult",
      "End": true
    },
    "Workflow Failed": {
      "Type": "Fail"
    }
  }
}
EOF
    
    echo -e "${GREEN}✓ Workflow definition created${NC}"
}

# Deploy
deploy() {
    echo -e "\n${YELLOW}Deploying Atlas Engine...${NC}"
    
    sam build --parallel
    
    sam deploy \
        --stack-name "AtlasEngine-${ENVIRONMENT}" \
        --region "$REGION" \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
            SalesforceSecretName="$SALESFORCE_SECRET" \
        --capabilities CAPABILITY_IAM \
        --no-fail-on-empty-changeset \
        --resolve-s3
    
    echo -e "${GREEN}✓ Deployment complete${NC}"
}

# Post-deployment
post_deployment() {
    echo -e "\n${YELLOW}Post-deployment steps:${NC}"
    
    STACK_NAME="AtlasEngine-${ENVIRONMENT}"
    LEX_HANDLER=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query "Stacks[0].Outputs[?OutputKey=='LexFulfillmentHandlerArn'].OutputValue" --output text)
    
    echo -e "\n${GREEN}✓ Deployment successful!${NC}"
    echo -e "\n${YELLOW}Manual steps required:${NC}"
    echo "1. Configure Lex bot with fulfillment Lambda: $LEX_HANDLER"
    echo "2. Set up Amazon Connect instance and update stack parameters"
    echo "3. Enable Bedrock model access in your account"
    echo "4. Update Salesforce secret with real credentials"
}

# Main
main() {
    check_prerequisites
    validate_parameters
    check_salesforce_secret
    build_layers
    create_workflow_definition
    deploy
    post_deployment
}

main
