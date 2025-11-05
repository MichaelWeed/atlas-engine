#!/bin/bash

EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
cd "$EXPORT_DIR"

BUCKETS=("intrepid-services-cc" "atlas-engine-transcripts")

for BUCKET in "${BUCKETS[@]}"; do
    echo "Checking bucket: $BUCKET"
    
    if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
        echo "  Exporting: $BUCKET"
        
        aws s3api get-bucket-location --bucket "$BUCKET" --output json > "s3/${BUCKET}_location.json" 2>/dev/null || echo "{}" > "s3/${BUCKET}_location.json"
        aws s3api get-bucket-versioning --bucket "$BUCKET" --output json > "s3/${BUCKET}_versioning.json" 2>/dev/null || echo "{}" > "s3/${BUCKET}_versioning.json"
        aws s3api get-bucket-policy --bucket "$BUCKET" --output json > "s3/${BUCKET}_policy.json" 2>/dev/null || echo "{\"Policy\": \"No policy\"}" > "s3/${BUCKET}_policy.json"
        aws s3 ls "s3://$BUCKET" --recursive --summarize 2>/dev/null | tail -2 > "s3/${BUCKET}_contents.txt" || echo "No access or empty" > "s3/${BUCKET}_contents.txt"
        
        echo "  ✓ Exported $BUCKET"
    else
        echo "  ✗ Bucket does not exist or no access: $BUCKET"
    fi
done
