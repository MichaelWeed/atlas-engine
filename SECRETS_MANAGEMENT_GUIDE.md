# Secrets Management Guide - Atlas Engine

## 🔐 How Secrets Work in This Project

### ✅ GOOD NEWS: Your Secrets Are Safe!

**What was exported:** Only metadata (ARN, name, tags, creation date)  
**What was NOT exported:** The actual secret values (credentials, keys, passwords)

---

## 📋 Current Setup

### **Secrets Manager Secret:**
- **Name:** `AtlasEngine/SalesforceCreds`
- **ARN:** `arn:aws:secretsmanager:us-west-2:<AWS_ACCOUNT_ID>:secret:AtlasEngine/SalesforceCreds-4xWYp9`
- **Contains:** Salesforce JWT credentials (username, client_id, private_key)

### **How Lambda Functions Access It:**

```python
# From CreateLeadHandler_code/lambda_function.py

# 1. Get the secret ARN from environment variable
secret_arn = os.environ.get('SALESFORCE_SECRET_ARN')

# 2. Retrieve the secret value at runtime
response = secrets_client.get_secret_value(SecretId=secret_arn)
secret_string = response['SecretString']
credentials = json.loads(secret_string)

# 3. Use the credentials
sf = Salesforce(
    username=credentials['username'],
    consumer_key=credentials['client_id'],
    privatekey=credentials['private_key']
)
```

---

## 🎯 How This Works

### **The Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SECRET STORED IN AWS SECRETS MANAGER                     │
│    (Encrypted at rest, never in code)                       │
│                                                              │
│    {                                                         │
│      "username": "your-sf-username@example.com",            │
│      "client_id": "your-connected-app-client-id",           │
│      "private_key": "-----BEGIN RSA PRIVATE KEY-----..."    │
│    }                                                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. LAMBDA ENVIRONMENT VARIABLE                               │
│    (Only stores the ARN, not the actual secret)             │
│                                                              │
│    SALESFORCE_SECRET_ARN=arn:aws:secretsmanager:...        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. LAMBDA FUNCTION RUNTIME                                   │
│    (Fetches secret value when function executes)            │
│                                                              │
│    credentials = get_salesforce_credentials(secret_arn)     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. USE CREDENTIALS                                           │
│    (Only in memory, never logged or stored)                 │
│                                                              │
│    sf = Salesforce(username=..., client_id=..., ...)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 For Open Source / Documentation

### **What You Need to Provide:**

Create a template file showing the structure (without actual values):

**`secrets-template.json`:**
```json
{
  "username": "your-salesforce-username@example.com",
  "client_id": "your-connected-app-consumer-key",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\nYour private key here\n-----END RSA PRIVATE KEY-----"
}
```

### **Deployment Instructions:**

```bash
# 1. Create the secret in AWS Secrets Manager
aws secretsmanager create-secret \
  --name AtlasEngine/SalesforceCreds \
  --description "Salesforce JWT credentials for Atlas Engine" \
  --secret-string file://secrets-template.json \
  --region us-west-2

# 2. The Lambda functions will automatically use it via the ARN
# (No code changes needed - ARN is in environment variables)
```

---

## 🔧 What's in the Secret

### **Required Fields for Salesforce JWT Authentication:**

```json
{
  "username": "string",      // Salesforce username
  "client_id": "string",     // Connected App Consumer Key
  "private_key": "string"    // RSA Private Key (PEM format)
}
```

### **Used By:**
- ✅ CreateLeadHandler
- ✅ UpdateLeadHandler
- ✅ LexFulfillmentHandler (indirectly)

---

## 🚀 CloudFormation Deployment

### **Option 1: Create Secret in CloudFormation**

```yaml
SalesforceSecret:
  Type: AWS::SecretsManager::Secret
  Properties:
    Name: AtlasEngine/SalesforceCreds
    Description: Salesforce JWT credentials
    SecretString: !Sub |
      {
        "username": "${SalesforceUsername}",
        "client_id": "${SalesforceClientId}",
        "private_key": "${SalesforcePrivateKey}"
      }
    Tags:
      - Key: Project
        Value: AtlasEngine
      - Key: Environment
        Value: !Ref Environment

Parameters:
  SalesforceUsername:
    Type: String
    NoEcho: true
    Description: Salesforce username for JWT authentication
  
  SalesforceClientId:
    Type: String
    NoEcho: true
    Description: Connected App Consumer Key
  
  SalesforcePrivateKey:
    Type: String
    NoEcho: true
    Description: RSA Private Key (PEM format)
```

### **Option 2: Reference Existing Secret**

```yaml
# Just reference the ARN - don't create it
LambdaFunction:
  Type: AWS::Lambda::Function
  Properties:
    Environment:
      Variables:
        SALESFORCE_SECRET_ARN: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:AtlasEngine/SalesforceCreds-XXXXXX"
```

---

## 🔒 Security Best Practices

### ✅ **What This Project Does Right:**

1. **Never hardcodes credentials** - All in Secrets Manager
2. **Uses IAM for access control** - Lambda roles have SecretsManager:GetSecretValue permission
3. **Secrets are encrypted at rest** - AWS manages encryption keys
4. **Secrets are encrypted in transit** - TLS for API calls
5. **No secrets in logs** - Code doesn't log credential values
6. **Environment variables only store ARN** - Not the actual secret

### ⚠️ **What You Need to Do:**

1. **Rotate secrets regularly** - Update Salesforce credentials periodically
2. **Use least privilege IAM** - Only grant access to specific secret ARN
3. **Enable secret rotation** - Consider AWS Secrets Manager automatic rotation
4. **Monitor access** - Use CloudTrail to audit secret access

---

## 📝 Setup Instructions for New Deployments

### **Step 1: Generate Salesforce JWT Credentials**

```bash
# 1. Generate RSA key pair
openssl genrsa -out salesforce-private-key.pem 2048
openssl rsa -in salesforce-private-key.pem -pubout -out salesforce-public-key.pem

# 2. Create Connected App in Salesforce
# - Go to Setup > App Manager > New Connected App
# - Enable OAuth Settings
# - Enable "Use digital signatures"
# - Upload salesforce-public-key.pem
# - Select OAuth Scopes: api, refresh_token, offline_access
# - Save and get Consumer Key (client_id)
```

### **Step 2: Create Secret in AWS**

```bash
# Create the secret JSON file
cat > salesforce-creds.json << EOF
{
  "username": "your-username@example.com",
  "client_id": "your-consumer-key-from-connected-app",
  "private_key": "$(cat salesforce-private-key.pem | sed ':a;N;$!ba;s/\n/\\n/g')"
}
EOF

# Create the secret in AWS
aws secretsmanager create-secret \
  --name AtlasEngine/SalesforceCreds \
  --description "Salesforce JWT credentials for Atlas Engine" \
  --secret-string file://salesforce-creds.json \
  --region us-west-2

# Clean up local files
rm salesforce-creds.json salesforce-private-key.pem
```

### **Step 3: Grant Lambda Access**

```yaml
# IAM Policy (already in AtlasEngineSecretsPolicy)
Statement:
  - Effect: Allow
    Action:
      - secretsmanager:GetSecretValue
    Resource: 
      - !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:AtlasEngine/SalesforceCreds-*"
```

---

## 🔍 Verification

### **Test Secret Access:**

```bash
# Retrieve the secret (requires IAM permissions)
aws secretsmanager get-secret-value \
  --secret-id AtlasEngine/SalesforceCreds \
  --region us-west-2 \
  --query SecretString \
  --output text | jq .

# Should output:
# {
#   "username": "...",
#   "client_id": "...",
#   "private_key": "..."
# }
```

### **Test Lambda Function:**

```bash
# Invoke CreateLeadHandler with test event
aws lambda invoke \
  --function-name CreateLeadHandler \
  --payload '{"firstName":"Test","lastName":"User","phone":"+15555551234"}' \
  --region us-west-2 \
  response.json

# Check logs for successful Salesforce authentication
aws logs tail /aws/lambda/CreateLeadHandler --follow
```

---

## 📊 Secret Metadata (What Was Exported)

```json
{
  "ARN": "arn:aws:secretsmanager:us-west-2:<AWS_ACCOUNT_ID>:secret:AtlasEngine/SalesforceCreds-4xWYp9",
  "Name": "AtlasEngine/SalesforceCreds",
  "CreatedDate": "2025-09-23T03:11:18.046000-07:00",
  "LastChangedDate": "2025-10-27T12:12:46.779000-07:00",
  "LastAccessedDate": "2025-11-04T16:00:00-08:00",
  "Tags": [
    {"Key": "Project", "Value": "AtlasEngine"},
    {"Key": "Environment", "Value": "demo"}
  ]
}
```

**Note:** This metadata is safe to share - it contains no sensitive information.

---

## ❓ FAQ

### **Q: Where is my actual secret value?**
**A:** It's stored securely in AWS Secrets Manager in your AWS account. It was never exported to these files.

### **Q: How do I update the secret?**
**A:** Use AWS Console or CLI:
```bash
aws secretsmanager update-secret \
  --secret-id AtlasEngine/SalesforceCreds \
  --secret-string file://new-creds.json
```

### **Q: Can I use a different secret name?**
**A:** Yes, but you'll need to update the `SALESFORCE_SECRET_ARN` environment variable in all Lambda functions that use it.

### **Q: What if I want to use username/password instead of JWT?**
**A:** You'd need to modify the Lambda code to use `Salesforce(username=..., password=..., security_token=...)` instead of JWT authentication.

### **Q: Is this secure for production?**
**A:** Yes! This is AWS's recommended approach for managing secrets. Just ensure:
- IAM permissions are properly scoped
- Secrets are rotated regularly
- CloudTrail logging is enabled

---

## 🎯 Summary

**For Documentation/Open Source:**
- ✅ Only share the metadata file (safe)
- ✅ Provide a template showing required fields
- ✅ Document the setup process
- ❌ Never share actual secret values

**For Deployment:**
- Create secret in Secrets Manager first
- Lambda functions automatically fetch it at runtime
- No code changes needed - ARN is in environment variables

---

*Your secrets are safe! The export only contains metadata, not actual credentials.*
