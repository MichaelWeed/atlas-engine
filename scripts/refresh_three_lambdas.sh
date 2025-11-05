#!/bin/bash
REGION="us-west-2"
EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"

for func in SummarizeAndResumeHandler GenerateDynamicScenarioHandler LexFulfillmentHandler; do
  echo "Re-downloading $func..."
  rm -rf "$EXPORT_DIR/lambda/${func}_code"
  CODE_URL=$(aws lambda get-function --function-name "$func" --region $REGION --query 'Code.Location' --output text)
  curl -s "$CODE_URL" -o "$EXPORT_DIR/lambda/${func}_code.zip"
  unzip -q "$EXPORT_DIR/lambda/${func}_code.zip" -d "$EXPORT_DIR/lambda/${func}_code"
  rm "$EXPORT_DIR/lambda/${func}_code.zip"
  aws lambda get-function --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_config.json"
  aws lambda get-function-configuration --function-name "$func" --region $REGION > "$EXPORT_DIR/lambda/${func}_runtime.json"
done

echo "Updated Lambda functions re-downloaded!"
