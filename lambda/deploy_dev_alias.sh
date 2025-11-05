#!/bin/bash

# Deploy Dev Alias with X-Ray Tracing for Atlas Engine Lambda Functions
# Region: us-west-2

set -e

REGION="us-west-2"
ALIAS_NAME="Dev"

echo "=========================================="
echo "Atlas Engine Dev Alias Deployment Script"
echo "=========================================="
echo ""

# Function 1: LexFulfillmentHandler
echo "[1/4] Deploying LexFulfillmentHandler..."
cd LexFulfillmentHandler_code
cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip3 install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/
aws lambda update-function-code \
  --function-name LexFulfillmentHandler \
  --zip-file fileb://function_dev.zip \
  --region $REGION
aws lambda wait function-updated --function-name LexFulfillmentHandler --region $REGION
VERSION_LFH=$(aws lambda publish-version --function-name LexFulfillmentHandler --region $REGION --query 'Version' --output text)
echo "Published version: $VERSION_LFH"
aws lambda create-alias \
  --function-name LexFulfillmentHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_LFH \
  --region $REGION || \
aws lambda update-alias \
  --function-name LexFulfillmentHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_LFH \
  --region $REGION
aws lambda update-function-configuration \
  --function-name LexFulfillmentHandler \
  --tracing-config Mode=Active \
  --region $REGION
echo "✓ LexFulfillmentHandler deployed with Dev alias pointing to version $VERSION_LFH"
cd ..

# Function 2: GenerateDynamicScenarioHandler
echo ""
echo "[2/4] Deploying GenerateDynamicScenarioHandler..."
cd GenerateDynamicScenarioHandler_code
cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip3 install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/
aws lambda update-function-code \
  --function-name GenerateDynamicScenarioHandler \
  --zip-file fileb://function_dev.zip \
  --region $REGION
aws lambda wait function-updated --function-name GenerateDynamicScenarioHandler --region $REGION
VERSION_GDSH=$(aws lambda publish-version --function-name GenerateDynamicScenarioHandler --region $REGION --query 'Version' --output text)
echo "Published version: $VERSION_GDSH"
aws lambda create-alias \
  --function-name GenerateDynamicScenarioHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_GDSH \
  --region $REGION || \
aws lambda update-alias \
  --function-name GenerateDynamicScenarioHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_GDSH \
  --region $REGION
aws lambda update-function-configuration \
  --function-name GenerateDynamicScenarioHandler \
  --tracing-config Mode=Active \
  --region $REGION
echo "✓ GenerateDynamicScenarioHandler deployed with Dev alias pointing to version $VERSION_GDSH"
cd ..

# Function 3: InvokeOutboundCallHandler
echo ""
echo "[3/4] Deploying InvokeOutboundCallHandler..."
cd InvokeOutboundCallHandler_code
cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip3 install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/
aws lambda update-function-code \
  --function-name InvokeOutboundCallHandler \
  --zip-file fileb://function_dev.zip \
  --region $REGION
aws lambda wait function-updated --function-name InvokeOutboundCallHandler --region $REGION
VERSION_IOCH=$(aws lambda publish-version --function-name InvokeOutboundCallHandler --region $REGION --query 'Version' --output text)
echo "Published version: $VERSION_IOCH"
aws lambda create-alias \
  --function-name InvokeOutboundCallHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_IOCH \
  --region $REGION || \
aws lambda update-alias \
  --function-name InvokeOutboundCallHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_IOCH \
  --region $REGION
aws lambda update-function-configuration \
  --function-name InvokeOutboundCallHandler \
  --tracing-config Mode=Active \
  --region $REGION
echo "✓ InvokeOutboundCallHandler deployed with Dev alias pointing to version $VERSION_IOCH"
cd ..

# Function 4: UpdateLeadHandler
echo ""
echo "[4/4] Deploying UpdateLeadHandler..."
cd UpdateLeadHandler_code
cp lambda_function_dev.py lambda_function.py
zip -r function_dev.zip lambda_function.py
pip3 install -r ../requirements_xray.txt -t .
zip -r function_dev.zip aws_xray_sdk/
aws lambda update-function-code \
  --function-name UpdateLeadHandler \
  --zip-file fileb://function_dev.zip \
  --region $REGION
aws lambda wait function-updated --function-name UpdateLeadHandler --region $REGION
VERSION_ULH=$(aws lambda publish-version --function-name UpdateLeadHandler --region $REGION --query 'Version' --output text)
echo "Published version: $VERSION_ULH"
aws lambda create-alias \
  --function-name UpdateLeadHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_ULH \
  --region $REGION || \
aws lambda update-alias \
  --function-name UpdateLeadHandler \
  --name $ALIAS_NAME \
  --function-version $VERSION_ULH \
  --region $REGION
aws lambda update-function-configuration \
  --function-name UpdateLeadHandler \
  --tracing-config Mode=Active \
  --region $REGION
echo "✓ UpdateLeadHandler deployed with Dev alias pointing to version $VERSION_ULH"
cd ..

echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo "LexFulfillmentHandler:Dev -> v$VERSION_LFH"
echo "GenerateDynamicScenarioHandler:Dev -> v$VERSION_GDSH"
echo "InvokeOutboundCallHandler:Dev -> v$VERSION_IOCH"
echo "UpdateLeadHandler:Dev -> v$VERSION_ULH"
echo ""
echo "All functions have Active X-Ray tracing enabled."
echo ""
echo "Next Steps:"
echo "1. Update IAM roles with X-Ray permissions (see iam_xray_policy.json)"
echo "2. Enable X-Ray tracing on AtlasEngineWorkflow Step Function"
echo "3. Update Step Function to use :Dev aliases"
echo "=========================================="
