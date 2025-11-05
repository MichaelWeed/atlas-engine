import json
import os
import boto3
import time
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed

# Global caching for Salesforce connection
secrets_manager = boto3.client('secretsmanager')
sf = None
last_auth_time = 0
AUTH_CACHE_DURATION = 1800  # 30 minutes

def get_salesforce_client():
    """Cached Salesforce client initialization."""
    global sf, last_auth_time
    current_time = time.time()
    
    if sf and (current_time - last_auth_time < AUTH_CACHE_DURATION):
        print(f"[{time.strftime('%H:%M:%S')}] Using cached Salesforce client.")
        return sf
    
    print(f"[{time.strftime('%H:%M:%S')}] Authenticating to Salesforce (no cache)...")
    secret_name = os.environ['SALESFORCE_SECRET_ARN']
    try:
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        # No domain - defaults to 'login' for production orgs
        sf = Salesforce(
            username=secret['username'],
            consumer_key=secret['client_id'],
            privatekey=secret['private_key']
        )
        last_auth_time = current_time
        print(f"[{time.strftime('%H:%M:%S')}] Salesforce authenticated successfully.")
        return sf
        
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Salesforce auth error: {str(e)}")
        raise SalesforceAuthenticationFailed(f"Auth failed: {str(e)}")

def lambda_handler(event, context):
    print(f"[{time.strftime('%H:%M:%S')}] UpdateLeadHandler started. Event keys: {list(event.keys())}")
    try:
        lead_id = event.get('leadId')
        summary = event.get('summary', 'No summary provided')
        
        if not lead_id:
            raise ValueError("Missing leadId in event")
        
        print(f"[{time.strftime('%H:%M:%S')}] Updating Lead {lead_id} with summary (length: {len(str(summary))})")
        
        sf_client = get_salesforce_client()
        
        update_payload = {'Description': str(summary)}  # Ensure string
        
        print(f"[{time.strftime('%H:%M:%S')}] Calling Salesforce API...")
        result_status = sf_client.Lead.update(lead_id, update_payload)
        
        if result_status == 204:
            print(f"[{time.strftime('%H:%M:%S')}] Success: Lead {lead_id} updated.")
            return {"status": "success", "leadId": lead_id, "updatedAt": time.strftime('%Y-%m-%d %H:%M:%S')}
        else:
            raise Exception(f"API returned {result_status}, expected 204")
            
    except SalesforceAuthenticationFailed as e:
        print(f"[{time.strftime('%H:%M:%S')}] Auth failed: {str(e)}")
        raise
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Update error: {str(e)}")
        raise
