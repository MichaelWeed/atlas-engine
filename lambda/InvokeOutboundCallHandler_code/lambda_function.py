import json
import os
import boto3
import logging
import traceback
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

connect = boto3.client('connect')
dynamodb = boto3.resource('dynamodb')
sfn_client = boto3.client('stepfunctions')

def lambda_handler(event, context):
    logger.info(f"Full event: {json.dumps(event)}")
    task_token = None

    try:
        task_token = event['TaskToken']
        logger.info(f"Extracted TaskToken: {task_token[:10]}...")
        
        input_data = event['Input']
        logger.info(f"Input payload keys: {list(input_data.keys())}")
        
        # Log environment variables
        instance_id = os.environ['INSTANCE_ID']
        source_phone_number = os.environ['SOURCE_PHONE_NUMBER']
        contact_flow_id = os.environ['CONTACT_FLOW_ID']
        table_name = os.environ['INTERACTIONS_DYNAMODB_TABLE']
        logger.info(f"Env vars - InstanceId: {instance_id}, ContactFlowId: {contact_flow_id}, Table: {table_name}")
        
        table = dynamodb.Table(table_name)
        
        # Extract and validate input data
        phone_number = input_data.get('phone')
        if not phone_number:
            raise ValueError("Missing 'phone' in input")
        logger.info(f"Phone: {phone_number}")
        
        scenario = input_data.get('llm', {}).get('scenario')
        if scenario is None:
            raise ValueError("Missing 'llm.scenario' in input")
        scenario = scenario[:30000]
        logger.info(f"Scenario length: {len(scenario)}")
        
        lead_id = input_data.get('salesforce', {}).get('leadId')
        pk = input_data.get('salesforce', {}).get('partitionKey')
        sk = input_data.get('salesforce', {}).get('sortKey')
        if not all([lead_id, pk, sk]):
            raise ValueError(f"Missing salesforce data - leadId: {lead_id}, pk: {pk}, sk: {sk}")
        logger.info(f"Salesforce - LeadId: {lead_id}, PK: {pk}, SK: {sk}")
        
        # Store scenario in DynamoDB first (too large for Connect attributes)
        interaction_key = f"{pk}#{sk}"
        logger.info(f"Storing scenario in DynamoDB with key: {interaction_key}")
        table.put_item(
            Item={
                'PK': pk,
                'SK': sk,
                'DynamicScenario': scenario,
                'LeadId': lead_id,
                'StepFunctionTaskToken': task_token
            }
        )
        
        logger.info("Preparing to call connect.start_outbound_voice_contact...")
        response = connect.start_outbound_voice_contact(
            DestinationPhoneNumber=phone_number,
            ContactFlowId=contact_flow_id,
            InstanceId=instance_id,
            SourcePhoneNumber=source_phone_number,
            Attributes={
                'interactionKey': interaction_key,
                'leadId': lead_id
            }
        )

        contact_id = response['ContactId']
        logger.info(f"Call started. ContactId: {contact_id}")

        logger.info("Updating DynamoDB with ContactId...")
        table.update_item(
            Key={'PK': pk, 'SK': sk},
            UpdateExpression='SET ContactId = :cid',
            ExpressionAttributeValues={':cid': contact_id}
        )
        logger.info(f"DynamoDB updated. Function complete. PK={pk}, SK={sk}")

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'Call Initiated', 'ContactId': contact_id})
        }

    except Exception as e:
        logger.error(f"UNCAUGHT EXCEPTION: {str(e)}")
        logger.error(traceback.format_exc())
        
        error_type = type(e).__name__
        error_message = str(e)
        
        if task_token:
            try:
                sfn_client.send_task_failure(
                    taskToken=task_token,
                    error=error_type,
                    cause=error_message[:256]
                )
                logger.info("Sent task failure to Step Functions")
            except Exception as sfn_error:
                logger.error(f"Failed to send task failure: {str(sfn_error)}")
        
        raise
