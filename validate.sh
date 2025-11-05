#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Atlas Engine Pre-Deployment Validation"
echo "=========================================="

ERRORS=0
WARNINGS=0

# Check AWS CLI
if command -v aws &> /dev/null; then
    VERSION=$(aws --version 2>&1 | cut -d' ' -f1 | cut -d'/' -f2)
    echo -e "${GREEN}✓ AWS CLI installed: $VERSION${NC}"
else
    echo -e "${RED}✗ AWS CLI not found${NC}"
    ((ERRORS++))
fi

# Check SAM CLI
if command -v sam &> /dev/null; then
    VERSION=$(sam --version | cut -d' ' -f4)
    echo -e "${GREEN}✓ SAM CLI installed: $VERSION${NC}"
else
    echo -e "${RED}✗ SAM CLI not found${NC}"
    ((ERRORS++))
fi

# Check Python
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python installed: $VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    ((ERRORS++))
fi

# Check AWS credentials
if aws sts get-caller-identity &> /dev/null; then
    ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    echo -e "${GREEN}✓ AWS credentials configured${NC}"
    echo "  Account: $ACCOUNT"
    echo "  Region: $REGION"
else
    echo -e "${RED}✗ AWS credentials not configured${NC}"
    ((ERRORS++))
fi

# Check Bedrock access
echo -e "\n${YELLOW}Checking Bedrock access...${NC}"
if aws bedrock list-foundation-models --region us-west-2 &> /dev/null; then
    MODELS=$(aws bedrock list-foundation-models --region us-west-2 --query "modelSummaries[?contains(modelId, 'claude')].modelId" --output text | wc -w)
    echo -e "${GREEN}✓ Bedrock accessible ($MODELS Claude models)${NC}"
else
    echo -e "${YELLOW}⚠ Bedrock access not verified${NC}"
    ((WARNINGS++))
fi

# Check Salesforce secret
echo -e "\n${YELLOW}Checking Salesforce secret...${NC}"
if aws secretsmanager describe-secret --secret-id AtlasEngine/SalesforceCreds &> /dev/null; then
    echo -e "${GREEN}✓ Salesforce secret exists${NC}"
else
    echo -e "${YELLOW}⚠ Salesforce secret not found (will be created)${NC}"
    ((WARNINGS++))
fi

# Check IAM permissions
echo -e "\n${YELLOW}Checking IAM permissions...${NC}"
REQUIRED_ACTIONS=(
    "lambda:CreateFunction"
    "dynamodb:CreateTable"
    "states:CreateStateMachine"
    "iam:CreateRole"
    "cloudformation:CreateStack"
)

for ACTION in "${REQUIRED_ACTIONS[@]}"; do
    SERVICE=$(echo $ACTION | cut -d':' -f1)
    if aws iam simulate-principal-policy \
        --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
        --action-names $ACTION \
        --query "EvaluationResults[0].EvalDecision" \
        --output text 2>/dev/null | grep -q "allowed"; then
        echo -e "${GREEN}✓ $ACTION${NC}"
    else
        echo -e "${YELLOW}⚠ $ACTION (may require additional permissions)${NC}"
        ((WARNINGS++))
    fi
done

# Check directory structure
echo -e "\n${YELLOW}Checking project structure...${NC}"
REQUIRED_DIRS=("lambda" "sam-template")
for DIR in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$DIR" ]; then
        echo -e "${GREEN}✓ $DIR/ exists${NC}"
    else
        echo -e "${RED}✗ $DIR/ not found${NC}"
        ((ERRORS++))
    fi
done

# Summary
echo -e "\n=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to deploy.${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warnings found. Review before deploying.${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS errors and $WARNINGS warnings found. Fix errors before deploying.${NC}"
    exit 1
fi
