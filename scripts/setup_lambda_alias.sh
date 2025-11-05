#!/bin/bash
# Setup Lambda Alias and Provisioned Concurrency for LexFulfillmentHandler

set -e  # Exit on error

REGION="us-west-2"
FUNCTION_NAME="LexFulfillmentHandler"
ALIAS_NAME="prod"
VERSION="28"

echo "=========================================="
echo "Setting up Lambda Alias for $FUNCTION_NAME"
echo "=========================================="

# Step 1: Check if alias already exists
echo ""
echo "Step 1: Checking if alias '$ALIAS_NAME' exists..."
if aws lambda get-alias --function-name $FUNCTION_NAME --name $ALIAS_NAME --region $REGION 2>/dev/null; then
    echo "✓ Alias '$ALIAS_NAME' already exists. Updating it..."
    aws lambda update-alias \
        --function-name $FUNCTION_NAME \
        --name $ALIAS_NAME \
        --function-version $VERSION \
        --region $REGION
    echo "✓ Alias updated to point to version $VERSION"
else
    echo "✗ Alias '$ALIAS_NAME' does not exist. Creating it..."
    aws lambda create-alias \
        --function-name $FUNCTION_NAME \
        --name $ALIAS_NAME \
        --function-version $VERSION \
        --description "Production alias for Lex integration" \
        --region $REGION
    echo "✓ Alias created and pointing to version $VERSION"
fi

# Step 2: Move provisioned concurrency from version to alias
echo ""
echo "Step 2: Checking provisioned concurrency..."

# Check if version 28 has provisioned concurrency
if aws lambda get-provisioned-concurrency-config \
    --function-name $FUNCTION_NAME \
    --qualifier $VERSION \
    --region $REGION 2>/dev/null; then
    echo "⚠️  Version $VERSION has provisioned concurrency. Removing it..."
    aws lambda delete-provisioned-concurrency-config \
        --function-name $FUNCTION_NAME \
        --qualifier $VERSION \
        --region $REGION
    echo "✓ Removed provisioned concurrency from version $VERSION"
    echo "⏳ Waiting 10 seconds for cleanup..."
    sleep 10
fi

# Now configure on alias
if aws lambda get-provisioned-concurrency-config \
    --function-name $FUNCTION_NAME \
    --qualifier $ALIAS_NAME \
    --region $REGION 2>/dev/null; then
    echo "✓ Provisioned concurrency already configured on alias"
else
    echo "Setting up provisioned concurrency on alias (1 instance)..."
    aws lambda put-provisioned-concurrency-config \
        --function-name $FUNCTION_NAME \
        --qualifier $ALIAS_NAME \
        --provisioned-concurrent-executions 1 \
        --region $REGION
    echo "✓ Provisioned concurrency configured"
    echo "⏳ Waiting for provisioned concurrency to be ready (this takes 2-3 minutes)..."
    
    # Wait for it to be ready
    for i in {1..36}; do
        STATUS=$(aws lambda get-provisioned-concurrency-config \
            --function-name $FUNCTION_NAME \
            --qualifier $ALIAS_NAME \
            --region $REGION \
            --query 'Status' \
            --output text)
        
        if [ "$STATUS" = "READY" ]; then
            echo "✓ Provisioned concurrency is READY!"
            break
        fi
        echo "   Status: $STATUS (attempt $i/36)"
        sleep 5
    done
fi

# Step 3: Get the alias ARN
echo ""
echo "Step 3: Getting alias ARN..."
ALIAS_ARN=$(aws lambda get-alias \
    --function-name $FUNCTION_NAME \
    --name $ALIAS_NAME \
    --region $REGION \
    --query 'AliasArn' \
    --output text)

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Alias ARN: $ALIAS_ARN"
echo ""
echo "NEXT STEP: Update your Lex bot to use this ARN"
echo ""
echo "Option 1 - AWS Console:"
echo "  1. Go to Amazon Lex console"
echo "  2. Select your bot: AtlasEngineBot"
echo "  3. Go to Aliases → Select your alias"
echo "  4. Under Languages → English (US) → Lambda function"
echo "  5. Change ARN to: $ALIAS_ARN"
echo "  6. Save"
echo ""
echo "Option 2 - AWS CLI (run this command):"
echo "  aws lexv2-models update-bot-alias \\"
echo "    --bot-id <YOUR_BOT_ID> \\"
echo "    --bot-alias-id <YOUR_ALIAS_ID> \\"
echo "    --bot-alias-locale-settings file://lex_alias_config.json \\"
echo "    --region $REGION"
echo ""
echo "I'll create the lex_alias_config.json file for you..."

# Create Lex config file
cat > lex_alias_config.json <<EOF
{
  "en_US": {
    "enabled": true,
    "codeHookSpecification": {
      "lambdaCodeHook": {
        "lambdaARN": "$ALIAS_ARN",
        "codeHookInterfaceVersion": "1.0"
      }
    }
  }
}
EOF

echo "✓ Created lex_alias_config.json"
echo ""
echo "To get your bot ID and alias ID, run:"
echo "  aws lexv2-models list-bots --region $REGION"
echo "  aws lexv2-models list-bot-aliases --bot-id <BOT_ID> --region $REGION"
echo ""
