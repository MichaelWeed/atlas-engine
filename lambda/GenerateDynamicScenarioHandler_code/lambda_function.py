import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    model_id = os.environ.get('MODEL_ID')
    bedrock_runtime = boto3.client(service_name='bedrock-runtime')
except Exception as e:
    logger.error(f"Error initializing Bedrock client: {e}")
    bedrock_runtime = None

def lambda_handler(event, context):
    if not bedrock_runtime:
        return {'statusCode': 500, 'body': json.dumps({'error': 'Bedrock client not initialized.'})}

    first_name = event.get('firstName', 'Valued')
    last_name = event.get('lastName', 'Prospect')
    prospect_name = f"{first_name} {last_name}".strip()
    chat_transcript = event.get('chat_transcript', '')

    prompt = f"You are 'Atlas,' an AI assistant. Your goal is to re-engage a user who just interacted with your web-chat bot. You are calling them on the phone. You will be given their name and the full transcript of the web chat. Your task is to generate a *single, short, conversational* greeting (1-2 sentences) that:\n1. Greets them by name.\n2. Directly references the *core topic* of the chat.\n3. Asks an open-ended question to continue the conversation.\n\nExample: 'Hi [Name], this is Atlas. I'm calling about your interest in our sales accelerator. I saw you had questions about the architecture; what's on your mind?'\n\nName: {prospect_name}\nChat Transcript: {chat_transcript}"

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    })

    try:
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response.get('body').read())
        scenario_text = response_body.get('content', [{}])[0].get('text', '').strip()
        logger.info(f"Successfully generated scenario: {scenario_text[:100]}...")
        return {'scenario': scenario_text}
    except Exception as e:
        logger.error(f"Error invoking Bedrock model: {e}")
        return {'scenario': f"Hello {prospect_name}, this is Atlas from the AI demo, calling to follow up on our chat."}
