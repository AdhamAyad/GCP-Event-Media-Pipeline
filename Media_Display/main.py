import os
import base64
import json
import io
from flask import Flask, request
from google.cloud import storage
from PIL import Image

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
PROCESSED_BUCKET_NAME = os.environ.get("PROCESSED_BUCKET_NAME")

storage_client = storage.Client()
raw_bucket = None
processed_bucket = None
logo_image = None 

try:
    if RAW_BUCKET_NAME:
        raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
    if PROCESSED_BUCKET_NAME:
        processed_bucket = storage_client.get_bucket(PROCESSED_BUCKET_NAME)
    
    logo_image = Image.open("logo.png")
    logo_image.thumbnail((150, 150))

except Exception as e:
    print(f"خطأ في تهيئة الباكيتس أو اللوجو: {e}")

DISPLAY_SIZE = (800, 800)

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    """
    يستقبل الرسالة، يغير حجم الصورة، يضيف اللوجو (Watermark)، ويرفعها.
    """
    if not raw_bucket or not processed_bucket or not logo_image:
        print("خطأ فادح: الباكيتس أو اللوجو غير مُعرّف.")
        return "Server configuration error", 500

    try:
        envelope = request.get_json(silent=True)
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        gcs_event = json.loads(data_str)
        
        file_name = gcs_event.get('name')
        if not file_name:
            return "Invalid message", 400
            
    except Exception as e:
        print(f"خطأ في تحليل الرسالة: {e}")
        return "Message parsing error", 400

    try:
        print(f"بدء معالجة (Display) للملف: {file_name}")

        source_blob = raw_bucket.blob(file_name)
        in_memory_file = io.BytesIO()
        source_blob.download_to_file(in_memory_file)
        in_memory_file.seek(0) 

        image = Image.open(in_memory_file)
        image.thumbnail(DISPLAY_SIZE) 
        padding = 20
        position = (
            image.width - logo_image.width - padding, 
            image.height - logo_image.height - padding
        )
        
        image.paste(logo_image, position, logo_image)

        out_memory_file = io.BytesIO()
        image.save(out_memory_file, format='PNG') 
        out_memory_file.seek(0)

        file_stem = os.path.splitext(file_name)[0]
        new_file_name = f"{file_stem}_display.png"

        dest_blob = processed_bucket.blob(new_file_name)
        dest_blob.upload_from_file(
            out_memory_file, 
            content_type='image/png'
        )

        print(f"تم إنشاء صورة العرض (Display) بنجاح: {new_file_name}")
        
        return "", 204

    except Exception as e:
        print(f"فشل معالجة الملف {file_name}: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))