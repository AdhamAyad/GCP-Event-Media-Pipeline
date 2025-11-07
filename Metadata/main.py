import os
import base64
import json
import io
import logging
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
FIRESTORE_COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME", "images_metadata")

storage_client = storage.Client()
firestore_client = firestore.Client()

# init bucket (raise early if misconfigured)
try:
    if not RAW_BUCKET_NAME:
        raise RuntimeError("RAW_BUCKET_NAME not set")
    raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
except Exception as e:
    logging.error("Bucket init error: %s", e)
    raw_bucket = None

@app.route("/", methods=["POST"])
def handle_pubsub():
    if not raw_bucket:
        logging.error("Raw bucket not initialized")
        return "Server configuration error", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        return "Bad Request", 400

    data_b64 = envelope["message"].get("data")
    if not data_b64:
        return "Bad Request", 400

    try:
        payload = base64.b64decode(data_b64).decode("utf-8")
        gcs_event = json.loads(payload)
        bucket_name = gcs_event.get("bucket")
        file_name = gcs_event.get("name")
        if not file_name or bucket_name != RAW_BUCKET_NAME:
            logging.info("Ignoring event for bucket=%s file=%s", bucket_name, file_name)
            return "", 204
    except Exception as e:
        logging.exception("Failed to parse pubsub message")
        return "Bad Request", 400

    try:
        blob = raw_bucket.blob(file_name)
        # ensure metadata (size) is loaded
        blob.reload()

        data_bytes = blob.download_as_bytes()
        mem = io.BytesIO(data_bytes)
        img = Image.open(mem)
        width, height = img.size
        fmt = img.format or (blob.content_type or "unknown")
        size_bytes = blob.size if blob.size is not None else len(data_bytes)

        doc_id = os.path.splitext(file_name)[0]
        doc = {
            "file_name": file_name,
            "width": width,
            "height": height,
            "format": fmt,
            "size_bytes": int(size_bytes)
        }

        firestore_client.collection(FIRESTORE_COLLECTION_NAME).document(doc_id).set(doc)
        logging.info("Saved metadata for %s => %s", file_name, doc_id)
        return "", 204

    except Exception as e:
        logging.exception("Error processing file %s", file_name)
        return "Internal Server Error", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
