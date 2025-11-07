import os
import uuid
from flask import Flask, request, jsonify
from google.cloud import storage

app = Flask(__name__)

BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")

storage_client = storage.Client()
bucket = None

if BUCKET_NAME:
    try:
        bucket = storage_client.get_bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Error initializing GCS bucket '{BUCKET_NAME}': {e}")
        bucket = None
else:
    print("FATAL ERROR: RAW_BUCKET_NAME environment variable is not set.")

@app.route('/')
def health_check():
    return jsonify({"message": "Backend API (Proxy Upload) is running."}), 200

@app.route('/upload-to-gcs', methods=['POST'])
def upload_to_gcs():
    if not bucket:
        return jsonify({"error": "GCS Bucket is not configured on server."}), 500

    if 'image_file' not in request.files:
        return jsonify({"error": "No 'image_file' found in request."}), 400

    file = request.files['image_file']

    if file.filename == '':
        return jsonify({"error": "Empty file uploaded."}), 400

    try:
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4()}{'.' + file_extension if file_extension else ''}"
        
        blob = bucket.blob(unique_filename)
        
        blob.upload_from_file(file.stream, content_type=file.mimetype)

        return jsonify({
            "message": "File proxied and uploaded to GCS successfully.",
            "filename": unique_filename,
            "bucket": BUCKET_NAME
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to upload to GCS: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))