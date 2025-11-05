#!/bin/bash
set -e

echo "=========================================="
echo "Atlas Engine - S3 Publishing Script"
echo "=========================================="
echo ""

# Check if bucket name provided
if [ -z "$1" ]; then
    echo "Usage: ./publish-to-s3.sh <bucket-name> [region]"
    echo ""
    echo "Example:"
    echo "  ./publish-to-s3.sh my-atlas-templates us-west-2"
    echo ""
    exit 1
fi

BUCKET_NAME=$1
REGION=${2:-us-west-2}
TEMPLATE_FILE="sam-template/template.yaml"
PACKAGED_TEMPLATE="packaged-template.yaml"
S3_PREFIX="atlas-engine"

echo "Configuration:"
echo "  Bucket: $BUCKET_NAME"
echo "  Region: $REGION"
echo "  Template: $TEMPLATE_FILE"
echo ""

# Check if bucket exists, create if not
echo "Checking S3 bucket..."
if ! aws s3 ls "s3://$BUCKET_NAME" --region $REGION 2>/dev/null; then
    echo "Creating bucket $BUCKET_NAME..."
    if [ "$REGION" = "us-east-1" ]; then
        aws s3 mb "s3://$BUCKET_NAME"
    else
        aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION --create-bucket-configuration LocationConstraint=$REGION
    fi
else
    echo "Bucket exists ✓"
fi

# Build Lambda layers
echo ""
echo "Building Lambda layers..."
./build-layers.sh

# Package SAM template
echo ""
echo "Packaging SAM template..."
sam package \
    --template-file $TEMPLATE_FILE \
    --output-template-file $PACKAGED_TEMPLATE \
    --s3-bucket $BUCKET_NAME \
    --s3-prefix $S3_PREFIX \
    --region $REGION

# Upload packaged template
echo ""
echo "Uploading template to S3..."
aws s3 cp $PACKAGED_TEMPLATE "s3://$BUCKET_NAME/$S3_PREFIX/$PACKAGED_TEMPLATE" \
    --region $REGION \
    --acl public-read

# Get template URL
TEMPLATE_URL="https://$BUCKET_NAME.s3.$REGION.amazonaws.com/$S3_PREFIX/$PACKAGED_TEMPLATE"

echo ""
echo "=========================================="
echo "✓ Publishing Complete!"
echo "=========================================="
echo ""
echo "Template URL:"
echo "$TEMPLATE_URL"
echo ""
echo "Deploy Button URL:"
echo "https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks/create/review?templateURL=$TEMPLATE_URL&stackName=AtlasEngine"
echo ""
echo "Add this to your README.md:"
echo ""
echo "[![Deploy to AWS](https://img.shields.io/badge/Deploy%20to-AWS-orange?style=for-the-badge&logo=amazon-aws)](https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks/create/review?templateURL=$TEMPLATE_URL&stackName=AtlasEngine)"
echo ""
