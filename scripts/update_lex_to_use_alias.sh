#!/bin/bash
# Update Lex bot to use Lambda alias

set -e

REGION="us-west-2"

# Load bot IDs from previous script
if [ ! -f lex_ids.txt ]; then
    echo "✗ lex_ids.txt not found. Run ./get_lex_info.sh first"
    exit 1
fi

source lex_ids.txt

echo "=========================================="
echo "Updating Lex Bot to use Lambda Alias"
echo "=========================================="
echo ""
echo "Bot ID: $BOT_ID"
echo "Alias ID: $ALIAS_ID"
echo ""

# Get Lambda alias ARN
LAMBDA_ARN=$(aws lambda get-alias \
    --function-name LexFulfillmentHandler \
    --name prod \
    --region $REGION \
    --query 'AliasArn' \
    --output text)

echo "Lambda Alias ARN: $LAMBDA_ARN"
echo ""

# Update the bot alias
echo "Updating bot alias configuration..."
aws lexv2-models update-bot-alias \
    --bot-id $BOT_ID \
    --bot-alias-id $ALIAS_ID \
    --bot-alias-name PROD \
    --bot-alias-locale-settings file://lex_alias_config.json \
    --region $REGION

echo ""
echo "✓ Lex bot updated successfully!"
echo ""
echo "The bot will now use the Lambda alias with provisioned concurrency."
echo "Cold starts should be eliminated."
echo ""
