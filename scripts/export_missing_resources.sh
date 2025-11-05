#!/bin/bash

# Export Missing Resources for Atlas Engine Project
# This script exports Lambda layers, SQS queues, missing IAM roles, and other resources

set -e

EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
REGION="us-west-2"

echo "=========================================="
echo "Exporting Missing Atlas Engine Resources"
echo "=========================================="

# Create directories
mkdir -p "$EXPORT_DIR/lambda_layers"
mkdir -p "$EXPORT_DIR/sqs"

# ============================================================================
# 1. EXPORT LAMBDA LAYERS
# ============================================================================
echo ""
echo "1. Exporting Lambda Layers..."

LAYERS=(
    "LexBotDependencies-v4-FIXED"
    "PythonLibraries-Minimal-v6"
    "RequestsAndSalesforceLibrary"
    "RequestsLibrary"
    "SalesforceDependenciesLayer"
    "SimpleSalesforceLibrary"
    "phonenumbers"
)

for LAYER_NAME in "${LAYERS[@]}"; do
    echo "  - Exporting layer: $LAYER_NAME"
    
    # Get latest version
    LAYER_INFO=$(aws lambda list-layer-versions --layer-name "$LAYER_NAME" --region "$REGION" --max-items 1 --output json)
    echo "$LAYER_INFO" > "$EXPORT_DIR/lambda_layers/${LAYER_NAME}_versions.json"
    
    # Get layer version ARN
    LAYER_VERSION_ARN=$(echo "$LAYER_INFO" | jq -r '.LayerVersions[0].LayerVersionArn')
    
    if [ "$LAYER_VERSION_ARN" != "null" ]; then
        # Get detailed layer version info
        aws lambda get-layer-version-by-arn --arn "$LAYER_VERSION_ARN" --region "$REGION" --output json > "$EXPORT_DIR/lambda_layers/${LAYER_NAME}_details.json"
        echo "    ✓ Exported $LAYER_NAME"
    fi
done

# ============================================================================
# 2. EXPORT SQS QUEUES
# ============================================================================
echo ""
echo "2. Exporting SQS Queues..."

QUEUE_URLS=$(aws sqs list-queues --region "$REGION" --output json | jq -r '.QueueUrls[]?')

if [ -n "$QUEUE_URLS" ]; then
    while IFS= read -r QUEUE_URL; do
        QUEUE_NAME=$(basename "$QUEUE_URL")
        echo "  - Exporting queue: $QUEUE_NAME"
        
        # Get queue attributes
        aws sqs get-queue-attributes --queue-url "$QUEUE_URL" --attribute-names All --region "$REGION" --output json > "$EXPORT_DIR/sqs/${QUEUE_NAME}_attributes.json"
        
        # Get queue URL info
        echo "{\"QueueUrl\": \"$QUEUE_URL\", \"QueueName\": \"$QUEUE_NAME\"}" > "$EXPORT_DIR/sqs/${QUEUE_NAME}_info.json"
        
        echo "    ✓ Exported $QUEUE_NAME"
    done <<< "$QUEUE_URLS"
else
    echo "  No SQS queues found"
fi

# ============================================================================
# 3. EXPORT MISSING IAM ROLE (UpdateLeadHandler)
# ============================================================================
echo ""
echo "3. Exporting Missing IAM Roles..."

# Get UpdateLeadHandler role name from Lambda config
UPDATE_LEAD_ROLE=$(aws lambda get-function --function-name UpdateLeadHandler --region "$REGION" --output json | jq -r '.Configuration.Role' | awk -F'/' '{print $NF}')

if [ -n "$UPDATE_LEAD_ROLE" ] && [ "$UPDATE_LEAD_ROLE" != "null" ]; then
    echo "  - Exporting role: $UPDATE_LEAD_ROLE"
    
    # Export role
    aws iam get-role --role-name "$UPDATE_LEAD_ROLE" --output json > "$EXPORT_DIR/iam/${UPDATE_LEAD_ROLE}.json"
    
    # Export attached policies
    aws iam list-attached-role-policies --role-name "$UPDATE_LEAD_ROLE" --output json > "$EXPORT_DIR/iam/${UPDATE_LEAD_ROLE}_policies.json"
    
    # Export inline policies
    aws iam list-role-policies --role-name "$UPDATE_LEAD_ROLE" --output json > "$EXPORT_DIR/iam/${UPDATE_LEAD_ROLE}_inline_policies.json"
    
    # Export each inline policy document
    INLINE_POLICIES=$(aws iam list-role-policies --role-name "$UPDATE_LEAD_ROLE" --output json | jq -r '.PolicyNames[]?')
    if [ -n "$INLINE_POLICIES" ]; then
        while IFS= read -r POLICY_NAME; do
            aws iam get-role-policy --role-name "$UPDATE_LEAD_ROLE" --policy-name "$POLICY_NAME" --output json > "$EXPORT_DIR/iam/${UPDATE_LEAD_ROLE}_inline_${POLICY_NAME}.json"
        done <<< "$INLINE_POLICIES"
    fi
    
    echo "    ✓ Exported $UPDATE_LEAD_ROLE"
fi

# ============================================================================
# 4. RE-EXPORT ALL LAMBDA FUNCTIONS (FRESH PULL)
# ============================================================================
echo ""
echo "4. Re-exporting All Lambda Functions..."

LAMBDA_FUNCTIONS=(
    "CreateLeadHandler"
    "GenerateDynamicScenarioHandler"
    "InitiateCallHandler"
    "InvokeOutboundCallHandler"
    "LexFulfillmentHandler"
    "StartTranscriptionHandler"
    "SummarizeAndResumeHandler"
    "UpdateLeadHandler"
)

for FUNCTION_NAME in "${LAMBDA_FUNCTIONS[@]}"; do
    echo "  - Re-exporting: $FUNCTION_NAME"
    
    # Export function configuration
    aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --output json > "$EXPORT_DIR/lambda/${FUNCTION_NAME}_config.json"
    
    # Export function code
    CODE_DIR="$EXPORT_DIR/lambda/${FUNCTION_NAME}_code"
    rm -rf "$CODE_DIR"
    mkdir -p "$CODE_DIR"
    
    # Get code location
    CODE_LOCATION=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --output json | jq -r '.Code.Location')
    
    # Download and extract code
    curl -s "$CODE_LOCATION" -o "$CODE_DIR/function.zip"
    unzip -q -o "$CODE_DIR/function.zip" -d "$CODE_DIR"
    rm "$CODE_DIR/function.zip"
    
    # Export function policy
    aws lambda get-policy --function-name "$FUNCTION_NAME" --region "$REGION" --output json > "$EXPORT_DIR/lambda/${FUNCTION_NAME}_policy.json" 2>/dev/null || echo "{\"Policy\": \"No resource policy\"}" > "$EXPORT_DIR/lambda/${FUNCTION_NAME}_policy.json"
    
    echo "    ✓ Re-exported $FUNCTION_NAME"
done

# ============================================================================
# 5. RE-EXPORT STEP FUNCTIONS
# ============================================================================
echo ""
echo "5. Re-exporting Step Functions..."

STATE_MACHINE_ARN="arn:aws:states:us-west-2:<AWS_ACCOUNT_ID>:stateMachine:AtlasEngineWorkflow"

echo "  - Re-exporting: AtlasEngineWorkflow"
aws stepfunctions describe-state-machine --state-machine-arn "$STATE_MACHINE_ARN" --region "$REGION" --output json > "$EXPORT_DIR/stepfunctions/AtlasEngineWorkflow.json"

# Export execution history (last 10 executions)
aws stepfunctions list-executions --state-machine-arn "$STATE_MACHINE_ARN" --max-results 10 --region "$REGION" --output json > "$EXPORT_DIR/stepfunctions/AtlasEngineWorkflow_executions.json"

echo "    ✓ Re-exported AtlasEngineWorkflow"

# ============================================================================
# 6. EXPORT CLOUDWATCH LOG GROUPS (STEP FUNCTIONS)
# ============================================================================
echo ""
echo "6. Exporting CloudWatch Log Groups for Step Functions..."

SF_LOG_GROUP="/aws/vendedlogs/states/AtlasEngineWorkflow-Logs"

if aws logs describe-log-groups --log-group-name-prefix "$SF_LOG_GROUP" --region "$REGION" --output json | jq -e '.logGroups | length > 0' > /dev/null 2>&1; then
    echo "  - Exporting log group: $SF_LOG_GROUP"
    aws logs describe-log-groups --log-group-name-prefix "$SF_LOG_GROUP" --region "$REGION" --output json > "$EXPORT_DIR/cloudwatch/AtlasEngineWorkflow_loggroup.json"
    echo "    ✓ Exported Step Functions log group"
else
    echo "  No Step Functions log group found"
fi

# ============================================================================
# 7. EXPORT CONNECT INSTANCE DETAILS
# ============================================================================
echo ""
echo "7. Exporting Amazon Connect Details..."

# Get Connect instance ID from the exported data
CONNECT_INSTANCE_ID=$(jq -r '.Instance.Id // empty' "$EXPORT_DIR/connect/intrepidlyintrepid.json" 2>/dev/null)

if [ -n "$CONNECT_INSTANCE_ID" ]; then
    echo "  - Exporting Connect instance: $CONNECT_INSTANCE_ID"
    
    # Export phone numbers
    aws connect list-phone-numbers-v2 --target-arn "arn:aws:connect:us-west-2:<AWS_ACCOUNT_ID>:instance/$CONNECT_INSTANCE_ID" --region "$REGION" --output json > "$EXPORT_DIR/connect/phone_numbers.json" 2>/dev/null || echo "[]" > "$EXPORT_DIR/connect/phone_numbers.json"
    
    # Export hours of operation
    aws connect list-hours-of-operations --instance-id "$CONNECT_INSTANCE_ID" --region "$REGION" --output json > "$EXPORT_DIR/connect/hours_of_operations.json" 2>/dev/null || echo "[]" > "$EXPORT_DIR/connect/hours_of_operations.json"
    
    # Export queues
    aws connect list-queues --instance-id "$CONNECT_INSTANCE_ID" --region "$REGION" --output json > "$EXPORT_DIR/connect/queues.json" 2>/dev/null || echo "[]" > "$EXPORT_DIR/connect/queues.json"
    
    echo "    ✓ Exported Connect details"
else
    echo "  Connect instance ID not found"
fi

# ============================================================================
# 8. EXPORT SECRETS MANAGER METADATA
# ============================================================================
echo ""
echo "8. Re-exporting Secrets Manager Metadata..."

SECRET_ARN="arn:aws:secretsmanager:us-west-2:<AWS_ACCOUNT_ID>:secret:AtlasEngine/SalesforceCreds-4xWYp9"

echo "  - Re-exporting: SalesforceCreds"
aws secretsmanager describe-secret --secret-id "$SECRET_ARN" --region "$REGION" --output json > "$EXPORT_DIR/secrets/SalesforceCreds_metadata.json"
echo "    ✓ Re-exported SalesforceCreds metadata"

# ============================================================================
# SUMMARY
# ============================================================================
echo ""
echo "=========================================="
echo "Export Complete!"
echo "=========================================="
echo ""
echo "Exported Resources:"
echo "  ✓ 7 Lambda Layers"
echo "  ✓ SQS Queues"
echo "  ✓ Missing IAM Roles"
echo "  ✓ 8 Lambda Functions (fresh pull)"
echo "  ✓ Step Functions State Machine"
echo "  ✓ CloudWatch Log Groups"
echo "  ✓ Amazon Connect Details"
echo "  ✓ Secrets Manager Metadata"
echo ""
echo "Export directory: $EXPORT_DIR"
echo ""
