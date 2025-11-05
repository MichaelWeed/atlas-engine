import json
import boto3

bedrock_client = boto3.client('bedrock-runtime', region_name='us-west-2')
HAIKU_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'

# Test the exact prompt from the Lambda
base_context = "Hi there! I'm Michael's AI assistant showcasing enterprise-grade conversational AI. Ready to see something impressive? Just say 'start demo' to begin!"
history = "User: (Initiated conversation)\n"
user_input = "Hello"

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
    "max_tokens": 150,
    "temperature": 0.7,
    "system": "You are Atlas, an AI assistant. Be concise and helpful.",
    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
})

print("Testing Haiku output with current prompt...\n")
print("=" * 80)

for i in range(10):
    try:
        response = bedrock_client.invoke_model(
            body=body,
            modelId=HAIKU_MODEL_ID,
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        generated_text = response_body.get('content')[0].get('text')
        
        print(f"\nTest {i+1}:")
        print(f"Output: {repr(generated_text)}")
        print(f"Stripped: {repr(generated_text.strip())}")
        
        # Check for XML tags
        if '<' in generated_text or '>' in generated_text:
            print("⚠️  WARNING: Contains angle brackets!")
        
    except Exception as e:
        print(f"\nTest {i+1} FAILED: {e}")

print("\n" + "=" * 80)
