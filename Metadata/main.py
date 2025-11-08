import os
import base64
import json
import io
from flask import Flask, request
from google.cloud import storage, firestore
from PIL import Image

app = Flask(name)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
FIRESTORE_COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")

storage_client = storage.Client()
firestore_client = firestore.Client()
raw_bucket = None

try:
    if RAW_BUCKET_NAME:
        raw_bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
except Exception as e:
    print(f"خطأ في تهيئة الباكيت: {e}")

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    """
    يستقبل الرسالة من Pub/Sub (التي أرسلها GCS).
    يقوم بتحليلها، استخراج البيانات الوصفية للصورة، ثم حفظها في Firestore.
    """
    if not raw_bucket:
        print("خطأ فادح: باكيت RAW غير مُعرّف.")
        return "Server configuration error", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        print("رسالة غير صالحة.")
        return "Bad Request", 400

    try:
        data_b64 = envelope['message'].get('data')
        if not data_b64:
            print("لا توجد بيانات في الرسالة.")
            return "Bad Request", 400

        data_str = base64.b64decode(data_b64).decode('utf-8')
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

        source_blob = raw_bucket.blob(file_name)
        in_memory_file = io.BytesIO()
        source_blob.download_to_file(in_memory_file)

        # حجم الملف بالبايت
        size_bytes = in_memory_file.getbuffer().nbytes

        # افتح الصورة لاستخراج الأبعاد والنوع
        in_memory_file.seek(0)
        image = Image.open(in_memory_file)
        width, height = image.size
        img_format = image.format if image.format else os.path.splitext(file_name)[1].lstrip('.').upper()

        doc_id = os.path.splitext(os.path.basename(file_name))[0]

        metadata = {
            'file_name': file_name,
            'width': width,
            'height': height,
            'format': img_format,
            'size_bytes': size_bytes,
        }

        if not FIRESTORE_COLLECTION_NAME:
            print("لم يتم تعيين FIRESTORE_COLLECTION_NAME في المتغيرات.")
            return "Server configuration error", 500

        collection = firestore_client.collection(FIRESTORE_COLLECTION_NAME)
        collection.document(doc_id).set(metadata)

        print(f"تم حفظ الميتاداتا ل: {file_name} في Firestore (doc: {doc_id})")
        return "", 204

    except Exception as e:
        print(f"فشل معالجة الملف {file_name}: {e}")
        return "Internal Server Error", 500


if name == 'main':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))