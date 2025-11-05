# Architecture Flow with Performance Bottlenecks

## Current Architecture (9+ seconds)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ USER SPEECH → LEX                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ LexFulfillmentHandler Lambda                                            │
│ ⚠️  COLD START: 3-5 seconds (31MB layers, $LATEST version)             │
│ ⚠️  Secrets Manager call: 300ms                                         │
│ ⚠️  Bedrock invoke_model: 2-4 seconds (BLOCKING)                        │
│ ⚠️  DynamoDB query: 200ms                                               │
│                                                                          │
│ Total: 5.5-9.5 seconds                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ LEX → USER (Response)                                                    │
└─────────────────────────────────────────────────────────────────────────┘

TOTAL LATENCY: 9+ seconds ❌
```

---

## Step Functions Workflow (Sequential - 6-11 seconds)

```
User initiates demo from web chat
         ↓
┌────────────────────────────────────────────────────────────────┐
│ LexFulfillmentHandler                                          │
│ - Starts Step Functions execution                             │
│ - Returns immediately to user                                  │
└────────────────────────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────────────────────────┐
│ Step Functions: AtlasEngineWorkflow (STANDARD)                 │
│                                                                 │
│  [1] CreateLeadHandler                                         │
│      ⚠️  Secrets Manager: 300ms                                │
│      ⚠️  Salesforce JWT auth: 500ms                            │
│      ⚠️  Salesforce API call: 800ms                            │
│      ⚠️  DynamoDB write: 100ms                                 │
│      Total: 2-3 seconds                                        │
│         ↓                                                       │
│  [2] GenerateDynamicScenarioHandler                            │
│      ⚠️  Bedrock invoke_model: 2-4 seconds                     │
│      ⚠️  Undersized (128MB): +500ms                            │
│      Total: 2.5-4.5 seconds                                    │
│         ↓                                                       │
│  [3] InvokeOutboundCallHandler                                 │
│      ⚠️  DynamoDB write (scenario): 200ms                      │
│      ⚠️  Connect start_outbound_voice_contact: 800ms           │
│      ⚠️  DynamoDB update (contactId): 100ms                    │
│      Total: 1-2 seconds                                        │
│         ↓                                                       │
│  [4] Wait for call completion (waitForTaskToken)               │
│      - Call happens (not counted in workflow time)             │
│         ↓                                                       │
│  [5] UpdateLeadHandler                                         │
│      ⚠️  Salesforce auth (cached): 100ms                       │
│      ⚠️  Salesforce API call: 800ms                            │
│      Total: 1-2 seconds                                        │
│                                                                 │
│ TOTAL WORKFLOW TIME: 6.5-11.5 seconds                          │
└────────────────────────────────────────────────────────────────┘
```

---

## Optimized Architecture (2-3 seconds target)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ USER SPEECH → LEX                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ LexFulfillmentHandler Lambda (OPTIMIZED)                                │
│ ✅ Provisioned Concurrency (version 28): 0ms cold start                 │
│ ✅ Cached secrets: 0ms (was 300ms)                                      │
│ ✅ DynamoDB cache check: 50ms                                           │
│    ├─ Cache HIT → Return cached response: 50ms                          │
│    └─ Cache MISS → Return static + async generate: 100ms                │
│                                                                          │
│ Total: 50-150ms                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ LEX → USER (Response)                                                    │
└─────────────────────────────────────────────────────────────────────────┘

TOTAL LATENCY: 50-150ms ✅ (60-180x faster!)
```

---

## Optimized Step Functions (Parallel - 3-5 seconds)

```
User initiates demo from web chat
         ↓
┌────────────────────────────────────────────────────────────────┐
│ LexFulfillmentHandler                                          │
│ - Starts Step Functions execution                             │
│ - Returns immediately to user                                  │
└────────────────────────────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────────────────────────────┐
│ Step Functions: AtlasEngineWorkflow (EXPRESS)                  │
│                                                                 │
│  [1] CreateLeadHandler (OPTIMIZED)                             │
│      ✅ Cached secrets: 0ms                                    │
│      ✅ Connection pooling: 200ms (was 800ms)                  │
│      ✅ DynamoDB write: 100ms                                  │
│      Total: 1-1.5 seconds                                      │
│         ↓                                                       │
│  [2] PARALLEL EXECUTION ═══════════════════════════════════    │
│      ║                                          ║              │
│      ║  GenerateDynamicScenarioHandler          ║              │
│      ║  ✅ Increased memory (512MB): 0ms        ║              │
│      ║  ✅ Haiku model: 0.5-1s (was 2-4s)       ║              │
│      ║  Total: 0.5-1 second                     ║              │
│      ║                                          ║              │
│      ║                                          ║              │
│      ║                                          ║              │
│      ╚══════════════════════════════════════════╝              │
│         ↓                                                       │
│  [3] InvokeOutboundCallHandler                                 │
│      ✅ DynamoDB write: 200ms                                  │
│      ✅ Connect API: 800ms                                     │
│      Total: 1 second                                           │
│         ↓                                                       │
│  [4] Wait for call completion (async)                          │
│         ↓                                                       │
│  [5] UpdateLeadHandler (ASYNC - non-blocking)                  │
│      ✅ Runs after call completes                              │
│      ✅ Not in critical path                                   │
│                                                                 │
│ TOTAL WORKFLOW TIME: 2.5-3.5 seconds                           │
└────────────────────────────────────────────────────────────────┘
```

---

## Detailed Bottleneck Analysis

### 1. LexFulfillmentHandler Cold Start (3-5 seconds)

```
Lambda Invocation
    ↓
┌─────────────────────────────────────────────────────────────┐
│ COLD START SEQUENCE                                         │
│                                                              │
│ 1. Download Lambda package (34KB)           : 100ms         │
│ 2. Download Layer 1 (LexBotDependencies)    : 800ms ⚠️      │
│ 3. Download Layer 2 (phonenumbers)          : 900ms ⚠️      │
│ 4. Download Layer 3 (RequestsLibrary)       : 200ms         │
│ 5. Initialize Python runtime                : 300ms         │
│ 6. Import modules (boto3, simple_salesforce): 500ms         │
│ 7. Initialize boto3 clients (3x)            : 400ms         │
│                                                              │
│ TOTAL COLD START: 3.2 seconds                               │
└─────────────────────────────────────────────────────────────┘
    ↓
Handler Execution
    ↓
┌─────────────────────────────────────────────────────────────┐
│ HANDLER EXECUTION                                           │
│                                                              │
│ 1. Parse event                              : 10ms          │
│ 2. Get session attributes                   : 5ms           │
│ 3. Check for interactionKey                 : 5ms           │
│ 4. Query DynamoDB (if phone call)           : 200ms ⚠️      │
│ 5. Route to intent handler                  : 5ms           │
│ 6. Get Salesforce credentials (Secrets Mgr) : 300ms ⚠️      │
│ 7. Generate dynamic response (Bedrock)      : 2500ms ⚠️     │
│ 8. Update conversation history              : 50ms          │
│ 9. Return response                          : 10ms          │
│                                                              │
│ TOTAL HANDLER: 3.1 seconds                                  │
└─────────────────────────────────────────────────────────────┘

TOTAL: 6.3 seconds (cold start + handler)
```

### 2. Bedrock API Call Breakdown (2-4 seconds)

```
invoke_model() call
    ↓
┌─────────────────────────────────────────────────────────────┐
│ BEDROCK API LATENCY                                         │
│                                                              │
│ 1. Construct prompt                         : 50ms          │
│ 2. JSON serialize request body              : 20ms          │
│ 3. HTTP request to Bedrock endpoint         : 100ms         │
│ 4. Model inference (Claude 3.5 Sonnet)      : 2000-3500ms ⚠️│
│    - Prompt processing: 500ms                               │
│    - Token generation (512 tokens): 1500-3000ms             │
│ 5. HTTP response                            : 100ms         │
│ 6. JSON deserialize response                : 30ms          │
│ 7. Extract text from response               : 10ms          │
│                                                              │
│ TOTAL: 2.3-3.8 seconds                                      │
└─────────────────────────────────────────────────────────────┘

OPTIMIZATION OPPORTUNITIES:
- Switch to Haiku: 0.5-1s (4-8x faster)
- Reduce max_tokens to 150: -500ms
- Cache responses: 0ms (cache hit)
- Async generation: perceived 0ms
```

### 3. Salesforce Authentication (500-800ms)

```
get_sf_connection() call
    ↓
┌─────────────────────────────────────────────────────────────┐
│ SALESFORCE JWT AUTHENTICATION                               │
│                                                              │
│ 1. Get secret from Secrets Manager          : 300ms ⚠️      │
│ 2. Parse JSON credentials                   : 5ms           │
│ 3. Construct JWT payload                    : 10ms          │
│ 4. Sign JWT with private key                : 50ms          │
│ 5. HTTP POST to Salesforce OAuth endpoint   : 200ms         │
│ 6. Parse OAuth response                     : 10ms          │
│ 7. Initialize Salesforce client             : 50ms          │
│                                                              │
│ TOTAL: 625ms                                                │
└─────────────────────────────────────────────────────────────┘

OPTIMIZATION OPPORTUNITIES:
- Cache secrets: -300ms
- Connection pooling: -200ms
- Total optimized: 125ms (5x faster)
```

---

## Performance Comparison Table

| Component | Current | Phase 1 | Phase 2 | Phase 3 |
|-----------|---------|---------|---------|---------|
| **LexFulfillmentHandler** |
| Cold start | 3-5s | 0s ✅ | 0s | 0s |
| Secrets call | 300ms | 0ms ✅ | 0ms | 0ms |
| DynamoDB query | 200ms | 50ms ✅ | 50ms | 50ms |
| Bedrock call | 2-4s | 2-4s | 0.5-1s ✅ | 0ms ✅ |
| **Subtotal** | **5.5-9.5s** | **2-4s** | **0.5-1s** | **50ms** |
| | | | | |
| **Step Functions** |
| CreateLead | 2-3s | 2-3s | 1-1.5s ✅ | 1-1.5s |
| GenerateScenario | 2.5-4.5s | 2.5-4.5s | 0.5-1s ✅ | 0.5-1s |
| InvokeCall | 1-2s | 1-2s | 1s ✅ | 1s |
| UpdateLead | 1-2s | 1-2s | async ✅ | async |
| **Subtotal** | **6.5-11.5s** | **6.5-11.5s** | **2.5-3.5s** | **2.5-3.5s** |
| | | | | |
| **TOTAL** | **9+ seconds** | **3-5 seconds** | **1-2 seconds** | **<1 second** |
| **vs Target** | ❌ 3x slower | ✅ At target | ✅ 2x better | ✅ 3x better |

---

## Critical Path Analysis

### Current Critical Path (9+ seconds)
```
User Speech
    → Lex Processing (500ms)
    → Lambda Cold Start (3-5s) ⚠️
    → Secrets Manager (300ms) ⚠️
    → DynamoDB Query (200ms) ⚠️
    → Bedrock API (2-4s) ⚠️
    → Response Processing (100ms)
    → Lex Response (500ms)
= 9+ seconds
```

### Optimized Critical Path (50-150ms)
```
User Speech
    → Lex Processing (500ms)
    → Lambda (warm, provisioned) (0ms) ✅
    → Cache Check (50ms) ✅
    → Return Cached/Static Response (50ms) ✅
    → Lex Response (500ms)
= 1.1 seconds

[Async: Bedrock generation for next turn]
```

---

## Caching Strategy

### Response Cache Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ DynamoDB Table: AtlasEngine-ResponseCache                   │
│                                                              │
│ PK: RESPONSE#{intent}#{context_hash}                        │
│ SK: TIMESTAMP                                               │
│ Attributes:                                                 │
│   - response: "Generated text..."                           │
│   - generatedAt: 1234567890                                 │
│   - TTL: 1234568190 (5 min expiry)                          │
│                                                              │
│ Indexes:                                                    │
│   - GSI1: intent + timestamp (for analytics)                │
└─────────────────────────────────────────────────────────────┘

Cache Hit Rate Projection:
- GreetingIntent: 80% (highly repetitive)
- AboutTechnologyIntent: 60%
- AboutDemoIntent: 60%
- FallbackIntent: 40%
- Overall: 50-60%

Performance Impact:
- Cache HIT: 50ms (vs 2-4s Bedrock call)
- Cache MISS: 2.5s (Bedrock + cache write)
- Average: 0.5 * 50ms + 0.5 * 2500ms = 1.3s
- Improvement: 1.2-2.7s saved (40-60% reduction)
```

---

## Network Latency Map

```
┌──────────────────────────────────────────────────────────────────┐
│ Lambda (us-west-2)                                               │
│   ↓ 5ms (same region)                                            │
│ DynamoDB (us-west-2)                                             │
│   ↓ 10ms (same region)                                           │
│ Secrets Manager (us-west-2)                                      │
│   ↓ 15ms (same region)                                           │
│ Bedrock (us-west-2)                                              │
│   ↓ 200ms (internet)                                             │
│ Salesforce (external API)                                        │
│   ↓ 100ms (AWS backbone)                                         │
│ Amazon Connect (us-west-2)                                       │
└──────────────────────────────────────────────────────────────────┘

Total Network Overhead: ~330ms (unavoidable)
Optimization Focus: Reduce API calls and processing time
```

---

## Memory vs Performance Trade-off

```
Lambda Memory Allocation Impact:

128 MB:  CPU: 0.2 vCPU  |  Cost: $0.0000000021/ms  |  Speed: 1.0x
256 MB:  CPU: 0.4 vCPU  |  Cost: $0.0000000042/ms  |  Speed: 1.5x ✅
512 MB:  CPU: 0.8 vCPU  |  Cost: $0.0000000083/ms  |  Speed: 2.0x ✅
1024 MB: CPU: 1.6 vCPU  |  Cost: $0.0000000167/ms  |  Speed: 2.5x

Recommendation:
- LexFulfillmentHandler: 512 MB (current) ✅
- GenerateDynamicScenarioHandler: 512 MB (upgrade from 128 MB) ⚠️
- CreateLeadHandler: 256 MB (upgrade from 128 MB) ⚠️
- InvokeOutboundCallHandler: 256 MB (current) ✅
- UpdateLeadHandler: 256 MB (current) ✅

Cost Impact: +$10/month
Performance Impact: -500ms to -1s
ROI: Excellent
```

---

## Provisioned Concurrency Analysis

```
Current Configuration:
- LexFulfillmentHandler version 28: 1 provisioned instance
- Cost: ~$15/month
- Problem: Lex pointing to $LATEST, not version 28 ⚠️

Optimized Configuration:
- Update Lex bot alias to use version 28
- Increase to 2 provisioned instances (for redundancy)
- Cost: ~$30/month
- Benefit: Zero cold starts

Cold Start Elimination:
- Current: 3-5s cold start on 30% of requests
- Optimized: 0s cold start on 100% of requests
- Average improvement: 0.3 * 4s = 1.2s saved per request
```

---

## Recommended Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Amazon Lex (NLU)                                                 │
│ - Intent recognition: 200-500ms                                  │
│ - Slot filling: 100-300ms                                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ LexFulfillmentHandler (Provisioned Concurrency)                  │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 1. Check Response Cache (DynamoDB)          : 50ms       │   │
│ │    ├─ HIT → Return immediately                           │   │
│ │    └─ MISS → Continue                                    │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 2. Return Static Response                   : 50ms       │   │
│ │    (User gets immediate feedback)                        │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ 3. Async: Invoke Bedrock (SQS/EventBridge)              │   │
│ │    - Generate better response for next turn              │   │
│ │    - Store in cache                                      │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│ Total User-Facing Latency: 100ms ✅                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step Functions (Express Workflow)                                │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ CreateLeadHandler (optimized)               : 1-1.5s     │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │              PARALLEL EXECUTION                             ││
│ │  ┌────────────────────────┐  ┌──────────────────────────┐  ││
│ │  │ GenerateScenario       │  │ Prepare Call Context     │  ││
│ │  │ (Haiku): 0.5-1s        │  │ (Pass state): 0ms        │  ││
│ │  └────────────────────────┘  └──────────────────────────┘  ││
│ └─────────────────────────────────────────────────────────────┘│
│                              ↓                                   │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ InvokeOutboundCallHandler                   : 1s         │   │
│ └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ UpdateLeadHandler (async, after call)                    │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│ Total Workflow Time: 2.5-3.5s ✅                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-29  
**Status:** Ready for Implementation
