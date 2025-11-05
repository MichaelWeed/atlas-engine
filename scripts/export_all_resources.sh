#!/bin/bash
# AWS Atlas Engine Resource Export Script
EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
REGION="us-west-2"

mkdir -p "$EXPORT_DIR"/{lambda,stepfunctions,dynamodb,s3,cloudformation,lex,connect,iam,secrets,cloudfront,sns,cloudwatch,transcribe}

echo "Starting AWS resource export..."

# Lambda Functions
for func in LexFulfillmentHandler GenerateDynamicScenarioHandler CreateLeadHandler UpdateLeadHandler StartTranscriptionHandler SummarizeAndResumeHandler InvokeOutboundCallHandler InitiateCallHandler; do
  aws lambda get-function --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_config.json" 2>/dev/null
  aws lambda get-function-configuration --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_runtime.json" 2>/dev/null
  aws lambda get-policy --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_policy.json" 2>/dev/null
done

# Step Functions
aws stepfunctions describe-state-machine --state-machine-arn $(aws stepfunctions list-state-machines --region $REGION --query "stateMachines[?name=='AtlasEngineWorkflow'].stateMachineArn" --output text) --region $REGION > "$EXPORT_DIR/stepfunctions/AtlasEngineWorkflow.json" 2>/dev/null

# DynamoDB Tables
for table in AtlasEngineTaskTokens AtlasEngineInteractions; do
  aws dynamodb describe-table --table-name "$table" --region $REGION > "$EXPORT_DIR/dynamodb/${table}_schema.json" 2>/dev/null
  aws dynamodb scan --table-name "$table" --region $REGION > "$EXPORT_DIR/dynamodb/${table}_data.json" 2>/dev/null
done

# S3 Buckets
for bucket in atlasengine-lexwebui-codebuilddeploy--webappbucket-k2kfa9imz0kf atlasengine-lexwebui-code-lexwebuicloudfrontdistri-r189yvixe251 atlasengine-lexwebui-codebuildd-s3serveraccesslogs-ybsdbnzymrrx; do
  aws s3api get-bucket-location --bucket "$bucket" > "$EXPORT_DIR/s3/${bucket}_location.json" 2>/dev/null
  aws s3api get-bucket-policy --bucket "$bucket" > "$EXPORT_DIR/s3/${bucket}_policy.json" 2>/dev/null
  aws s3api get-bucket-versioning --bucket "$bucket" > "$EXPORT_DIR/s3/${bucket}_versioning.json" 2>/dev/null
  aws s3 ls "s3://$bucket" --recursive > "$EXPORT_DIR/s3/${bucket}_contents.txt" 2>/dev/null
done

# CloudFormation Stacks
for stack in AtlasEngine-LexWebUI atlas-engine-dynamodb; do
  aws cloudformation describe-stacks --stack-name "$stack" --region $REGION > "$EXPORT_DIR/cloudformation/${stack}_stack.json" 2>/dev/null
  aws cloudformation get-template --stack-name "$stack" --region $REGION > "$EXPORT_DIR/cloudformation/${stack}_template.json" 2>/dev/null
done

# Lex Bot
aws lexv2-models describe-bot --bot-id M4GK3H6ODQ --region $REGION > "$EXPORT_DIR/lex/AtlasEngineBot.json" 2>/dev/null
aws lexv2-models list-bot-locales --bot-id M4GK3H6ODQ --bot-version DRAFT --region $REGION > "$EXPORT_DIR/lex/AtlasEngineBot_locales.json" 2>/dev/null

# Connect Instance
aws connect describe-instance --instance-id <CONNECT_INSTANCE_ID> --region $REGION > "$EXPORT_DIR/connect/intrepidlyintrepid.json" 2>/dev/null
aws connect list-contact-flows --instance-id <CONNECT_INSTANCE_ID> --region $REGION > "$EXPORT_DIR/connect/contact_flows.json" 2>/dev/null

# IAM Roles
for role in StepFunctions-AtlasEngineWorkflow-role-46ivk0793 LexFulfillmentHandler-role-gf8r6bq2 CreateLeadHandler-role-sduo9h9n StartTranscriptionHandler-role-k0h94r1f GenerateDynamicScenarioHandler-role-vbv9ftg1 SummarizeAndResumeHandler-role-ogn1ngtx InvokeOutboundCallHandler-role-p7ou5zno InitiateCallHandler-role-iwcl0yhb; do
  aws iam get-role --role-name "$role" > "$EXPORT_DIR/iam/${role}.json" 2>/dev/null
  aws iam list-attached-role-policies --role-name "$role" > "$EXPORT_DIR/iam/${role}_policies.json" 2>/dev/null
  aws iam list-role-policies --role-name "$role" > "$EXPORT_DIR/iam/${role}_inline_policies.json" 2>/dev/null
done

# Secrets Manager
aws secretsmanager describe-secret --secret-id AtlasEngine/SalesforceCreds --region $REGION > "$EXPORT_DIR/secrets/SalesforceCreds_metadata.json" 2>/dev/null

# CloudFront Distributions
for dist in E3785MV35RHIXR E2I21H2PCFYG9J; do
  aws cloudfront get-distribution --id "$dist" > "$EXPORT_DIR/cloudfront/${dist}.json" 2>/dev/null
  aws cloudfront get-distribution-config --id "$dist" > "$EXPORT_DIR/cloudfront/${dist}_config.json" 2>/dev/null
done

# SNS Topics
aws sns get-topic-attributes --topic-arn $(aws sns list-topics --region $REGION --query "Topics[?contains(TopicArn, 'SmsQuickStartSnsDestination-d9558817')].TopicArn" --output text) --region $REGION > "$EXPORT_DIR/sns/SmsQuickStartSnsDestination.json" 2>/dev/null

# CloudWatch Log Groups
for func in LexFulfillmentHandler GenerateDynamicScenarioHandler CreateLeadHandler UpdateLeadHandler StartTranscriptionHandler SummarizeAndResumeHandler InvokeOutboundCallHandler InitiateCallHandler; do
  aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/$func" --region $REGION > "$EXPORT_DIR/cloudwatch/${func}_loggroup.json" 2>/dev/null
done

# Transcribe Jobs
aws transcribe list-transcription-jobs --max-results 10 --region $REGION > "$EXPORT_DIR/transcribe/recent_jobs.json" 2>/dev/null

echo "Export complete! Files saved to: $EXPORT_DIR"
