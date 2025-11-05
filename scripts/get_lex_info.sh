#!/bin/bash
# Get Lex Bot and Alias IDs

REGION="us-west-2"

echo "=========================================="
echo "Getting Lex Bot Information"
echo "=========================================="
echo ""

echo "Finding AtlasEngineBot..."
BOT_INFO=$(aws lexv2-models list-bots --region $REGION --output json)

BOT_ID=$(echo $BOT_INFO | jq -r '.botSummaries[] | select(.botName=="AtlasEngineBot") | .botId')

if [ -z "$BOT_ID" ]; then
    echo "✗ Could not find AtlasEngineBot"
    echo ""
    echo "Available bots:"
    echo $BOT_INFO | jq -r '.botSummaries[] | "  - \(.botName) (ID: \(.botId))"'
    exit 1
fi

echo "✓ Found bot: AtlasEngineBot"
echo "  Bot ID: $BOT_ID"
echo ""

echo "Getting bot aliases..."
ALIAS_INFO=$(aws lexv2-models list-bot-aliases --bot-id $BOT_ID --region $REGION --output json)

echo "Available aliases:"
echo $ALIAS_INFO | jq -r '.botAliasSummaries[] | "  - \(.botAliasName) (ID: \(.botAliasId))"'

# Get the first non-TestBotAlias
ALIAS_ID=$(echo $ALIAS_INFO | jq -r '.botAliasSummaries[] | select(.botAliasName!="TestBotAlias") | .botAliasId' | head -1)

if [ -z "$ALIAS_ID" ]; then
    echo ""
    echo "⚠️  No production alias found. Using TestBotAlias..."
    ALIAS_ID=$(echo $ALIAS_INFO | jq -r '.botAliasSummaries[] | select(.botAliasName=="TestBotAlias") | .botAliasId')
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Bot ID: $BOT_ID"
echo "Alias ID: $ALIAS_ID"
echo ""

# Save to file for next script
cat > lex_ids.txt <<EOF
BOT_ID=$BOT_ID
ALIAS_ID=$ALIAS_ID
EOF

echo "✓ Saved to lex_ids.txt"
echo ""
