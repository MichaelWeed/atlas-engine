# GitHub Publishing Checklist

Quick checklist to publish Atlas Engine with one-click deployment.

## Pre-Publishing Checklist

- [ ] **Update LICENSE**
  ```bash
  # Edit LICENSE file and replace:
  # <YEAR> → 2024
  # <YOUR_NAME> → Your Name
  ```

- [ ] **Create S3 Bucket**
  ```bash
  aws s3 mb s3://YOUR-BUCKET-NAME --region us-west-2
  ```

- [ ] **Publish Template to S3**
  ```bash
  ./publish-to-s3.sh YOUR-BUCKET-NAME us-west-2
  ```

- [ ] **Copy Deploy Button URL**
  - Script outputs the deploy button markdown
  - Copy the full URL

- [ ] **Update README.md**
  - Replace `<YOUR_S3_TEMPLATE_URL>` with actual URL from script output
  - Verify flag.jpg displays correctly

- [ ] **Security Review**
  ```bash
  # Check for AWS keys
  grep -r "AKIA" . --exclude-dir=.git
  
  # Check for secrets
  grep -r "password\|secret\|key" . --exclude-dir=.git --exclude="*.md"
  
  # Check for personal emails
  grep -r "@.*\.com" . --exclude-dir=.git --exclude="*.md"
  ```

- [ ] **Remove Personal Data**
  - Check all JSON files in config/, iam/, etc.
  - Remove any account IDs, emails, phone numbers
  - Verify no real Salesforce credentials

- [ ] **Test Template Locally**
  ```bash
  sam validate --template sam-template/template.yaml
  ```

## Publishing to GitHub

- [ ] **Initialize Git**
  ```bash
  git init
  git add .
  git commit -m "Initial commit: Atlas Engine v1.0"
  ```

- [ ] **Create GitHub Repository**
  - Go to https://github.com/new
  - Name: `atlas-engine`
  - Description: "AI-powered sales automation with Amazon Bedrock, Lex, Connect, and Salesforce"
  - Public repository
  - Don't initialize with README (you already have one)

- [ ] **Push to GitHub**
  ```bash
  git remote add origin https://github.com/YOUR_USERNAME/atlas-engine.git
  git branch -M main
  git push -u origin main
  ```

- [ ] **Configure Repository**
  - Add topics: `aws`, `bedrock`, `lex`, `connect`, `salesforce`, `ai`, `sales-automation`, `serverless`
  - Add website URL (optional)
  - Enable Issues
  - Enable Discussions (optional)

## Post-Publishing Checklist

- [ ] **Test Deploy Button**
  - Click "Deploy to AWS" button in README
  - Verify CloudFormation console opens
  - Check all parameters display correctly
  - Don't actually deploy (unless testing)

- [ ] **Verify Documentation**
  - README.md displays correctly
  - flag.jpg image loads
  - All links work
  - Code blocks render properly

- [ ] **Create GitHub Release**
  ```bash
  git tag -a v1.0.0 -m "Initial release"
  git push origin v1.0.0
  ```
  - Go to GitHub → Releases → Create new release
  - Tag: v1.0.0
  - Title: "Atlas Engine v1.0.0 - Initial Release"
  - Description: Copy from README.md

- [ ] **Add Additional Files** (Optional)
  - CONTRIBUTING.md
  - CODE_OF_CONDUCT.md
  - SECURITY.md
  - Issue templates
  - Pull request template

- [ ] **Test in Clean AWS Account**
  - Use the one-click deploy button
  - Verify all resources deploy successfully
  - Check CloudFormation outputs
  - Test basic functionality

## Maintenance Checklist

When updating the template:

- [ ] **Make Changes**
  - Edit sam-template/template.yaml
  - Update version number
  - Update CHANGELOG.md

- [ ] **Republish to S3**
  ```bash
  ./publish-to-s3.sh YOUR-BUCKET-NAME us-west-2
  ```

- [ ] **Commit and Push**
  ```bash
  git add .
  git commit -m "Update: description of changes"
  git push
  ```

- [ ] **Create New Release**
  ```bash
  git tag -a v1.1.0 -m "Version 1.1.0"
  git push origin v1.1.0
  ```

## Quick Commands

```bash
# Full publishing flow
sed -i '' 's/<YEAR>/2024/g' LICENSE
sed -i '' 's/<YOUR_NAME>/Your Name/g' LICENSE
aws s3 mb s3://your-bucket --region us-west-2
./publish-to-s3.sh your-bucket us-west-2
# Copy URL from output and update README.md
git init
git add .
git commit -m "Initial commit: Atlas Engine v1.0"
git remote add origin https://github.com/YOUR_USERNAME/atlas-engine.git
git push -u origin main
```

## Files to Review

- [ ] LICENSE - Name and year updated
- [ ] README.md - Deploy button URL updated
- [ ] .gitignore - Excludes sensitive files
- [ ] sam-template/template.yaml - Parameters look good
- [ ] All documentation files - No personal data

## Ready to Share!

Once all checkboxes are complete:

1. Share repository URL
2. Tweet/post about it
3. Submit to AWS samples (optional)
4. Add to your portfolio
5. Monitor GitHub issues for feedback

🚀 **Your one-click deployment is ready!**
