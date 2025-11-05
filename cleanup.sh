#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🗑️  Atlas Engine Cleanup Script"
echo "==============================="

if [ -z "$1" ]; then
    read -p "Environment to delete (dev/staging/prod): " ENVIRONMENT
else
    ENVIRONMENT=$1
fi

STACK_NAME="AtlasEngine-${ENVIRONMENT}"
REGION=$(aws configure get region)

echo -e "\n${RED}⚠️  WARNING: This will delete all resources in stack: $STACK_NAME${NC}"
read -p "Type 'DELETE' to confirm: " CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
    echo "Aborted"
    exit 0
fi

echo -e "\n${YELLOW}Emptying S3 buckets...${NC}"
BUCKETS=$(aws cloudformation describe-stack-resources --stack-name "$STACK_NAME" --region "$REGION" --query "StackResources[?ResourceType=='AWS::S3::Bucket'].PhysicalResourceId" --output text 2>/dev/null || echo "")
for BUCKET in $BUCKETS; do
    aws s3 rm s3://$BUCKET --recursive 2>/dev/null || true
done

echo -e "\n${YELLOW}Deleting CloudFormation stack...${NC}"
aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$REGION"

echo -e "\n${YELLOW}Waiting for deletion...${NC}"
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME" --region "$REGION"

echo -e "\n${GREEN}✓ Cleanup complete${NC}"
