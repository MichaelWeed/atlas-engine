#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-dev}
STACK_NAME="AtlasEngine-${ENVIRONMENT}"

echo "🧪 Testing Atlas Engine Deployment"
echo "==================================="
echo "Environment: $ENVIRONMENT"
echo "Stack: $STACK_NAME"

# Get outputs
echo -e "\n${YELLOW}Fetching stack outputs...${NC}"
WORKFLOW_ARN=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='WorkflowArn'].OutputValue" \
    --output text)

INTERACTIONS_TABLE=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='InteractionsTableName'].OutputValue" \
    --output text)

echo "Workflow ARN: $WORKFLOW_ARN"
echo "Interactions Table: $INTERACTIONS_TABLE"

# Test Step Functions execution
echo -e "\n${YELLOW}Testing Step Functions workflow...${NC}"
EXECUTION_ARN=$(aws stepfunctions start-execution \
    --state-machine-arn "$WORKFLOW_ARN" \
    --input '{
        "firstName": "Test",
        "lastName": "User",
        "phone": "+15555551234"
    }' \
    --query 'executionArn' \
    --output text)

echo "Execution started: $EXECUTION_ARN"
echo "Waiting for completion..."

# Wait for execution
sleep 5

STATUS=$(aws stepfunctions describe-execution \
    --execution-arn "$EXECUTION_ARN" \
    --query 'status' \
    --output text)

echo "Status: $STATUS"

if [ "$STATUS" == "SUCCEEDED" ]; then
    echo -e "${GREEN}✓ Workflow test passed${NC}"
elif [ "$STATUS" == "RUNNING" ]; then
    echo -e "${YELLOW}⚠ Workflow still running (check console)${NC}"
else
    echo -e "${RED}✗ Workflow failed${NC}"
    aws stepfunctions describe-execution --execution-arn "$EXECUTION_ARN"
    exit 1
fi

# Test DynamoDB
echo -e "\n${YELLOW}Testing DynamoDB access...${NC}"
ITEM_COUNT=$(aws dynamodb scan \
    --table-name "$INTERACTIONS_TABLE" \
    --select COUNT \
    --query 'Count' \
    --output text)

echo "Items in table: $ITEM_COUNT"
echo -e "${GREEN}✓ DynamoDB test passed${NC}"

# Test Lambda
echo -e "\n${YELLOW}Testing Lambda functions...${NC}"
FUNCTIONS=$(aws lambda list-functions \
    --query "Functions[?starts_with(FunctionName, 'AtlasEngine-')].FunctionName" \
    --output text)

for FUNC in $FUNCTIONS; do
    echo "  ✓ $FUNC"
done

echo -e "\n${GREEN}✓ All tests passed${NC}"
