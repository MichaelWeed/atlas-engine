#!/bin/bash
EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
REGION="us-west-2"

echo "Refreshing updated resources..."

# Lambda Functions
echo "Re-exporting Lambda functions..."
for func in LexFulfillmentHandler GenerateDynamicScenarioHandler CreateLeadHandler UpdateLeadHandler StartTranscriptionHandler SummarizeAndResumeHandler InvokeOutboundCallHandler InitiateCallHandler; do
  aws lambda get-function --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_config.json" 2>/dev/null
  aws lambda get-function-configuration --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_runtime.json" 2>/dev/null
  aws lambda get-policy --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_policy.json" 2>/dev/null
done

# Step Functions
echo "Re-exporting Step Functions..."
aws stepfunctions describe-state-machine --state-machine-arn $(aws stepfunctions list-state-machines --region $REGION --query "stateMachines[?name=='AtlasEngineWorkflow'].stateMachineArn" --output text) --region $REGION > "$EXPORT_DIR/stepfunctions/AtlasEngineWorkflow.json" 2>/dev/null

# IAM Roles
echo "Re-exporting IAM roles..."
for role in StepFunctions-AtlasEngineWorkflow-role-46ivk0793 LexFulfillmentHandler-role-gf8r6bq2 CreateLeadHandler-role-sduo9h9n StartTranscriptionHandler-role-k0h94r1f GenerateDynamicScenarioHandler-role-vbv9ftg1 SummarizeAndResumeHandler-role-ogn1ngtx InvokeOutboundCallHandler-role-p7ou5zno InitiateCallHandler-role-iwcl0yhb; do
  aws iam get-role --role-name "$role" > "$EXPORT_DIR/iam/${role}.json" 2>/dev/null
  aws iam list-attached-role-policies --role-name "$role" > "$EXPORT_DIR/iam/${role}_policies.json" 2>/dev/null
  aws iam list-role-policies --role-name "$role" > "$EXPORT_DIR/iam/${role}_inline_policies.json" 2>/dev/null
done

# EventBridge
echo "Exporting EventBridge rules..."
mkdir -p "$EXPORT_DIR/eventbridge"
aws events list-rules --region $REGION > "$EXPORT_DIR/eventbridge/rules_list.json" 2>/dev/null
aws events list-rules --region $REGION --query 'Rules[*].Name' --output text | tr '\t' '\n' | while read rule; do
  [ -n "$rule" ] && aws events describe-rule --name "$rule" --region $REGION > "$EXPORT_DIR/eventbridge/${rule}.json" 2>/dev/null
done

echo "Refresh complete!"
