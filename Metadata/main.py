# app.py
import os
import base64
import json
import io
import os.path
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

app = Flask(__name__)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
PROCESSED_BUCKET_NAME = os.environ.get("PROCESSED_BUCKET_NAME")
FIRESTORE_COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")

storage_client = storage.Client()
firestore_client = firestore.Client()

raw_bucket = None
processed_bucket = None

try:
    if RAW_BUCKET_NAME:
        raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
    if PROCESSED_BUCKET_NAME:
        processed_bucket = storage_client.get_bucket(PROCESSED_BUCKET_NAME)
except Exception as e:
    print(f"خطأ في تهيئة الباكيتس: {e}")

THUMBNAIL_SIZE = (150, 150)

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    """
    يستقبل الرسالة من Pub/Sub (التي أرسلها GCS).
    يقوم بتحليلها، تصغير الصورة، رفعها للباكيت الجديد، وتخزين ميتاداتا الصورة في Firestore.
    """
    if not raw_bucket or not processed_bucket or not FIRESTORE_COLLECTION_NAME:
        print("خطأ فادح: الباكيتس أو مجموعة Firestore غير مُعرّفة.")
        return "Server configuration error", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        print("رسالة غير صالحة.")
        return "Bad Request", 400

    try:
        data_str = base64.b64decode(envelope['message'].get('data', '')).decode('utf-8')
        gcs_event = json.loads(data_str)
        
        bucket_name = gcs_event.get('bucket')
        file_name = gcs_event.get('name')

        if not file_name or bucket_name != RAW_BUCKET_NAME:
            print(f"تجاهل الرسالة: (ملف: {file_name}, باكيت: {bucket_name})")
            return "", 204

    except Exception as e:
        print(f"خطأ في تحليل الرسالة: {e}")
        return "Message parsing error", 400

    try:
        print(f"بدء معالجة الملف: {file_name}")

        # تحميل الصورة من الباكيت المصدر
        source_blob = raw_bucket.blob(file_name)
        in_memory_file = io.BytesIO()
        source_blob.download_to_file(in_memory_file)
        in_memory_file.seek(0)

        # استخراج ميتاداتا الصورة الأصلية
        try:
            original_size_bytes = source_blob.size
            if original_size_bytes is None:
                original_size_bytes = len(in_memory_file.getvalue())
        except Exception:
            original_size_bytes = len(in_memory_file.getvalue())

        image = Image.open(in_memory_file)
        width, height = image.size
        img_format = image.format or "UNKNOWN"

        # إنشاء صورة مصغرة ورفعها
        image.thumbnail(THUMBNAIL_SIZE)
        out_memory_file = io.BytesIO()
        image.save(out_memory_file, format='JPEG')
        out_memory_file.seek(0)

        file_basename = os.path.basename(file_name)
        file_stem = os.path.splitext(file_basename)[0]
        new_file_name = f"{file_stem}_thumb.jpg"

        dest_blob = processed_bucket.blob(new_file_name)
        dest_blob.upload_from_file(
            out_memory_file,
            content_type='image/jpeg'
        )

        print(f"تم إنشاء الصورة المصغرة بنجاح: {new_file_name}")

        # إعداد وحفظ الميتاداتا في Firestore
        metadata = {
            "file_name": file_basename,
            "width": int(width),
            "height": int(height),
            "format": img_format,
            "size_bytes": int(original_size_bytes)
        }

        doc_ref = firestore_client.collection(FIRESTORE_COLLECTION_NAME).document(file_stem)
        doc_ref.set(metadata)

        print(f"تم حفظ الميتاداتا في Firestore للمستند: {file_stem}")

        return "", 204

    except Exception as e:
        print(f"فشل معالجة الملف {file_name}: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
