import boto3
import json
import urllib.parse
import re

def lambda_handler(event, context):
    """
    Lambda function triggered by S3 .wav file uploads to start Transcribe jobs.
    Extracts ContactId from filename and uses it as the job name.
    """
    
    # PRIORITY 1: Log full event structure for debugging
    print("=== RAW EVENT STRUCTURE ===")
    print(json.dumps(event, indent=2))
    print("=== END RAW EVENT ===")
    
    transcribe = boto3.client('transcribe')
    
    try:
        # Check if Records exist in event
        if 'Records' not in event:
            raise ValueError("No 'Records' found in event structure")
        
        if not event['Records']:
            raise ValueError("Records array is empty")
        
        # Process each record (typically one for S3 events)
        for i, record in enumerate(event['Records']):
            print(f"Processing record {i+1}/{len(event['Records'])}")
            print(f"Record structure: {json.dumps(record, indent=2)}")
            
            # Validate record has S3 data
            if 's3' not in record:
                print(f"Skipping record {i} - no 's3' key found")
                continue
            
            # Extract S3 information
            s3_data = record['s3']
            bucket = s3_data['bucket']['name']
            # URL decode the key (handles spaces and special characters)
            key = urllib.parse.unquote_plus(s3_data['object']['key'])
            
            print(f"Bucket: {bucket}")
            print(f"Key: {key}")
            
            # Validate it's a .wav file
            if not key.lower().endswith('.wav'):
                print(f"Skipping non-wav file: {key}")
                continue
            
            # Extract ContactId from filename pattern: [ContactId]_[date]_UTC.wav
            # Example: cc49ae4e-abcd-1234-wxyz-567890abcdef_20241009_UTC.wav
            filename = key.split('/')[-1]  # Get just the filename, not the path
            print(f"Filename: {filename}")
            
            # Regex to extract ContactId (UUID pattern before first underscore)
            contact_id_match = re.match(r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})_', filename, re.IGNORECASE)
            
            if not contact_id_match:
                print(f"Could not extract ContactId from filename: {filename}")
                print("Expected format: [ContactId]_[date]_UTC.wav")
                continue
            
            contact_id = contact_id_match.group(1)
            print(f"Extracted ContactId: {contact_id}")
            
            # Construct S3 URI for the media file
            media_uri = f"s3://{bucket}/{key}"
            print(f"Media URI: {media_uri}")
            
            # Start Transcribe job
            job_name = contact_id  # Use ContactId as job name
            
            print(f"Starting transcription job: {job_name}")
            
            response = transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={
                    'MediaFileUri': media_uri
                },
                MediaFormat='wav',
                LanguageCode='en-US',
                OutputBucketName=bucket,
                Settings={
                    'ChannelIdentification': True
                }
            )
            
            print(f"✅ Transcription job started successfully")
            print(f"Job Name: {job_name}")
            print(f"Job Status: {response['TranscriptionJob']['TranscriptionJobStatus']}")
            print(f"Media URI: {media_uri}")
            print(f"Output Bucket: {bucket}")
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Transcription jobs processed successfully',
                'recordsProcessed': len(event['Records'])
            })
        }
        
    except Exception as e:
        print(f"❌ ERROR in lambda_handler: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Log additional context for debugging
        print("=== ERROR CONTEXT ===")
        print(f"Event keys: {list(event.keys()) if isinstance(event, dict) else 'Event is not a dict'}")
        
        if isinstance(event, dict) and 'Records' in event:
            print(f"Records count: {len(event['Records'])}")
            for i, record in enumerate(event['Records']):
                print(f"Record {i} keys: {list(record.keys()) if isinstance(record, dict) else 'Record is not a dict'}")
        
        print("=== END ERROR CONTEXT ===")
        
        # Re-raise the exception to mark Lambda as failed
        raise e

