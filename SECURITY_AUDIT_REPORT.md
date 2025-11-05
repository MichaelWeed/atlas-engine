# Atlas Engine - Security Audit Report
## Pre-Open Source Checklist

**Audit Date:** 2025-10-29  
**Status:** 🔴 CRITICAL - DO NOT OPEN SOURCE WITHOUT REMEDIATION

---

## 🚨 CRITICAL FINDINGS

### 1. AWS Account ID Exposure (HIGH SEVERITY)
**Account ID:** `<AWS_ACCOUNT_ID>`

**Locations Found:**
- All JSON configuration files (100+ occurrences)
- All IAM role ARNs
- All Lambda function ARNs
- All DynamoDB table ARNs
- Step Functions definitions
- CloudWatch log groups
- EventBridge rules

**Risk:** Account enumeration, targeted attacks

**Remediation:**
```bash
# Replace all occurrences with placeholder
find . -type f \( -name "*.json" -o -name "*.md" -o -name "*.py" \) -exec sed -i '' 's/<AWS_ACCOUNT_ID>/<AWS_ACCOUNT_ID>/g' {} +
```

---

### 2. PII in DynamoDB Data (CRITICAL SEVERITY)

**Phone Number Found:** `<PHONE_NUMBER>` (<PHONE_NUMBER>)
**Occurrences:** 124+ times in `dynamodb/AtlasEngineInteractions_data.json`

**Names Found in Transcripts:**
- "Donald Trump" (test data)
- "John Cena" (test data)
- "Michael Weed"
- "Jack Frosty"
- "Mark Benioff"
- "Andrew" (multiple occurrences)

**Remediation:**
```bash
# DELETE the entire DynamoDB data file
rm dynamodb/AtlasEngineInteractions_data.json

# Or sanitize it
sed -i '' 's/<PHONE_NUMBER>/<PHONE_NUMBER>/g' dynamodb/AtlasEngineInteractions_data.json
sed -i '' 's/<PHONE_NUMBER>/<PHONE_NUMBER>/g' dynamodb/AtlasEngineInteractions_data.json
```

---

### 3. Step Functions Task Tokens (CRITICAL SEVERITY)

**Location:** `dynamodb/AtlasEngineInteractions_data.json`

**Finding:** 50+ actual Step Functions task tokens exposed in DynamoDB export

**Example:**
```
"StepFunctionTaskToken": {
    "S": "AQB8AAAAKgAAAAMAAAAAAAAAAcCVC2Ycp12BoPzhF72ye58NspayVvsIhtQbSCahoHpjqwvTh4B9DkaYIOLyHhkGMxDMaWSrYplU4A+443WkutzyqpPGl0ywRfYrSA==..."
}
```

**Risk:** Could potentially be used to manipulate workflow execution

**Remediation:**
- DELETE the DynamoDB data file entirely
- Never export production data

---

### 4. Hardcoded Values in Lambda Code

#### a. DynamoDB Table Name (MEDIUM SEVERITY)
**File:** `lambda/InitiateCallHandler_code/lambda_function.py:12`
```python
table = dynamodb.Table('AtlasEngineTaskTokens')
```

**Suggested Fix:**
```python
table = dynamodb.Table(os.environ.get('TASK_TOKENS_TABLE', 'AtlasEngineTaskTokens'))
```

#### b. Source Phone Number (LOW SEVERITY)
**Files:**
- `lambda/InitiateCallHandler_config.json:17`
- `lambda/InvokeOutboundCallHandler_config.json:17`

```json
"SOURCE_PHONE_NUMBER": "<SOURCE_PHONE_NUMBER>"
```

**Suggested Fix:**
- Already in environment variables ✅
- Document as example value in README

#### c. Salesforce Endpoints (LOW SEVERITY)
**File:** `lambda/LexFulfillmentHandler_code/lambda_function.py:52`
```python
endpoint = 'https://test.salesforce.com' if is_sandbox else 'https://login.salesforce.com'
```

**Status:** Acceptable - these are public Salesforce endpoints

---

### 5. Amazon Connect Instance ID (MEDIUM SEVERITY)

**Instance ID:** `<CONNECT_INSTANCE_ID>`

**Locations:**
- IAM policies
- Connect configuration files
- Documentation

**Remediation:**
```bash
find . -type f -exec sed -i '' 's/<CONNECT_INSTANCE_ID>/<CONNECT_INSTANCE_ID>/g' {} +
```

---

### 6. Salesforce Lead IDs (LOW SEVERITY)

**Example:** `00QKa00000iYfg0MAC`

**Location:** `dynamodb/AtlasEngineInteractions_data.json`

**Remediation:** Delete DynamoDB data file

---

### 7. AWS Region Hardcoding (LOW SEVERITY)

**Region:** `us-west-2` (hardcoded in 100+ places)

**Suggested Fix:**
- Document as example
- Add parameterization guide in README

---

## ✅ GOOD SECURITY PRACTICES FOUND

1. **No Hardcoded Credentials** ✅
   - All secrets use AWS Secrets Manager
   - No API keys in code

2. **Environment Variables** ✅
   - Most configuration uses environment variables
   - Proper separation of config from code

3. **IAM Least Privilege** ✅
   - Scoped policies
   - Separate roles per function

4. **No Database Credentials** ✅
   - DynamoDB uses IAM roles
   - No connection strings

---

## 📋 PRE-OPEN SOURCE CHECKLIST

### Must Do (Before ANY Public Release):

- [ ] **DELETE** `dynamodb/AtlasEngineInteractions_data.json`
- [ ] **DELETE** `dynamodb/AtlasEngineTaskTokens_data.json`
- [ ] Replace AWS Account ID `<AWS_ACCOUNT_ID>` with `<AWS_ACCOUNT_ID>`
- [ ] Replace Connect Instance ID with `<CONNECT_INSTANCE_ID>`
- [ ] Replace phone number `<PHONE_NUMBER>` with `<PHONE_NUMBER>`
- [ ] Replace phone number `<SOURCE_PHONE_NUMBER>` with `<SOURCE_PHONE_NUMBER>`
- [ ] Review all JSON files for additional PII
- [ ] Sanitize CloudWatch log exports (if any)
- [ ] Remove any temporary security tokens from layer download URLs

### Should Do (Best Practices):

- [ ] Parameterize hardcoded table name in `InitiateCallHandler`
- [ ] Add `.gitignore` for sensitive files
- [ ] Create `config.example.json` with placeholder values
- [ ] Document all required environment variables
- [ ] Add security section to README
- [ ] Create deployment guide with parameterization instructions

### Nice to Have:

- [ ] Add pre-commit hooks to prevent credential commits
- [ ] Create sanitization script for future exports
- [ ] Add SECURITY.md file
- [ ] Document AWS account setup requirements

---

## 🔧 AUTOMATED REMEDIATION SCRIPT

```bash
#!/bin/bash
# sanitize_for_opensource.sh

EXPORT_DIR="/Users/johndoe/Downloads/aws_org_export"
cd "$EXPORT_DIR"

echo "🔒 Sanitizing Atlas Engine export for open source..."

# 1. DELETE sensitive data files
echo "Deleting DynamoDB data files..."
rm -f dynamodb/*_data.json

# 2. Replace AWS Account ID
echo "Replacing AWS Account ID..."
find . -type f \( -name "*.json" -o -name "*.md" -o -name "*.py" -o -name "*.txt" \) \
    -exec sed -i '' 's/<AWS_ACCOUNT_ID>/<AWS_ACCOUNT_ID>/g' {} +

# 3. Replace Connect Instance ID
echo "Replacing Connect Instance ID..."
find . -type f \( -name "*.json" -o -name "*.md" -o -name "*.py" \) \
    -exec sed -i '' 's/<CONNECT_INSTANCE_ID>/<CONNECT_INSTANCE_ID>/g' {} +

# 4. Replace phone numbers
echo "Replacing phone numbers..."
find . -type f \( -name "*.json" -o -name "*.md" -o -name "*.py" \) \
    -exec sed -i '' 's/<PHONE_NUMBER>/<PHONE_NUMBER>/g' {} +
find . -type f \( -name "*.json" -o -name "*.md" -o -name "*.py" \) \
    -exec sed -i '' 's/<PHONE_NUMBER>/<PHONE_NUMBER>/g' {} +
find . -type f \( -name "*.json" -o -name "*.md" -o -name "*.py" \) \
    -exec sed -i '' 's/<SOURCE_PHONE_NUMBER>/<SOURCE_PHONE_NUMBER>/g' {} +

# 5. Remove temporary AWS URLs with security tokens
echo "Removing temporary AWS URLs..."
find lambda_layers -name "*_details.json" -exec sed -i '' 's/"Location": "https:\/\/.*"/"Location": "<LAYER_DOWNLOAD_URL>"/g' {} +

# 6. Create .gitignore
echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Sensitive data
*_data.json
*.pem
*.key
*.env
.env

# AWS credentials
.aws/
credentials

# Temporary files
*.tmp
*.log
EOF

echo "✅ Sanitization complete!"
echo ""
echo "⚠️  MANUAL REVIEW REQUIRED:"
echo "  1. Review all JSON files for additional PII"
echo "  2. Check Lambda code for hardcoded values"
echo "  3. Verify no secrets in environment variables"
echo "  4. Test deployment with placeholder values"
```

---

## 📊 SUMMARY

| Category | Count | Severity |
|----------|-------|----------|
| AWS Account IDs | 100+ | HIGH |
| PII (Phone Numbers) | 124+ | CRITICAL |
| PII (Names) | 50+ | MEDIUM |
| Task Tokens | 50+ | CRITICAL |
| Instance IDs | 10+ | MEDIUM |
| Hardcoded Values | 3 | LOW-MEDIUM |

**Total Issues:** 300+ occurrences requiring remediation

---

## 🎯 RECOMMENDATION

**DO NOT open source this repository without:**

1. Running the automated sanitization script
2. Deleting all DynamoDB data files
3. Manual review of all configuration files
4. Testing deployment with sanitized values

**Estimated Remediation Time:** 2-4 hours

---

## 📝 NOTES

- No actual AWS credentials or API keys were found ✅
- All sensitive data is in configuration, not code ✅
- Most issues are easily fixable with find/replace ✅
- DynamoDB data should NEVER have been exported ❌

---

*Generated: 2025-10-29*  
*Auditor: Amazon Q*  
*Files Scanned: 150+*
