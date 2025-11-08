import os
import base64
import json
from flask import Flask, request
from google.cloud import storage, firestore, vision

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")
FIRESTORE_DB_NAME = os.environ.get("FIRESTORE_DB_NAME")

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    try:
        storage_client = storage.Client()
        raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
        db = firestore.Client(database=FIRESTORE_DB_NAME)
        vision_client = vision.ImageAnnotatorClient()
        
    except Exception as e:
        print(f"FATAL ERROR: Failed to initialize clients: {e}")
        return "Server configuration error", 500

    if not COLLECTION_NAME:
        print("Fatal Error: Collection name not defined.")
        return "Server configuration error", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        return "Bad Request", 400

    try:
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        gcs_event = json.loads(data_str)
        
        file_name = gcs_event.get('name')
        content_type = gcs_event.get('contentType', '')

        if not file_name or gcs_event.get('bucket') != RAW_BUCKET_NAME:
            return "", 204
            
        if not content_type.startswith('image/'):
            print(f"Skipping non-image file: {file_name}")
            return "", 204

    except Exception as e:
        print(f"Error parsing message: {e}")
        return "Message parsing error", 400

    try:
        print(f"Starting AI Labeling for: {file_name}")
        
        gcs_uri = f"gs://{RAW_BUCKET_NAME}/{file_name}"
        
        image = vision.Image()
        image.source.image_uri = gcs_uri

        features = [vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION)]
        request_ = vision.AnnotateImageRequest(image=image, features=features)

        response = vision_client.annotate_image(request=request_)

        if response.error.message:
            raise Exception(f"Vision API Error: {response.error.message}")

        labels = [label.description for label in response.label_annotations]
        
        print(f"Labels found: {labels}")

        doc_id = os.path.splitext(file_name)[0]
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

        ai_data = {
            'ai_labels': labels,
            'last_updated_ai': firestore.SERVER_TIMESTAMP,
            'status': 'Processing_AI_Complete'
        }

        doc_ref.set(ai_data, merge=True)

        print(f"AI Labels successfully written for: {file_name}")
        
        return "", 204

    except Exception as e:
        print(f"Failed to process AI labels for {file_name}: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))