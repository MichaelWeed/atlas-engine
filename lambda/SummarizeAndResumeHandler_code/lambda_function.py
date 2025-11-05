import json
import os
import logging
import boto3
from typing import Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError
from urllib.parse import urlparse
from requests.exceptions import RequestException

# Configure logging for structured JSON output
logger = logging.getLogger(__name__)
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level))

# Instantiate AWS clients outside handler for reuse
s3_client = boto3.client('s3')
bedrock_runtime = boto3.client('bedrock-runtime')
transcribe_client = boto3.client('transcribe')
dynamodb_client = boto3.client('dynamodb')
sfn_client = boto3.client('stepfunctions')

# Environment variables / Constants
INTERACTIONS_DYNAMODB_TABLE = os.environ.get('INTERACTIONS_DYNAMODB_TABLE')
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID')
MAX_INPUT_CHARS = 5000
MAX_TOKENS = 2000
ANTHROPIC_VERSION = os.environ.get('ANTHROPIC_VERSION')

def validate_event(event: Dict[str, Any]) -> Tuple[Optional[Dict[str, str]], str, str]:
    """
    Validate the input event structure and extract transcript info from Transcribe if COMPLETED.
    Returns: (transcript_info or None, job_name, status)
    Raises: ValueError on invalid structure or fetch failure.
    """
    if not isinstance(event, dict):
        raise ValueError("Event must be a dictionary")
    detail = event.get('detail', {})
    if not isinstance(detail, dict):
        raise ValueError("detail must be a dictionary")
    job_name = detail.get('TranscriptionJobName')
    if not job_name or not isinstance(job_name, str):
        raise ValueError("detail.TranscriptionJobName is required and must be a string")
    status = detail.get('TranscriptionJobStatus')
    if status not in ['COMPLETED', 'FAILED']:
        raise ValueError(f"TranscriptionJobStatus must be COMPLETED or FAILED, got: {status}")
    if status == 'FAILED':
        return None, job_name, status
    try:
        job_response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        transcript_uri = job_response['TranscriptionJob']['Transcript']['TranscriptFileUri']
        if not isinstance(transcript_uri, str) or not transcript_uri.startswith('https://s3.'):
            raise ValueError("Invalid TranscriptFileUri format")
        # Corrected parsing using urlparse
        parsed_url = urlparse(transcript_uri)
        path_parts = parsed_url.path.lstrip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError("Could not parse bucket/key from TranscriptFileUri")
        bucket = path_parts[0]
        key = '/'.join(path_parts[1:])
        logger.info(json.dumps({"event": "input_validated", "bucket": bucket, "key_prefix": key[:20] + '...', "contactId": job_name}))
        return {'bucket': bucket, 'key': key}, job_name, status
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(json.dumps({"event": "transcribe_error", "error_code": error_code, "job_name": job_name}))
        raise ValueError(f"Failed to fetch transcription job: {str(e)}")
    except KeyError as e:
        logger.error(json.dumps({"event": "transcribe_parse_error", "error": str(e), "job_name": job_name}))
        raise ValueError("Invalid transcription job response format")
    except Exception as e:
        logger.error(json.dumps({"event": "transcribe_error", "error": str(e), "job_name": job_name}))
        raise e

def get_transcript_from_s3(transcript_info: Dict[str, str]) -> str:
    """
    Retrieve and parse transcript from S3.
    Returns: Transcript text.
    Raises: ClientError or ValueError.
    """
    bucket = transcript_info['bucket']
    key = transcript_info['key']
    try:
        logger.info(json.dumps({"event": "s3_retrieve_start", "bucket": bucket, "key": key}))
        s3_response = s3_client.get_object(Bucket=bucket, Key=key)
        content_bytes = s3_response['Body'].read()
        content_str = content_bytes.decode('utf-8')
        transcript_data = json.loads(content_str)
        transcripts = transcript_data.get('results', {}).get('transcripts', [])
        if not transcripts:
            full_transcript = ''
        else:
            full_transcript = transcripts[0].get('transcript', '')
        
        # Handle empty/short transcripts gracefully for conversational bots
        if not full_transcript or not isinstance(full_transcript, str) or len(full_transcript.strip()) < 10:
            logger.warning(json.dumps({"event": "short_transcript", "length": len(full_transcript.strip()) if full_transcript else 0}))
            full_transcript = "[No speech detected during call]"
        
        # Truncate if too long
        if len(full_transcript) > MAX_INPUT_CHARS:
            full_transcript = full_transcript[:MAX_INPUT_CHARS] + "... [truncated]"
            logger.warning(json.dumps({"event": "transcript_truncated", "original_length": len(full_transcript) + 3, "truncated_length": MAX_INPUT_CHARS}))
        logger.info(json.dumps({"event": "transcript_retrieved", "transcript_length": len(full_transcript)}))
        return full_transcript.strip()
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(json.dumps({"event": "s3_error", "error_code": error_code, "bucket": bucket, "key": key}))
        raise e
    except Exception as e:
        logger.error(json.dumps({"event": "s3_error", "error": str(e), "bucket": bucket, "key": key}))
        raise e

def generate_summary_with_bedrock(transcript: str) -> str:
    """
    Generate summary using Bedrock Claude.
    Returns: Summary text.
    Raises: ClientError or ValueError.
    """
    prompt = f"""Please analyze this call transcript and provide a concise summary in the format of 3 bullet points below. NEVER comment on the transcript I give you. Separate by spaeker if available. Use specific phrases or names as expressed, and you can remain generic if the transcript is generic:
• Key topics discussed
• Important decisions or outcomes
• Next steps or action items
Transcript:
{transcript}
Summary:"""
    try:
        logger.info(json.dumps({"event": "bedrock_start", "model_id": BEDROCK_MODEL_ID, "transcript_length": len(transcript)}))
        body = json.dumps({
            "anthropic_version": ANTHROPIC_VERSION,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "top_p": 0.9
        })
        bedrock_response = bedrock_runtime.invoke_model(
            body=body,
            modelId=BEDROCK_MODEL_ID,
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(bedrock_response.get('body').read())
        content = response_body.get('content', [])
        if not content or not isinstance(content, list):
            raise ValueError("Invalid Bedrock response format")
        summary = content[0].get('text', '').strip()
        if not summary:
            raise ValueError("Empty summary generated")
        logger.info(json.dumps({"event": "summary_generated", "summary_length": len(summary)}))
        return summary
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(json.dumps({"event": "bedrock_error", "error_code": error_code}))
        raise e
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(json.dumps({"event": "bedrock_parse_error", "error": str(e)}))
        raise ValueError("Invalid Bedrock response format.")
    except Exception as e:
        logger.error(json.dumps({"event": "bedrock_error", "error": str(e)}))
        raise e

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler: Handles two invocation modes.
    - EventBridge from Transcribe: Retrieves transcript if COMPLETED, summarizes via Bedrock, resumes Step Functions.
    - Direct from Step Functions: Fetches transcript by bucket/key, summarizes, returns output.
    Handles FAILED by sending task failure.
    """
    logger.info(f"Full event: {json.dumps(event)}")
    logger.info(json.dumps({"event": "handler_start", "input_keys": list(event.keys())}))
    task_token = None
    is_callback = 'detail' in event
    try:
        if is_callback:
            # EventBridge callback mode
            transcript_info, contact_id, status = validate_event(event)
            # Query DynamoDB using ContactId GSI
            query_response = dynamodb_client.query(
                TableName=INTERACTIONS_DYNAMODB_TABLE,
                IndexName='ContactId-index',
                KeyConditionExpression='ContactId = :cid',
                ExpressionAttributeValues={':cid': {'S': contact_id}}
            )
            if not query_response.get('Items'):
                raise ValueError(f"No interaction record found for ContactId: {contact_id}")
            item = query_response['Items'][0]
            
            # Handle both low-level ({'S': 'value'}) and high-level ('value') formats
            if 'StepFunctionTaskToken' not in item:
                logger.warning(json.dumps({"event": "task_token_missing", "contactId": contact_id, "message": "Task token already processed or missing"}))
                return {'statusCode': 200, 'body': json.dumps({"status": "SKIPPED", "message": "Task token not found, likely already processed"})}
            
            task_token = item['StepFunctionTaskToken'].get('S') if isinstance(item['StepFunctionTaskToken'], dict) else item['StepFunctionTaskToken']
            partition_key = item['PK'].get('S') if isinstance(item['PK'], dict) else item['PK']
            sort_key = item['SK'].get('S') if isinstance(item['SK'], dict) else item['SK']
            lead_id = partition_key.split('#')[1]
            logger.info(json.dumps({"event": "dynamodb_queried", "contactId": contact_id, "leadId": lead_id}))
            
            detail = event.get('detail', {})
            if status == 'COMPLETED':
                full_transcript = get_transcript_from_s3(transcript_info)
                summary = generate_summary_with_bedrock(full_transcript)
                
                output_payload = {
                    "summary": summary,
                    "leadId": lead_id,
                    "transcriptBucket": transcript_info['bucket'],
                    "transcriptKey": transcript_info['key']
                }
                sfn_client.send_task_success(
                    taskToken=task_token,
                    output=json.dumps(output_payload)
                )
                logger.info(json.dumps({"event": "sfn_success_sent", "leadId": lead_id}))
                
                # Update DynamoDB: add summary and transcript, remove task token
                dynamodb_client.update_item(
                    TableName=INTERACTIONS_DYNAMODB_TABLE,
                    Key={'PK': {'S': partition_key}, 'SK': {'S': sort_key}},
                    UpdateExpression='SET CallSummary = :s, FullTranscript = :t REMOVE StepFunctionTaskToken',
                    ExpressionAttributeValues={
                        ':s': {'S': summary},
                        ':t': {'S': full_transcript}
                    }
                )
                logger.info(json.dumps({"event": "dynamodb_updated", "message": "Final record updated and task token removed"}))
            elif status == 'FAILED':
                failure_reason = detail.get('FailureReason', 'Unknown')
                sfn_client.send_task_failure(
                    taskToken=task_token,
                    error="TranscriptionFailed",
                    cause=failure_reason
                )
                logger.error(json.dumps({"event": "sfn_failure_sent", "reason": failure_reason, "contactId": contact_id}))
            return {
                'statusCode': 200,
                'body': json.dumps({
                    "status": "SUCCESS" if status == 'COMPLETED' else "FAILED",
                    "contactId": contact_id,
                    "message": "Step Functions notified."
                })
            }
        else:
            # Direct Step Functions invoke mode
            if not all(key in event for key in ['transcriptBucket', 'transcriptKey', 'leadId']):
                raise ValueError("Direct invoke requires transcriptBucket, transcriptKey, and leadId")
            bucket = event['transcriptBucket']
            key = event['transcriptKey']
            lead_id = event['leadId']
            transcript_info = {'bucket': bucket, 'key': key}
            full_transcript = get_transcript_from_s3(transcript_info)
            summary = generate_summary_with_bedrock(full_transcript)
            logger.info(json.dumps({"event": "direct_summary_generated", "leadId": lead_id}))
            return {
                'statusCode': 200,
                'body': json.dumps({
                    "summary": summary,
                    "leadId": lead_id
                })
            }
    except Exception as e:
        logger.error(json.dumps({"event": "handler_error", "error": str(e), "is_callback": is_callback}))
        if task_token:
            try:
                sfn_client.send_task_failure(
                    taskToken=task_token,
                    error=type(e).__name__,
                    cause=str(e)
                )
                logger.info(json.dumps({"event": "sfn_failure_sent_on_error"}))
            except Exception as sfn_err:
                logger.error(json.dumps({"event": "sfn_failure_error", "error": str(sfn_err)}))
        raise e