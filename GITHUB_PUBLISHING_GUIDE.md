# GitHub Publishing Guide

Quick guide to publish Atlas Engine to GitHub with one-click deployment.

## Step 1: Update License

Edit `LICENSE` file and replace placeholders:
```
<YEAR> → 2024
<YOUR_NAME> → Your Name
```

## Step 2: Publish Template to S3

Create an S3 bucket and publish the packaged template:

```bash
# Create bucket (one-time)
aws s3 mb s3://my-atlas-templates --region us-west-2

# Publish template
./publish-to-s3.sh my-atlas-templates us-west-2
```

The script will output:
- Template URL
- Deploy button URL
- Markdown code for README

## Step 3: Update README Deploy Button

Copy the deploy button markdown from the script output and replace the placeholder in `README.md`:

```markdown
[![Deploy to AWS](https://img.shields.io/badge/Deploy%20to-AWS-orange?style=for-the-badge&logo=amazon-aws)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=YOUR_ACTUAL_URL&stackName=AtlasEngine)
```

## Step 4: Create GitHub Repository

```bash
# Initialize git (if not already)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit: Atlas Engine v1.0"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/atlas-engine.git

# Push
git push -u origin main
```

## Step 5: Configure GitHub Repository

1. Go to your GitHub repository settings
2. Add repository description: "AI-powered sales automation with Amazon Bedrock, Lex, Connect, and Salesforce"
3. Add topics: `aws`, `bedrock`, `lex`, `connect`, `salesforce`, `ai`, `sales-automation`, `serverless`
4. Enable Issues and Discussions (optional)

## Step 6: Test One-Click Deployment

1. Click the "Deploy to AWS" button in your README
2. Verify CloudFormation console opens with pre-filled parameters
3. Test deployment in a clean AWS account

## Files to Review Before Publishing

- [ ] `LICENSE` - Update year and name
- [ ] `README.md` - Update deploy button URL
- [ ] `sam-template/template.yaml` - Review parameter defaults
- [ ] `.gitignore` - Ensure sensitive files excluded
- [ ] Remove any personal/sensitive data from example files

## Optional: Add GitHub Actions

Create `.github/workflows/validate.yml`:

```yaml
name: Validate SAM Template

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aws-actions/setup-sam@v2
      - name: Validate template
        run: |
          cd sam-template
          sam validate
```

## Maintenance

To update the published template:

```bash
# Make changes to template.yaml
# Then republish
./publish-to-s3.sh my-atlas-templates us-west-2

# Commit and push changes
git add .
git commit -m "Update template"
git push
```

## S3 Bucket Policy (Optional)

To make the entire bucket publicly readable:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-atlas-templates/*"
    }
  ]
}
```

Apply with:
```bash
aws s3api put-bucket-policy \
    --bucket my-atlas-templates \
    --policy file://bucket-policy.json
```

## Cost Considerations

The S3 bucket for templates will cost:
- Storage: ~$0.023/GB/month
- Requests: ~$0.0004 per 1,000 GET requests

For a small template (~100KB) with 1,000 deployments/month:
- Storage: < $0.01/month
- Requests: < $0.01/month
- **Total: < $0.02/month**

## Support

After publishing, users can:
- Open GitHub Issues for bugs
- Submit Pull Requests for improvements
- Star the repository
- Fork for customization
