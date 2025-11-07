import os
import base64
import json
import io
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ["RAW_BUCKET_NAME"]
COLLECTION = os.environ["FIRESTORE_COLLECTION_NAME"]

storage_client = storage.Client()
fire_db = firestore.Client()
raw_bucket = storage_client.bucket(RAW_BUCKET_NAME)

@app.route('/', methods=['POST'])
def handle_pubsub():
    try:
        envelope = request.get_json()
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        gcs_event = json.loads(data_str)
        file_name = gcs_event['name']
    except:
        return "bad req", 400

    try:
        blob = raw_bucket.blob(file_name)
        mem = io.BytesIO()
        blob.download_to_file(mem)
        mem.seek(0)

        img = Image.open(mem)
        width, height = img.size
        fmt = img.format
        size_bytes = blob.size

        doc_id = os.path.splitext(file_name)[0]

        fire_db.collection(COLLECTION).document(doc_id).set({
            "file_name": file_name,
            "width": width,
            "height": height,
            "format": fmt,
            "size_bytes": size_bytes
        })

        return "", 204

    except Exception as e:
        print(e)
        return "err", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))