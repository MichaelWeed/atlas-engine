# START HERE - Simple Deployment Guide

## What is this?

This folder contains everything needed to deploy Atlas Engine (your AI sales system) to AWS. You don't need to understand all the files if you *just want to install* - follow these steps.

## Before You Start

You need:
1. **AWS Account** - with admin access
2. **AWS CLI** - installed and configured (`aws configure`)
3. **SAM CLI** - installed ([install guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
4. **Salesforce Credentials** - from your [Connected App](SALESFORCE_INTEGRATION.md)

## Simple 3-Step Deployment

### Step 1: Open Terminal and Go to This Folder

```bash
cd /Users/johndoe/Downloads/aws_org_export
```

### Step 2: Run the Deployment Script

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will ask you questions like:
- **Environment**: Type `dev` (for development)
- **Region**: Press Enter to use your default region, or type `us-west-2`
- **Salesforce Secret**: Press Enter to use default name

### Step 3: Wait

The script does everything automatically:
- ✓ Checks prerequisites
- ✓ Builds Lambda functions
- ✓ Creates AWS resources
- ✓ Deploys everything

Takes 15-20 minutes.

## What About My AWS Account ID?

**You don't need to provide it!** The script automatically gets it from your AWS credentials.

## What About Region?

**Two ways to set it:**

Option 1: Before running deploy.sh
```bash
aws configure set region us-west-2 # <-Change this to your region
./deploy.sh
```

Option 2: When the script asks
```
AWS Region [us-west-2]: us-east-1
```
Just type the region you want.

## What Gets Created?

In your AWS account:
- 8 Lambda functions
- 2 DynamoDB tables
- 1 Step Functions workflow
- IAM roles and policies
- CloudWatch logs

**Cost**: ~$24/month for development

## After Deployment

The script will show you:
1. Lambda ARN for Lex bot configuration
2. Manual steps for Amazon Connect (if using voice)
3. How to test the system

## Need Help?

- **Can't find AWS CLI?** Run `aws --version` to check if installed
- **Can't find SAM CLI?** Run `sam --version` to check if installed
- **Deployment fails?** Run `./validate.sh` to see what's missing
- **Want to remove everything?** Run `./cleanup.sh dev`

## Files You Can Ignore

You don't need to understand these unless you want to customize:
- `template.yaml` - Infrastructure definition
- `*.sh` scripts - Automation scripts
- `lambda/` folders - Function code
- Documentation files - Reference material

## Just Want to Deploy?

```bash
cd /Users/johndoe/Downloads/aws_org_export
chmod +x deploy.sh
./deploy.sh
```

Answer the questions, wait 20 minutes, done!
