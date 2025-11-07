import os
import base64
import json
import io
import mimetypes
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME") 

storage_client = storage.Client()
db = firestore.Client() 

raw_bucket = None

try:
    if RAW_BUCKET_NAME:
        raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
except Exception as e:
    print(f"Error initializing bucket: {e}")


@app.route('/', methods=['POST'])
def handle_pubsub_message():
    if not raw_bucket or not COLLECTION_NAME:
        print("Fatal Error: Bucket or Collection name not defined.")
        return "Server configuration error", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        print("Invalid message.")
        return "Bad Request", 400

    try:
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        gcs_event = json.loads(data_str)
        
        bucket_name = gcs_event.get('bucket')
        file_name = gcs_event.get('name')
        
        file_size_bytes = gcs_event.get('size')
        content_type = gcs_event.get('contentType', 'application/octet-stream')

        if not file_name or bucket_name != RAW_BUCKET_NAME:
            print(f"Ignoring message: (File: {file_name}, Bucket: {bucket_name})")
            return "", 204

    except Exception as e:
        print(f"Error parsing message: {e}")
        return "Message parsing error", 400

    width, height, image_format = (None, None, None)
    
    if content_type.startswith('image/'):
        try:
            print(f"Starting metadata processing for: {file_name}")

            source_blob = raw_bucket.blob(file_name)
            in_memory_file = io.BytesIO()
            source_blob.download_to_file(in_memory_file)
            in_memory_file.seek(0)

            image = Image.open(in_memory_file)
            width, height = image.size
            image_format = image.format

        except Exception as e:
            print(f"Failed to extract image dimensions for {file_name}: {e}")
    else:
        print(f"Skipping dimension extraction, not an image: {content_type}")

    try:
        file_stem = os.path.splitext(file_name)[0]
        
        doc_ref = db.collection(COLLECTION_NAME).document(file_stem)

        metadata = {
            'original_filename': file_name,
            'gcs_path': f"gs://{RAW_BUCKET_NAME}/{file_name}",
            'size_bytes': int(file_size_bytes) if file_size_bytes else None,
            'content_type': content_type,
            'image_properties': {
                'width_px': width,
                'height_px': height,
                'format': image_format
            },
            'last_updated_metadata': firestore.SERVER_TIMESTAMP
        }

        doc_ref.set(metadata, merge=True)

        print(f"Metadata successfully written for: {file_name}")
        
        return "", 204

    except Exception as e:
        print(f"Failed to write to Firestore for {file_name}: {e}")
        return "Internal Server Error", 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))