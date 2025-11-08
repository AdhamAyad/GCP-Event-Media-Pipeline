import os
import base64
import json
import datetime
from flask import Flask, request

# استيراد مكتبات Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# --- قراءة جميع الإعدادات من متغيرات البيئة (Environment Variables) ---
# 1. اسم قاعدة بيانات Firestore (مثل: metadata-db)
FIRESTORE_DATABASE_NAME = os.environ.get("FIRESTORE_DB_NAME", "(default)")

# 2. اسم المجموعة (Collection) في Firestore (مثل: images_collection_name)
FIRESTORE_COLLECTION = os.environ.get("FIRESTORE_COLLECTION_NAME", "gcs_file_events")

# 3. اسم الباكيت الخام للتحقق من مصدر الحدث (مثل: gcp_event_media)
RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")


# تهيئة Firebase Admin SDK
db = None
try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
    
    # نمرر اسم قاعدة البيانات الصريح
    db = firestore.client(database=FIRESTORE_DATABASE_NAME)
    
    display_name = FIRESTORE_DATABASE_NAME if FIRESTORE_DATABASE_NAME != "(default)" else "الافتراضية (default)"
    print(f"تمت تهيئة Firestore بنجاح للـ Database: {display_name} والمجموعة: {FIRESTORE_COLLECTION}")

except Exception as e:
    print(f"خطأ في تهيئة Firebase: {e}")
    db = None

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    """
    يستقبل الرسالة من Pub/Sub، ويقوم بتحليلها لاستخلاص اسم الملف،
    ثم يخزن اسم الملف في Firestore.
    """
    # التحقق من التهيئة
    if db is None:
        print("خطأ فادح: لم يتم تهيئة Firestore.")
        return "Server configuration error (Firestore not initialized)", 500
        
    # التحقق من وجود اسم الباكيت الخام
    if not RAW_BUCKET_NAME:
        print("خطأ فادح: متغير البيئة RAW_BUCKET_NAME غير مُعرّف.")
        return "Server configuration error (RAW_BUCKET_NAME missing)", 500


    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        print("رسالة Pub/Sub غير صالحة أو مفقودة.")
        return "Bad Request: Invalid Pub/Sub format", 400

    try:
        # 1. استخلاص البيانات المشفرة من مظروف Pub/Sub
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        
        # 2. تحليل الحمولة (Payload) إلى حدث GCS
        gcs_event = json.loads(data_str)
        
        # 3. استخلاص اسم الملف والباكيت
        file_name = gcs_event.get('name')
        bucket_name = gcs_event.get('bucket')

        # 🚨 إضافة التحقق الأمني: تأكيد أن الحدث جاء من الباكيت الذي نتوقعه
        if not file_name or bucket_name != RAW_BUCKET_NAME:
            print(f"تجاهل الرسالة: (ملف: {file_name}, باكيت: {bucket_name}). ليست من الباكيت المطلوب ({RAW_BUCKET_NAME}).")
            return "", 204 # نرد بنجاح (204) لتجنب إعادة إرسال الرسالة

    except Exception as e:
        print(f"خطأ في تحليل الرسالة: {e}")
        return "Message parsing error", 400

    try:
        print(f"ملف GCS المُستلَم: {file_name} من الباكيت: {bucket_name}")

        # 4. التخزين في Firestore باستخدام اسم الملف كـ Document ID واسم المجموعة من ENV
        doc_ref = db.collection(FIRESTORE_COLLECTION).document(file_name)
        
        data_to_save = {
            "file_name": file_name,
            "bucket_name": bucket_name,
            "received_at": datetime.datetime.now(datetime.timezone.utc),
            "status": "logged_success"
        }

        doc_ref.set(data_to_save)
        
        print(f"تم تسجيل الملف في Firestore بنجاح. ID: {file_name}")
        
        return "", 204

    except Exception as e:
        print(f"فشل تخزين الملف {file_name} في Firestore: {e}")
        return "Internal Server Error during Firestore save", 500

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=PORT)