#!/bin/bash

EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
cd "$EXPORT_DIR"

POLICIES=("AtlasEngineCorePolicy" "AtlasEngineLoggingPolicy" "AtlasEngineSecretsPolicy" "ScopedBedrockInvokePolicy")

for POLICY_NAME in "${POLICIES[@]}"; do
    echo "Exporting policy: $POLICY_NAME"
    
    POLICY_ARN=$(aws iam list-policies --scope Local --output json | jq -r ".Policies[] | select(.PolicyName == \"$POLICY_NAME\") | .Arn")
    
    if [ -n "$POLICY_ARN" ] && [ "$POLICY_ARN" != "null" ]; then
        aws iam get-policy --policy-arn "$POLICY_ARN" --output json > "iam/${POLICY_NAME}_policy.json"
        
        VERSION_ID=$(aws iam get-policy --policy-arn "$POLICY_ARN" --output json | jq -r '.Policy.DefaultVersionId')
        aws iam get-policy-version --policy-arn "$POLICY_ARN" --version-id "$VERSION_ID" --output json > "iam/${POLICY_NAME}_document.json"
        
        echo "  ✓ Exported $POLICY_NAME"
    else
        echo "  ✗ Policy not found: $POLICY_NAME"
    fi
done
