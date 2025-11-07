import os
import base64
import json
import io
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
FIRESTORE_COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")

storage_client = storage.Client()
fire_db = firestore.Client()
raw_bucket = storage_client.bucket(RAW_BUCKET_NAME)

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    try:
        envelope = request.get_json(silent=True)
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        gcs_event = json.loads(data_str)
        bucket_name = gcs_event.get('bucket')
        file_name = gcs_event.get('name')
        if not file_name or bucket_name != RAW_BUCKET_NAME:
            return "", 204
    except:
        return "Bad Request", 400

    try:
        blob = raw_bucket.blob(file_name)
        mem_file = io.BytesIO()
        blob.download_to_file(mem_file)
        mem_file.seek(0)

        img = Image.open(mem_file)
        width, height = img.size
        fmt = img.format
        size_bytes = blob.size

        doc_id = os.path.splitext(file_name)[0]
        fire_db.collection(FIRESTORE_COLLECTION_NAME).document(doc_id).set({
            "file_name": file_name,
            "width": width,
            "height": height,
            "format": fmt,
            "size_bytes": size_bytes
        })

        return "", 204

    except Exception as e:
        print(f"Error processing {file_name}: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
