import json
import os
import boto3
import phonenumbers
import logging
import requests
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import SalesforceAuthenticationFailed
from jwt import encode, decode
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# ===== NEW: Setup Logging =====
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ===== Initialize clients/resources =====
stepfunctions_client = boto3.client('stepfunctions')
bedrock_client = boto3.client('bedrock-runtime')
sns_client = boto3.client('sns')

# ===== NEW: Bedrock Model ID from Env Vars =====
# Using Haiku for faster response times on voice calls
ANTHROPIC_MODEL_ID = os.environ.get('ANTHROPIC_MODEL_ID', 'anthropic.claude-3-5-haiku-20241022-v1:0')
SALES_TEAM_TOPIC_ARN = os.environ.get('SALES_TEAM_TOPIC_ARN')

# ===== Conversation History Helper =====
def update_conversation_history(event, session_state, bot_response, max_turns=10):
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    conversation_history = session_attributes.get('conversationHistory', '')
    user_input = event.get('inputTranscript', '')
    
    # Check if this exact exchange already exists at the end
    last_line = conversation_history.strip().split('\n')[-1] if conversation_history.strip() else ''
    if last_line == f"Bot: {bot_response}":
        return conversation_history  # Already added, don't duplicate
    
    new_turn = f"User: {user_input}\nBot: {bot_response}\n"
    updated_history = (conversation_history + new_turn).splitlines()
    trimmed_history = "\n".join(updated_history[-max_turns*2:])
    return trimmed_history

# ===== Salesforce auth (full JWT from Session 2) =====
def get_sf_connection():
    secret_arn = os.environ['SALESFORCE_SECRET_ARN']
    secrets_client = boto3.client('secretsmanager')
    secret = secrets_client.get_secret_value(SecretId=secret_arn)
    creds = json.loads(secret['SecretString'])
    
    # Determine the OAuth endpoint (sandbox vs production)
    is_sandbox = creds.get('is_sandbox', False)  # Add this to your secret if using sandbox
    endpoint = 'https://test.salesforce.com' if is_sandbox else 'https://login.salesforce.com'
    
    # Step 1: Create the JWT
    now = datetime.utcnow()
    payload = {
        'iss': creds['client_id'],
        'sub': creds['username'],
        'aud': endpoint,
        'exp': now + timedelta(minutes=5)
    }
    
    private_key = creds['private_key']
    jwt_token = encode(payload, private_key, algorithm='RS256')
    
    # Step 2: Exchange JWT for access token
    result = requests.post(
        endpoint + '/services/oauth2/token',
        data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
            'assertion': jwt_token
        }
    )
    
    body = result.json()
    
    if result.status_code != 200:
        logger.error(f"[SF AUTH] JWT exchange failed: {body}")
        raise SalesforceAuthenticationFailed(body.get('error', 'Unknown'), 
                                            body.get('error_description', 'JWT token exchange failed'))
    
    # Step 3: Initialize Salesforce with the access token and instance URL
    logger.info(f"[SF AUTH] Successfully authenticated. Instance: {body['instance_url']}")
    return Salesforce(instance_url=body['instance_url'], session_id=body['access_token'])

# ============================================================================
# ===== NEW: GENERATIVE RESPONSE HANDLER =====
# ============================================================================
def generate_dynamic_response(base_context, history, user_input):
    """
    Uses Bedrock to rephrase a static response based on conversation context.
    """
    logger.info(f"[Bedrock] Generating dynamic response. User input: {user_input}")

    # If history is empty, just use a simple greeting.
    if not history:
        history = "User: (Initiated conversation)\n"
        
    # The prompt is key. We "ground" the AI with our static context.
    prompt = f"""
Human: You are Atlas, an enterprise AI assistant part of the Atlas Engine. A user is talking to you.
Your *only* goal is to provide the information in the <grounding_context> in a natural, conversational way.
- First, briefly and naturally acknowledge the user's last message.
- Then, conversationally deliver the information from the <grounding_context>.
- Do NOT add any new information or answer questions that are not in the context.
- Be concise. Keep the response to 1-3 sentences.
- Do NOT include any <tags> in your final response.
- Your main goal is to get the user to ask for "the creator".

<conversation_history>
{history}User: {user_input}
</conversation_history>

<grounding_context>
{base_context}
</grounding_context>

A:"""

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "system": "IMPORTANT: You are an AI assistant named Atlas, from the Atlas Engine. You are NOT a human. You MUST NEVER, under any circumstances, claim to be a real person. Always refer to yourself as an AI assistant. Your goal is to be helpful and conversational, encouraging them to ask to speak to the creator.",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    })
    
    try:
        response = bedrock_client.invoke_model(
            body=body,
            modelId=ANTHROPIC_MODEL_ID,
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        generated_text = response_body.get('content')[0].get('text')
        
        logger.info(f"[Bedrock] Generated text: {generated_text}")
        return generated_text.strip()
        
    except Exception as e:
        logger.error(f"[Bedrock] Error invoking model: {e}")
        # Fallback to the static content if Bedrock fails
        return base_context

# ============================================================================
# INTENT HANDLERS (Now with Generative Responses)
# ============================================================================

def handle_greeting_intent(event, session_state, intent_name):
    logger.info(f"[HANDLER] GreetingIntent triggered")
    
    # This is the static, "ground truth" response
    base_context = "Hi there! I'm Michael's AI assistant showcasing enterprise-grade conversational AI. Ready to see something impressive? Just say 'start demo' to begin!"
    
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    history = session_attributes.get('conversationHistory', '')
    user_input = event.get('inputTranscript', '')

    # Generate the dynamic response
    content = generate_dynamic_response(base_context, history, user_input)
    
    updated_history = update_conversation_history(event, session_state, content)
    logger.info(f"[HISTORY] Updated conversation history:\n{updated_history}")
    
    # Check if this is a dialog code hook (invocationSource)
    invocation_source = event.get('invocationSource', 'FulfillmentCodeHook')
    if invocation_source == 'DialogCodeHook':
        return {
            'sessionState': {
                'dialogAction': {'type': 'ElicitIntent'},
                'intent': {'name': intent_name, 'state': 'Fulfilled'},
                'sessionAttributes': {'conversationHistory': updated_history}
            },
            'messages': [{'contentType': 'PlainText', 'content': content}]
        }
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': {'conversationHistory': updated_history}
        },
        'messages': [{'contentType': 'PlainText', 'content': content}]
    }

def handle_about_technology_intent(event, session_state, intent_name):
    logger.info(f"[HANDLER] AboutTechnologyIntent triggered")
    
    base_context = (
        "This demo leverages AWS serverless architecture: Amazon Lex for natural language understanding, "
        "Lambda for compute, Step Functions for orchestration, Bedrock for AI, and Amazon Connect for outbound calling. "
        "Everything integrates with Salesforce in real-time. For complete architecture details including C4 diagrams and code, "
        "check out the full documentation linked from the demo site."
    )
    
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    history = session_attributes.get('conversationHistory', '')
    user_input = event.get('inputTranscript', '')

    content = generate_dynamic_response(base_context, history, user_input)
    
    updated_history = update_conversation_history(event, session_state, content)
    logger.info(f"[HISTORY] Updated conversation history:\n{updated_history}")
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': {'conversationHistory': updated_history}
        },
        'messages': [{'contentType': 'PlainText', 'content': content}]
    }

def handle_about_demo_intent(event, session_state, intent_name):
    logger.info(f"[HANDLER] AboutDemoIntent triggered")
    
    base_context = (
        "This is an end-to-end sales acceleration workflow: AI-powered outbound calling with real-time Salesforce integration, "
        "personalized conversations using customer data, and intelligent lead qualification. It's an enterprise-grade prototype "
        "delivered in record time, demonstrating how modern serverless architecture enables rapid innovation without sacrificing quality."
    )
    
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    history = session_attributes.get('conversationHistory', '')
    user_input = event.get('inputTranscript', '')

    content = generate_dynamic_response(base_context, history, user_input)
    
    updated_history = update_conversation_history(event, session_state, content)
    logger.info(f"[HISTORY] Updated conversation history:\n{updated_history}")
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': {'conversationHistory': updated_history}
        },
        'messages': [{'contentType': 'PlainText', 'content': content}]
    }

def handle_delete_my_info_intent(event, session_state, intent_name):
    logger.info(f"[HANDLER] DeleteMyInfoIntent triggered")
    slots = session_state.get('intent', {}).get('slots', {})
    
    # Extract BOTH slots for security
    phone_slot = slots.get('VisitorPhoneNumber')
    last_name_slot = slots.get('VisitorLastName')
    
    if (phone_slot and 'value' in phone_slot and 
        last_name_slot and 'value' in last_name_slot):
        
        phone_number_raw = phone_slot['value'].get('interpretedValue')
        last_name_raw = last_name_slot['value'].get('interpretedValue')

        try:
            # Validate and format phone number
            parsed_number = phonenumbers.parse(phone_number_raw, "US")
            e164_phone = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            
            # Sanitize last name - SOQL escaping + case-insensitive
            last_name = last_name_raw.strip().title()  # Normalize: "smith" -> "Smith"
            safe_last_name = last_name.replace("'", "''")  # FIXED: SOQL uses '' not \'
            
            logger.info(f"[DELETE] Attempting to find Lead with phone: {e164_phone} AND LastName: {last_name}")
            
            # Query with both phone AND last name for security
            sf = get_sf_connection()
            query = f"SELECT Id FROM Lead WHERE Phone = '{e164_phone}' AND LastName = '{safe_last_name}' LIMIT 1"
            logger.info(f"[DELETE] SOQL Query: {query}")
            
            query_result = sf.query(query)
            
            if query_result['totalSize'] > 0:
                lead_id = query_result['records'][0]['Id']
                sf.Lead.delete(lead_id)
                logger.info(f"[DELETE] Successfully deleted Lead: {lead_id}")
                content = "Your information has been successfully verified and completely removed from our systems. This demonstrates our commitment to data privacy and compliance - essential for enterprise solutions."
            else:
                logger.info(f"[DELETE] No Lead found matching criteria.")
                content = "I was unable to find a record matching that phone number and last name. Please verify your information and try again."
        
        except Exception as e:
            logger.error(f"[ERROR] Delete operation failed: {e}")
            content = "I encountered an issue processing your deletion request. Please contact support if this persists."
    else:
        logger.warning("[DELETE] Intent fulfilled but required slots were missing.")
        content = "I need both your phone number and last name to securely verify and delete your information. Please provide both."

    # STATIC RESPONSE - No AI generation for compliance-critical operations
    updated_history = update_conversation_history(event, session_state, content)
    logger.info(f"[HISTORY] Updated conversation history:\n{updated_history}")
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': {'conversationHistory': updated_history}
        },
        'messages': [{'contentType': 'PlainText', 'content': content}]
    }

def handle_fallback_intent(event, session_state, intent_name):
    logger.info(f"[HANDLER] FallbackIntent triggered")
    
    base_context = (
        "I didn't quite catch that. Here's what I can help with: Say 'start demo' to begin the experience, "
        "ask 'what technology powers this' for technical details, 'tell me about the demo' for an overview, "
        "or 'delete my info' to remove your data. What would you like to do?"
    )
    
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    history = session_attributes.get('conversationHistory', '')
    user_input = event.get('inputTranscript', '')

    content = generate_dynamic_response(base_context, history, user_input)
    
    updated_history = update_conversation_history(event, session_state, content)
    logger.info(f"[HISTORY] Updated conversation history:\n{updated_history}")
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': {'conversationHistory': updated_history}
        },
        'messages': [{'contentType': 'PlainText', 'content': content}]
    }

def handle_close_intent(event, session_state, intent_name):
    logger.info("[HANDLER] Handling CloseIntent")
    
    response_message = "Thank you for your time. Have a great day!"
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': session_state.get('sessionAttributes', {})
        },
        'messages': [{'contentType': 'PlainText', 'content': response_message}]
    }

def handle_callback_intent(event, session_state, intent_name, dynamodb_item=None):
    logger.info("[HANDLER] Handling CallbackIntent")
    
    if not dynamodb_item:
        logger.error("[HANDLER] No DynamoDB item provided")
        response_message = "I'm sorry, I ran into an internal error. Please try again later."
        fulfillment_state = "Failed"
    else:
        lead_id = dynamodb_item.get('LeadId')
        if not lead_id:
            logger.error("[HANDLER] No LeadId found in DynamoDB item")
            response_message = "I'm sorry, I ran into an internal error. Please try again later."
            fulfillment_state = "Failed"
        else:
            try:
                sf = get_sf_connection()
                case_data = {
                    'Subject': 'Atlas Engine: Callback Request',
                    'Description': f'User requested a callback ("talk to creator") during the outbound AI call. Lead ID: {lead_id}',
                    'Status': 'New',
                    'Origin': 'Phone (AI)'
                }
                result = sf.Case.create(case_data)
                logger.info(f"[HANDLER] Successfully created Case {result['id']} for Lead {lead_id}")
                response_message = "Thank you. I've created a priority request for our team, and someone will call you back shortly. Have a great day."
                fulfillment_state = "Fulfilled"
            except Exception as e:
                logger.error(f"[HANDLER] Failed to create Salesforce Case: {str(e)}")
                response_message = "I'm sorry, I ran into an error trying to process your request. Please try again."
                fulfillment_state = "Failed"

    # Return a 'Close' dialog action and clear session to end call
    return {
        'sessionState': {
            'dialogAction': {'type': 'Close'},
            'intent': {'name': intent_name, 'state': fulfillment_state},
            'sessionAttributes': {}  # Clear all session attributes to end the session
        },
        'messages': [{'contentType': 'PlainText', 'content': response_message}]
    }

def handle_initiate_demo_intent(event, session_state, intent_name):
    # --- THIS INTENT REMAINS STATIC ---
    # This is the final step of the funnel; we want a clear, consistent message.
    logger.info(f"[HANDLER] InitiateDemo triggered")
    state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
    logger.info(f"[CONFIG] State Machine ARN: {state_machine_arn}")
    slots = session_state.get('intent', {}).get('slots', {})
    
    full_name_slot = slots.get('VisitorFullName')
    phone_number_slot = slots.get('VisitorPhoneNumber')
    
    if not (full_name_slot and phone_number_slot and 'value' in full_name_slot and 'value' in phone_number_slot):
        logger.error("Error: Slots are missing or malformed.")
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': intent_name, 'state': 'Failed'}
            },
            'messages': [{'contentType': 'PlainText', 'content': 'Sorry, there was an error processing your information.'}]
        }
        
    full_name = full_name_slot['value'].get('interpretedValue')
    phone_number_raw = phone_number_slot['value'].get('interpretedValue')
    
    if not all([full_name, phone_number_raw]):
        logger.error("Error: Full name or phone number is missing from slots.")
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': intent_name, 'state': 'Failed'}
            },
            'messages': [{'contentType': 'PlainText', 'content': 'Sorry, there was an error processing your information.'}]
        }
        
    # --- PHONE NUMBER TRANSFORMATION ---
    try:
        parsed_number = phonenumbers.parse(phone_number_raw, "US")
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValueError("The provided phone number is not valid.")
        e164_phone_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        logger.info(f"[PHONE] Transformed '{phone_number_raw}' to E164: {e164_phone_number}")
    except Exception as e:
        logger.error(f"[ERROR] Phone validation failed for '{phone_number_raw}': {e}")
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': intent_name, 'state': 'Failed'}
            },
            'messages': [{'contentType': 'PlainText', 'content': 'Sorry, the phone number provided is invalid.'}]
        }
    # --- END TRANSFORMATION ---

    name_parts = full_name.strip().split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else 'LNU' # Use LNU for robustness
    logger.info(f"[PARSED] FirstName: '{first_name}', LastName: '{last_name}'")

    session_attributes = session_state.get('sessionAttributes', {}) or {}
    try:
        conversation_history = session_attributes.get('conversationHistory', '')
        user_input = event.get('inputTranscript', '')
        if user_input:
            conversation_history += f"User: {user_input}\n"
        
        history_lines = conversation_history.splitlines()
        limited_history = "\n".join(history_lines[-20:])
        logger.info(f"[HISTORY] Passing transcript to scenario generator:\n{limited_history}")
        
        sfn_input = {
            'firstName': first_name,
            'lastName': last_name,
            'phone': e164_phone_number,
            'chat_transcript': limited_history
        }

        logger.info(f"[SFN] Starting execution with input: {json.dumps(sfn_input)}")
        response = stepfunctions_client.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps(sfn_input)
        )
        logger.info(f"[SFN] Execution started: {response['executionArn']}")

        success_message = f"Thank you for your interest, {first_name}! I'll reach out within 2 minutes. Prefer scheduling tools like Calendly? Let me know during our call!"
        updated_history = update_conversation_history(event, session_state, success_message)
        logger.info(f"[HISTORY] Updated conversation history:\n{updated_history}")
        
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': intent_name, 'state': 'Fulfilled'},
                'sessionAttributes': {'conversationHistory': updated_history}
            },
            'messages': [{'contentType': 'PlainText', 'content': success_message}]
        }
    except Exception as e:
        logger.error(f"[ERROR] Step Function execution failed: {e}")
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': intent_name, 'state': 'Failed'},
                'sessionAttributes': session_attributes
            },
            'messages': [{'contentType': 'PlainText', 'content': 'Sorry, there was an error processing your request.'}]
        }

# ============================================================================
# PHONE CALL HANDLER - Uses dynamicScenario context
# ============================================================================

def handle_general_ai_conversation(event, session_state, scenario):
    """
    Handles conversational intents for phone calls using general AI (Bedrock).
    Uses the dynamicScenario context to generate personalized responses.
    This is the fallback for AboutTechnologyIntent, AboutDemoIntent, etc.
    """
    logger.info(f"[GENERAL AI] Processing conversational intent with scenario. Length: {len(scenario)}")
    
    user_input = event.get('inputTranscript', '')
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    conversation_history = session_attributes.get('conversationHistory', '')
    
    # Use the scenario as context for generating responses
    prompt = f"""
Human: You are conducting a personalized outbound sales call. Use the scenario below as your script and context.

<scenario>
{scenario}
</scenario>

<conversation_history>
{conversation_history}
</conversation_history>

User just said: {user_input}

Respond naturally and conversationally based on the scenario. Keep responses concise (1-2 sentences).

A:"""
    
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 150,
        "system": "You are Atlas, an AI sales assistant. Be concise and conversational.",
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    })
    
    try:
        response = bedrock_client.invoke_model(
            body=body,
            modelId=ANTHROPIC_MODEL_ID,
            contentType='application/json',
            accept='application/json'
        )
        response_body = json.loads(response.get('body').read())
        content = response_body.get('content')[0].get('text').strip()
        logger.info(f"[GENERAL AI] Generated response: {content}")
    except Exception as e:
        logger.error(f"[GENERAL AI] Bedrock error: {e}")
        content = "I'm here to discuss how our solution can help you. What questions do you have?"
    
    # Update conversation history
    conversation_history += f"User: {user_input}\nBot: {content}\n"
    session_attributes['conversationHistory'] = conversation_history
    session_attributes['dynamicScenario'] = scenario  # Preserve for next turn
    
    intent = session_state.get('intent', {})
    intent_name = intent.get('name', 'FallbackIntent')
    
    return {
        'sessionState': {
            'dialogAction': {'type': 'ElicitIntent'},
            'intent': {'name': intent_name, 'state': 'Fulfilled'},
            'sessionAttributes': session_attributes
        },
        'messages': [{'contentType': 'PlainText', 'content': content}]
    }

# ============================================================================
# MAIN HANDLER - ROUTER PATTERN
# ============================================================================

def lambda_handler(event, context):
    logger.info(f"[EVENT] Full event: {json.dumps(event, indent=2)}")
    
    session_state = event.get('sessionState', {})
    session_attributes = session_state.get('sessionAttributes', {}) or {}
    
    # DEBUG: Log all session attributes
    logger.info(f"[DEBUG] Session attributes keys: {list(session_attributes.keys())}")
    logger.info(f"[DEBUG] Session attributes: {json.dumps(session_attributes)}")
    
    # CHECK FOR PHONE CALL CONTEXT (from Amazon Connect)
    interaction_key = session_attributes.get('interactionKey')
    logger.info(f"[DEBUG] interactionKey: {interaction_key}")
    
    dynamic_scenario = None
    dynamodb_item = None
    if interaction_key:
        # Retrieve scenario from DynamoDB
        try:
            # interactionKey format: LEAD#<PHONE_NUMBER>#INTERACTION#2025-10-26T06:07:12.367643+00:00
            # Split into PK (LEAD#<PHONE_NUMBER>) and SK (INTERACTION#2025-10-26T06:07:12.367643+00:00)
            parts = interaction_key.split('#')
            if len(parts) >= 4:
                pk = f"{parts[0]}#{parts[1]}"  # LEAD#<PHONE_NUMBER>
                sk = '#'.join(parts[2:])  # INTERACTION#2025-10-26T06:07:12.367643+00:00
            elif len(parts) >= 2:
                pk, sk = interaction_key.split('#', 1)
            else:
                logger.error(f"[DEBUG] Invalid interactionKey format: {interaction_key}")
                raise ValueError(f"Invalid interactionKey format: {interaction_key}")
            
            logger.info(f"[DEBUG] Parsed interactionKey - PK: {pk}, SK: {sk}")
            
            table_name = os.environ.get('INTERACTIONS_DYNAMODB_TABLE')
            if not table_name:
                logger.error("[DEBUG] INTERACTIONS_DYNAMODB_TABLE environment variable not set")
                raise ValueError("INTERACTIONS_DYNAMODB_TABLE environment variable not set")
            
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(table_name)
            response = table.get_item(Key={'PK': pk, 'SK': sk})
            if 'Item' in response:
                dynamodb_item = response['Item']
                dynamic_scenario = dynamodb_item.get('DynamicScenario')
                logger.info(f"[DEBUG] Retrieved dynamicScenario from DynamoDB. Length: {len(dynamic_scenario) if dynamic_scenario else 0}")
                # Store in session for subsequent turns
                session_attributes['dynamicScenario'] = dynamic_scenario
            else:
                logger.warning(f"[DEBUG] No DynamoDB item found for key: {interaction_key}")
        except Exception as e:
            logger.error(f"[DEBUG] Error retrieving scenario from DynamoDB: {e}")
            import traceback
            logger.error(traceback.format_exc())
    else:
        # Check if already in session from previous turn
        dynamic_scenario = session_attributes.get('dynamicScenario')
        logger.info(f"[DEBUG] dynamicScenario from session: {dynamic_scenario[:100] if dynamic_scenario else 'None'}...")
    
    # Get intent name first (needed for both phone and web chat)
    intent = session_state.get('intent', {})
    intent_name = intent.get('name')
    logger.info(f"[ROUTER] Intent: {intent_name}")
    
    # PHONE CALL ROUTING - Check for command intents first
    if dynamic_scenario:
        logger.info("[ROUTER] Phone call detected with dynamicScenario")
        
        # Check for command intents that should NOT use general AI
        if intent_name == 'GreetingIntent':
            logger.info("[ROUTER] Phone call - routing to GreetingIntent handler")
            return handle_greeting_intent(event, session_state, intent_name)
        elif intent_name == 'CallbackIntent':
            logger.info("[ROUTER] Phone call - routing to CallbackIntent handler")
            return handle_callback_intent(event, session_state, intent_name, dynamodb_item)
        elif intent_name == 'CloseIntent':
            logger.info("[ROUTER] Phone call - routing to CloseIntent handler")
            return handle_close_intent(event, session_state, intent_name)
        else:
            # Fallback to general AI for conversational intents
            logger.info(f"[ROUTER] Phone call - routing {intent_name} to general AI handler")
            return handle_general_ai_conversation(event, session_state, dynamic_scenario)
    
    # WEB CHAT - Use normal intent routing
    logger.info("[ROUTER] Web chat detected - using standard intent handlers")
    
    if intent_name == 'InitiateDemo':
        return handle_initiate_demo_intent(event, session_state, intent_name)
    elif intent_name == 'GreetingIntent':
        return handle_greeting_intent(event, session_state, intent_name)
    elif intent_name == 'AboutTechnologyIntent':
        return handle_about_technology_intent(event, session_state, intent_name)
    elif intent_name == 'AboutDemoIntent':
        return handle_about_demo_intent(event, session_state, intent_name)
    elif intent_name == 'CallbackIntent':
        return handle_callback_intent(event, session_state, intent_name)
    elif intent_name == 'DeleteMyInfoIntent':
        return handle_delete_my_info_intent(event, session_state, intent_name)
    elif intent_name == 'FallbackIntent':
        return handle_fallback_intent(event, session_state, intent_name)
    else:
        logger.warning(f"[ROUTER] Unknown intent: {intent_name}")
        return {
            'sessionState': {
                'dialogAction': {'type': 'Close'},
                'intent': {'name': intent_name, 'state': 'Failed'},
                'sessionAttributes': session_state.get('sessionAttributes', {})
            },
            'messages': [{'contentType': 'PlainText', 'content': 'Sorry, I encountered an unexpected error.'}]
        }
