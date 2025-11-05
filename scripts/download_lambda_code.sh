#!/bin/bash
EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
REGION="us-west-2"

echo "Downloading Lambda function code..."

for func in LexFulfillmentHandler GenerateDynamicScenarioHandler CreateLeadHandler UpdateLeadHandler StartTranscriptionHandler SummarizeAndResumeHandler InvokeOutboundCallHandler InitiateCallHandler; do
  echo "Downloading $func..."
  CODE_URL=$(aws lambda get-function --function-name "$func" --region $REGION --query 'Code.Location' --output text)
  curl -s "$CODE_URL" -o "$EXPORT_DIR/lambda/${func}_code.zip"
  unzip -q "$EXPORT_DIR/lambda/${func}_code.zip" -d "$EXPORT_DIR/lambda/${func}_code"
  rm "$EXPORT_DIR/lambda/${func}_code.zip"
done

echo "Lambda code download complete!"
