import boto3
import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

connect_client = boto3.client('connect')
sfn_client = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('TASK_TOKENS_TABLE', 'AtlasEngineTaskTokens'))

def lambda_handler(event, context):
    """
    Initiates an outbound call and stores the mapping of ContactId to the
    Step Functions Task Token. If any step fails, it sends a failure
    signal back to the paused Step Function.
    """
    # The Step Function passes the state data inside an 'input' object
    # and the token at the top level.
    payload = event.get('input', {})
    task_token = event.get('taskToken')

    try:
        # Retrieve environment variables
        connect_instance_id = os.environ.get('CONNECT_INSTANCE_ID')
        contact_flow_id = os.environ.get('CONTACT_FLOW_ID')
        source_phone_number = os.environ.get('SOURCE_PHONE_NUMBER')

        # Get data from the payload
        destination_phone_number = payload.get('phone')
        ai_scenario = payload.get('aiResult', {}).get('scenario', 'Hello. This is a default message.')
        lead_id = payload.get('salesforceResult', {}).get('leadId')

        if not all([task_token, lead_id, destination_phone_number]):
            raise ValueError("Missing required data: TaskToken, LeadId, or phone number.")

        logger.info(f"Initiating call to {destination_phone_number} for Lead ID {lead_id}.")

        # --- Your call initiation logic here ---
        response = connect_client.start_outbound_voice_contact(
            InstanceId=connect_instance_id,
            ContactFlowId=contact_flow_id,
            DestinationPhoneNumber=destination_phone_number,
            SourcePhoneNumber=source_phone_number,
            Attributes={
                'dynamicScenario': ai_scenario
            }
        )
        
        contact_id = response['ContactId']
        logger.info(f"Successfully initiated call with ContactId: {contact_id}")

        # Store the mapping in DynamoDB to link the call to the paused workflow
        table.put_item(
            Item={
                'ContactId': contact_id,
                'TaskToken': task_token,
                'LeadId': lead_id
            }
        )
        logger.info(f"Stored mapping for ContactId {contact_id} in DynamoDB.")

        # Return an empty object. The function's job is done.
        # The Step Function will remain paused, waiting for the callback.
        return {}

    except Exception as e:
        logger.error(f"Error during call initiation: {e}")
        
        # --- Send failure back to Step Functions ---
        sfn_client.send_task_failure(
            taskToken=task_token,
            error='CallInitiationFailed',
            cause=str(e)
        )
        # Re-raise the exception to ensure the Lambda execution itself is marked as failed.
        raise e