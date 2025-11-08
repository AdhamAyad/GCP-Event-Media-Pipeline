import os
import base64
import json
import datetime
from flask import Flask, request

# استيراد مكتبات Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# تهيئة Firebase Admin SDK
# في بيئات Google Cloud (مثل Cloud Functions/Run)، سيتم العثور على بيانات الاعتماد
# تلقائيًا عبر "Application Default Credentials" (ADC).
try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("تمت تهيئة Firestore بنجاح.")
except Exception as e:
    print(f"خطأ في تهيئة Firebase: {e}")
    # إذا فشلت التهيئة، سنسمح باستمرار التطبيق ولكن سنقوم بالرد بخطأ عند محاولة التخزين
    db = None

# اسم المجموعة التي سيتم التخزين فيها
# يمكنك تغيير هذا الاسم (مثلاً: 'gcs_file_logs')
# في بيئة Canvas، قد تحتاج إلى استخدام مسار محدد مثل:
# f"artifacts/{appId}/public/data/gcs_events"
FIRESTORE_COLLECTION = "gcs_file_events"

@app.route('/', methods=['POST'])
def handle_pubsub_message():
    """
    يستقبل الرسالة من Pub/Sub، ويقوم بتحليلها لاستخلاص اسم الملف،
    ثم يخزن اسم الملف في Firestore.
    """
    if db is None:
        print("خطأ فادح: لم يتم تهيئة Firestore.")
        return "Server configuration error (Firestore not initialized)", 500

    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        print("رسالة Pub/Sub غير صالحة أو مفقودة.")
        return "Bad Request: Invalid Pub/Sub format", 400

    try:
        # 1. استخلاص البيانات المشفرة من مظروف Pub/Sub
        data_str = base64.b64decode(envelope['message']['data']).decode('utf-8')
        
        # 2. تحليل الحمولة (Payload) إلى حدث GCS
        gcs_event = json.loads(data_str)
        
        # 3. استخلاص اسم الملف كما طلبته (نفس الكود الأصلي)
        file_name = gcs_event.get('name')
        bucket_name = gcs_event.get('bucket')

        if not file_name:
            print(f"تجاهل الرسالة: اسم الملف مفقود في حمولة GCS.")
            return "File name not found in GCS event", 204

    except Exception as e:
        print(f"خطأ في تحليل الرسالة: {e}")
        return "Message parsing error", 400

    try:
        print(f"ملف GCS المُستلَم: {file_name} من الباكيت: {bucket_name}")

        # 4. التخزين في Firestore
        # نستخدم اسم الملف كـ Document ID لأنه فريد ومميز كما طلبت
        
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
    # لتشغيل محلي لاختبار بسيط
    PORT = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=PORT)