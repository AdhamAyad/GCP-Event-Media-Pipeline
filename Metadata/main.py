import os
import base64
import json
import io
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")

try:
    storage_client = storage.Client()
    db = firestore.Client()
except Exception as e:
    print(f"FATAL ERROR: Failed to initialize Google Cloud clients: {e}")


@app.route('/', methods=['POST'])
def handle_pubsub_message():

    if not RAW_BUCKET_NAME or not COLLECTION_NAME:
        print("FATAL ERROR: Environment variables RAW_BUCKET_NAME or FIRESTORE_COLLECTION_NAME are not set.")
        return "Server configuration error", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope or "data" not in envelope['message']:
        print(f"Bad Request: Invalid Pub/Sub message format. Envelope: {envelope}")
        return "Bad Request: Invalid Pub/Sub message", 400

    try:
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        gcs_event = json.loads(data_str)

    except Exception as e:
        print(f"Error parsing Pub/Sub message data: {e} | Data: {envelope['message'].get('data')}")
        return "Message parsing error", 400

    try:
        file_name = gcs_event.get('name')
        bucket_name = gcs_event.get('bucket')
        file_size_bytes_str = gcs_event.get('size')
        content_type = gcs_event.get('contentType', 'application/octet-stream')

        if not file_name or bucket_name != RAW_BUCKET_NAME:
            print(f"Ignoring event for file '{file_name}' in bucket '{bucket_name}'.")
            return "Event ignored", 204

        file_size_bytes = int(file_size_bytes_str) if file_size_bytes_str else None

    except Exception as e:
        print(f"Error extracting GCS event details: {e} | Event: {gcs_event}")
        return "Invalid GCS event structure", 400


    width, height, image_format = (None, None, None)
    
    if content_type and content_type.startswith('image/'):
        try:
            raw_bucket = storage_client.bucket(RAW_BUCKET_NAME)
            source_blob = raw_bucket.blob(file_name)
            
            in_memory_file = io.BytesIO()
            source_blob.download_to_file(in_memory_file)
            in_memory_file.seek(0)

            with Image.open(in_memory_file) as image:
                width, height = image.size
                image_format = image.format

            print(f"Image properties extracted for {file_name}: {width}x{height}, {image_format}")

        except Exception as e:
            print(f"Failed to extract image dimensions for {file_name}: {e}")
    else:
        print(f"Skipping image dimension extraction for non-image file: {file_name} (Type: {content_type})")


    try:
        doc_id = os.path.splitext(file_name)[0]
        
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

        metadata = {
            'original_filename': file_name,
            'gcs_path': f"gs://{RAW_BUCKET_NAME}/{file_name}",
            'size_bytes': file_size_bytes,
            'content_type': content_type,
            'image_properties': {
                'width_px': width,
                'height_px': height,
                'format': image_format
            },
            'last_updated_metadata': firestore.SERVER_TIMESTAMP,
            'status': 'Processing'
        }

        doc_ref.set(metadata, merge=True)

        print(f"Metadata successfully written for: {file_name} (Doc ID: {doc_id})")
        
        return "Metadata written successfully", 204

    except Exception as e:
        print(f"FATAL ERROR: Failed to write to Firestore for file {file_name}: {e}")
        return "Internal Server Error: Firestore write failed", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))