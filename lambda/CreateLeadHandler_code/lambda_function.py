import json
import logging
import boto3
import os
from datetime import datetime, timezone
from simple_salesforce import Salesforce
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto3 clients
secrets_client = boto3.client('secretsmanager')
dynamodb_client = boto3.client('dynamodb')

def get_salesforce_credentials(secret_arn):
    """
    Retrieve Salesforce JWT credentials from AWS Secrets Manager.
    """
    try:
        logger.info(f"Retrieving credentials from secret: {secret_arn}")
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_string = response['SecretString']  # Corrected: Extract 'SecretString'
        credentials = json.loads(secret_string)
        
        # Validate that all required credentials for JWT flow are present
        required_keys = ['username', 'client_id', 'private_key']
        for key in required_keys:
            if key not in credentials:
                raise ValueError(f"Missing required credential for JWT flow: {key}")
        
        logger.info("Successfully retrieved Salesforce JWT credentials")
        return credentials
    
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving credentials: {e}")
        raise

def lambda_handler(event, context):
    """
    AWS Lambda function to find or create a Lead in Salesforce using JWT Bearer Flow.
    This function is invoked by AWS Step Functions.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Get the secret ARN from an environment variable
        secret_arn = os.environ.get('SALESFORCE_SECRET_ARN')
        if not secret_arn:
            raise ValueError("SALESFORCE_SECRET_ARN environment variable not set.")
        
        # Retrieve Salesforce credentials from Secrets Manager
        credentials = get_salesforce_credentials(secret_arn)
        
        # Extract input data from the Step Functions event
        first_name = event.get('firstName')
        last_name = event.get('lastName')
        phone = event.get('phone')
        
        if not all([first_name, last_name, phone]):
            raise ValueError("Missing required input fields: firstName, lastName, and phone are required")
        
        logger.info(f"Processing Lead for: {first_name} {last_name}, Phone: {phone}")
        
        # Authenticate with Salesforce using JWT Bearer Flow
        sf = Salesforce(
            username=credentials['username'],
            consumer_key=credentials['client_id'],
            privatekey=credentials['private_key']
        )
        
        logger.info("Successfully authenticated with Salesforce using JWT Flow")
        
        # --- NEW: Idempotency Check ---
        # First, query for an existing Lead with the same phone number
        logger.info(f"Searching for existing Lead with phone number: {phone}")
        query = f"SELECT Id FROM Lead WHERE Phone = '{phone}' LIMIT 1"
        query_result = sf.query(query)
        
        if query_result.get('totalSize', 0) > 0:
            # If a Lead is found, extract the ID and return it immediately.
            lead_id = query_result['records'][0]['Id']  # Corrected: Access first record in list
            logger.info(f"Found existing Lead with ID: {lead_id}. Returning this ID.")
        else:
            # If no lead was found, proceed to create a new one.
            logger.info("No existing Lead found. Creating a new Lead.")
            
            # Construct the Lead record
            lead_data = {
                'FirstName': first_name,
                'LastName': last_name,
                'Phone': phone,
                'Company': 'Atlas Engine Demo'
            }
            
            logger.info(f"Creating Lead with data: {lead_data}")
            
            # Insert the new Lead into Salesforce
            result = sf.Lead.create(lead_data)
            
            lead_id = result.get('id')
            if not lead_id:
                raise Exception(f"Lead creation failed. Salesforce response: {result}")
            
            logger.info(f"Successfully created new Lead with ID: {lead_id}")
        
        # Write to DynamoDB AtlasEngineInteractions table
        interactions_table = os.environ['INTERACTIONS_DYNAMODB_TABLE']
        partition_key = f"LEAD#{event.get('phone')}"
        sort_key = f"INTERACTION#{datetime.now(timezone.utc).isoformat()}"
        
        dynamodb_client.put_item(
            TableName=interactions_table,
            Item={
                'PK': {'S': partition_key},
                'SK': {'S': sort_key},
                'SalesforceLeadID': {'S': lead_id},
                'InteractionType': {'S': 'CHAT_AND_CALL'},
                'InitialTranscript': {'S': json.dumps(event.get('lexTranscript', {}))}
            }
        )
        
        logger.info("Successfully created interaction record in DynamoDB")
        
        return {
            'leadId': lead_id,
            'partitionKey': partition_key,
            'sortKey': sort_key
        }
        # --- End of New Logic ---
    
    except Exception as e:
        logger.error(f"Error processing Salesforce Lead: {str(e)}")
        # This will cause the Step Function execution to fail, which is what we want for error handling.
        raise