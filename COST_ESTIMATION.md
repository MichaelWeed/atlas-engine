# Atlas Engine Cost Estimation

Detailed cost breakdown for different usage scenarios.

## ⚠️ Cost Estimates Disclaimer

**All cost estimates are approximate and preliminary.** They do not account for real-time usage, discounts, taxes, or AWS-specific variables. For precise pricing, contact AWS directly or use their tool:

- [AWS Pricing Calculator](https://calculator.aws/#/addService)

## Development Environment

**Assumptions:**
- 1,000 conversations/month
- 5 Lambda invocations per conversation
- 30-day retention for logs
- US West (Oregon) region

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Lambda** | 5,000 invocations, 512MB, 10s avg | $0.50 |
| **Lambda (Lex Handler)** | 1,000 invocations, 1.5GB, 30s avg | $2.00 |
| **DynamoDB** | 10,000 writes, 20,000 reads | $2.50 |
| **Step Functions** | 1,000 EXPRESS executions | $0.25 |
| **Bedrock (Claude 3.5)** | 1M input tokens, 100K output | $15.00 |
| **CloudWatch Logs** | 5GB ingestion, 7-day retention | $2.50 |
| **Secrets Manager** | 1 secret | $0.40 |
| **SNS** | 1,000 notifications | $0.50 |
| **S3** | 1GB storage, 1,000 requests | $0.25 |
| **TOTAL** | | **~$24/month** |

## Staging Environment

**Assumptions:**
- 10,000 conversations/month
- Testing and QA workloads
- 30-day log retention

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Lambda** | 50,000 invocations | $5.00 |
| **Lambda (Lex Handler)** | 10,000 invocations | $20.00 |
| **DynamoDB** | 100K writes, 200K reads | $25.00 |
| **Step Functions** | 10,000 executions | $2.50 |
| **Bedrock** | 10M input tokens, 1M output | $150.00 |
| **CloudWatch Logs** | 20GB, 30-day retention | $10.00 |
| **Secrets Manager** | 1 secret | $0.40 |
| **SNS** | 10,000 notifications | $0.50 |
| **S3** | 10GB storage | $0.50 |
| **TOTAL** | | **~$214/month** |

## Production Environment (Low Traffic)

**Assumptions:**
- 50,000 conversations/month
- Amazon Connect enabled
- 90-day log retention
- Reserved capacity for DynamoDB

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Lambda** | 250,000 invocations | $25.00 |
| **Lambda (Lex Handler)** | 50,000 invocations | $100.00 |
| **DynamoDB** | 500K writes, 1M reads (on-demand) | $125.00 |
| **Step Functions** | 50,000 executions | $12.50 |
| **Bedrock** | 50M input tokens, 5M output | $750.00 |
| **Amazon Connect** | 50K minutes | $65.00 |
| **CloudWatch Logs** | 100GB, 90-day retention | $50.00 |
| **Secrets Manager** | 1 secret | $0.40 |
| **SNS** | 50,000 notifications | $0.50 |
| **S3** | 50GB storage | $1.15 |
| **Data Transfer** | 100GB out | $9.00 |
| **TOTAL** | | **~$1,138/month** |

## Production Environment (High Traffic)

**Assumptions:**
- 500,000 conversations/month
- High availability setup
- Provisioned DynamoDB capacity
- 90-day log retention

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Lambda** | 2.5M invocations | $250.00 |
| **Lambda (Lex Handler)** | 500K invocations | $1,000.00 |
| **DynamoDB** | Provisioned: 500 RCU, 250 WCU | $350.00 |
| **Step Functions** | 500K executions | $125.00 |
| **Bedrock** | 500M input tokens, 50M output | $7,500.00 |
| **Amazon Connect** | 500K minutes | $650.00 |
| **CloudWatch Logs** | 500GB, 90-day retention | $250.00 |
| **Secrets Manager** | 1 secret | $0.40 |
| **SNS** | 500K notifications | $0.50 |
| **S3** | 200GB storage | $4.60 |
| **Data Transfer** | 1TB out | $90.00 |
| **TOTAL** | | **~$10,220/month** |

## Cost Optimization Strategies

### 1. Lambda Optimization
```yaml
# Reduce memory for simple functions - review the end of the CloudWatch logs
# for running size and timeout. Recommend double active working memory to maintain
# memory pressure 
MemorySize: 128  # Instead of 512

# Use ARM architecture (20% cheaper)
Architectures: [arm64]

# Set appropriate timeouts
Timeout: 15  # Don't use default 30s
```

**Savings: 30-40%**

### 2. DynamoDB Optimization
```yaml
# Use on-demand for unpredictable workloads
BillingMode: PAY_PER_REQUEST

# Use provisioned with auto-scaling for steady workloads
BillingMode: PROVISIONED
ProvisionedThroughput:
  ReadCapacityUnits: 5
  WriteCapacityUnits: 5

# Enable TTL for temporary data
TimeToLiveSpecification:
  AttributeName: ExpirationTime
  Enabled: true
```

**Savings: 40-60%**

### 3. Bedrock Optimization
```python
# Use smaller models for simple tasks
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"  # 80% cheaper

# Implement caching
@lru_cache(maxsize=1000)
def get_scenario(lead_info):
    return bedrock.invoke_model(...)

# Batch requests when possible
# Use streaming for long responses
```

**Savings: 50-80%**

### 4. CloudWatch Logs Optimization
```yaml
# Reduce retention period
RetentionInDays: 7  # Instead of 30

# Filter logs before ingestion
# Use log sampling for high-volume functions
```

**Savings: 60-75%**

### 5. Step Functions Optimization
```yaml
# Use EXPRESS workflows (cheaper)
Type: EXPRESS

# Minimize state transitions
# Combine multiple Lambda calls into one
```

**Savings: 90% vs STANDARD**

### 6. Amazon Connect Optimization
- Use callback queues to reduce hold time
- Implement IVR to filter calls
- Use voicemail for off-hours

**Savings: 30-50%**

## Cost Monitoring

### Set Up Billing Alarms
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name AtlasEngine-BillingAlarm \
    --alarm-description "Alert when costs exceed $100" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 21600 \
    --threshold 100 \
    --comparison-operator GreaterThanThreshold
```

### Enable Cost Allocation Tags
```yaml
Tags:
  - Key: Project
    Value: AtlasEngine
  - Key: Environment
    Value: !Ref Environment
  - Key: CostCenter
    Value: Sales
```

### Use AWS Cost Explorer
```bash
# View costs by service
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

## Free Tier Eligibility

**First 12 months:**
- Lambda: 1M requests/month free
- DynamoDB: 25GB storage, 25 RCU/WCU free
- CloudWatch: 10 custom metrics, 5GB logs free
- SNS: 1M requests free
- Step Functions: 4,000 state transitions free

**Always free:**
- Secrets Manager: First 30 days free (then $0.40/secret/month)
- S3: First 5GB free (12 months)

## Cost Comparison: Atlas Engine vs Alternatives

| Solution | Monthly Cost (50K conversations) |
|----------|----------------------------------|
| **Atlas Engine (AWS)** | $1,138 |
| Salesforce Einstein | $2,500+ |
| Custom on-premises | $5,000+ (infrastructure + maintenance) |
| Third-party SaaS | $1,500-3,000 |

## ROI Calculation

**Assumptions:**
- 50,000 conversations/month
- 10% conversion rate = 5,000 leads
- Average deal size: $1,000
- Close rate: 20%

**Revenue:**
- Closed deals: 1,000/month
- Revenue: $1,000,000/month

**Costs:**
- Atlas Engine: $1,138/month
- Sales team (10 reps): $50,000/month
- **Total: $51,138/month**

**ROI: 1,855%**

## Budget Recommendations

| Environment | Monthly Budget | Annual Budget |
|-------------|----------------|---------------|
| Development | $50 | $600 |
| Staging | $250 | $3,000 |
| Production (Low) | $1,500 | $18,000 |
| Production (High) | $12,000 | $144,000 |

## Questions?

Use AWS Pricing Calculator for custom scenarios:
https://calculator.aws/#/addService

Contact AWS Support for Enterprise Discount Program (EDP):
https://aws.amazon.com/pricing/
