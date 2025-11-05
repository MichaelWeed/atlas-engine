# Quick Start: Fix Cold Starts in 5 Minutes

## What This Does

Sets up Lambda alias with provisioned concurrency and updates Lex to use it.

**Result:** Eliminates 3-5 second cold starts ✅

---

## Simple Explanation

**Version vs Alias:**
- **Version** = Snapshot of your code (like v1.0, v2.0)
- **Alias** = Pointer to a version (like "prod" → v28)

**Why use alias?**
- Lex points to alias "prod"
- When you update code, just move "prod" to new version
- Lex automatically uses new code (no Lex config change needed)

---

## Run These 3 Commands

```bash
cd /Users/johndoe/Downloads/aws_org_export

# 1. Setup Lambda alias with provisioned concurrency
./setup_lambda_alias.sh

# 2. Get your Lex bot IDs
./get_lex_info.sh

# 3. Update Lex to use the alias
./update_lex_to_use_alias.sh
```

**Total time:** 5 minutes (2-3 minutes waiting for provisioned concurrency)

---

## What Each Script Does

### 1. setup_lambda_alias.sh
- Creates alias "prod" pointing to version 28
- Configures provisioned concurrency on the alias
- Generates config file for Lex

### 2. get_lex_info.sh
- Finds your AtlasEngineBot
- Gets bot ID and alias ID
- Saves to lex_ids.txt

### 3. update_lex_to_use_alias.sh
- Updates Lex bot to use Lambda alias
- Uses the ARN with ":prod" at the end

---

## Verify It Worked

```bash
# Check provisioned concurrency status
aws lambda get-provisioned-concurrency-config \
  --function-name LexFulfillmentHandler:prod \
  --region us-west-2

# Should show: "Status": "READY"
```

Test your Lex bot - responses should be 3-5 seconds faster!

---

## Troubleshooting

**Error: "Alias already exists"**
- Script will update existing alias (this is fine)

**Error: "Bot not found"**
- Check bot name in get_lex_info.sh
- Run: `aws lexv2-models list-bots --region us-west-2`

**Error: "Permission denied"**
- Run: `chmod +x *.sh`

**Provisioned concurrency stuck at "IN_PROGRESS"**
- Wait 5 minutes, it takes time to provision
- Check status: `aws lambda get-provisioned-concurrency-config --function-name LexFulfillmentHandler:prod --region us-west-2`

---

## Next Steps

After this works:
1. Monitor CloudWatch for 1 hour
2. Verify cold starts are gone
3. Move to Phase 1 remaining tasks (secrets caching, etc.)

---

## Rollback (if needed)

```bash
# Point Lex back to $LATEST
aws lexv2-models update-bot-alias \
  --bot-id <BOT_ID> \
  --bot-alias-id <ALIAS_ID> \
  --bot-alias-locale-settings '{
    "en_US": {
      "enabled": true,
      "codeHookSpecification": {
        "lambdaCodeHook": {
          "lambdaARN": "arn:aws:lambda:us-west-2:<AWS_ACCOUNT_ID>:function:LexFulfillmentHandler",
          "codeHookInterfaceVersion": "1.0"
        }
      }
    }
  }' \
  --region us-west-2
```

---

**Questions?** Just run the scripts and see what happens. They're safe and can be rolled back.
