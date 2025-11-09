import os
import uuid
import datetime # <-- (إضافة جديدة)
from flask import Flask, request, jsonify, render_template_string # <-- (إضافة جديدة)
from google.cloud import storage, firestore # <-- (إضافة جديدة)

app = Flask(__name__)

# --- (الكود القديم الخاص بك - كما هو) ---
RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")

storage_client = storage.Client()
bucket = None # (هذا هو الباكيت الخاص بالرفع)

if RAW_BUCKET_NAME:
    try:
        bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
    except Exception as e:
        print(f"Error initializing GCS bucket '{RAW_BUCKET_NAME}': {e}")
        bucket = None
else:
    print("FATAL ERROR: RAW_BUCKET_NAME environment variable is not set.")

# --- (متغيرات البيئة الجديدة - إضافة) ---
PROCESSED_BUCKET_NAME = os.environ.get("PROCESSED_BUCKET_NAME")
COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")
FIRESTORE_DB_NAME = os.environ.get("FIRESTORE_DB_NAME")

# --- (الـ Endpoint القديم - كما هو) ---
@app.route('/')
def health_check():
    return jsonify({"message": "Backend API (Proxy Upload) is running."}), 200

# --- (الـ Endpoint القديم - كما هو) ---
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
            "bucket": RAW_BUCKET_NAME
        }), 201

    except Exception as e:
        return jsonify({"error": f"Failed to upload to GCS: {str(e)}"}), 500

# --- (الإضافات الجديدة - قالب HTML) ---
GALLERY_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>معرض الداتا ست</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; background: #f4f4f9; }
        main { max-width: 1200px; margin: auto; }
        h1 { color: #333; }
        .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1.5rem; }
        .card { background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); overflow: hidden; }
        .card img { width: 100%; height: 200px; object-fit: cover; background: #eee; }
        .card-content { padding: 1rem; }
        .card h3 { margin: 0 0 0.5rem 0; font-size: 1.1rem; }
        .tags { margin-top: 0.5rem; }
        .tag { display: inline-block; background: #e0e7ff; color: #4338ca; padding: 0.25rem 0.75rem; border-radius: 99px; font-size: 0.8rem; margin: 2px; }
    </style>
</head>
<body>
    <main>
        <h1>المعرض (الداتا ست)</h1>
        <p>عرض آخر 20 صورة تمت معالجتها (يتم جلبها من Firestore)</p>
        <div class="gallery">
            {% if error %}
                <p style="color: red;">خطأ: {{ error }}</p>
            {% else %}
                {% for item in dataset %}
                <div class="card">
                    <!-- (نستخدم الرابط المؤقت (Signed URL)) -->
                    <img src="{{ item.signed_thumb_url }}" 
                         alt="{{ item.doc_id }}"
                         onerror="this.src='https://placehold.co/250x200?text=Processing...';">
                    
                    <div class="card-content">
                        <!-- (نعرض الـ AI Tags) -->
                        <div class="tags">
                            {% if item.ai_labels %}
                                {% for label in item.ai_labels[:5] %} 
                                    <span class="tag">{{ label }}</span>
                                {% endfor %}
                            {% else %}
                                <span class="tag" style="background: #f3f4f6; color: #6b7280;">(No AI Tags)</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            {% endif %}
        </div>
    </main>
</body>
</html>
"""


@app.route('/gallery', methods=['GET'])
def gallery():
    if not COLLECTION_NAME or not FIRESTORE_DB_NAME or not PROCESSED_BUCKET_NAME:
        return render_template_string(GALLERY_TEMPLATE, error="متغيرات البيئة الخاصة بالداتا ست غير مُعدّة.")

    try:
        # (تهيئة العملاء داخل الدالة - Lazy Init)
        db = firestore.Client(database=FIRESTORE_DB_NAME)
        
        # (يجب تهيئة عميل GCS جديد هنا للـ processed_bucket)
        gallery_storage_client = storage.Client()
        processed_bucket = gallery_storage_client.get_bucket(PROCESSED_BUCKET_NAME)
        
        docs = db.collection(COLLECTION_NAME)\
                 .order_by('last_updated_metadata', direction=firestore.Query.DESCENDING)\
                 .limit(20)\
                 .stream()

        dataset = []
        for doc in docs:
            data = doc.to_dict()
            data['doc_id'] = doc.id
            
            # (إنشاء Signed URL للباكيت الـ Private)
            try:
                thumb_blob_name = f"{doc.id}_display.jpg"
                
                data['signed_thumb_url'] = f"https://storage.googleapis.com/{PROCESSED_BUCKET_NAME}/{doc.id}_display.jpg"

            except Exception as e:
                print(f"Error generating signed URL for {doc.id}: {e}")
                data['signed_thumb_url'] = "https://placehold.co/250x200?text=Error:NoAccess"

            dataset.append(data)
            
        return render_template_string(
            GALLERY_TEMPLATE, 
            dataset=dataset
        )

    except Exception as e:
        print(f"Error reading Firestore for gallery: {e}")
        return render_template_string(GALLERY_TEMPLATE, error=f"فشل جلب الداتا ست: {e}")

# --- (الإضافات الجديدة - Endpoint الـ API) ---
@app.route('/api/dataset', methods=['GET'])
def get_dataset():
    try:
        db = firestore.Client(database=FIRESTORE_DB_NAME)
        
        docs = db.collection(COLLECTION_NAME)\
                 .order_by('last_updated_metadata', direction=firestore.Query.DESCENDING)\
                 .limit(20)\
                 .stream()

        dataset = []
        for doc in docs:
            data = doc.to_dict()
            data['doc_id'] = doc.id
            dataset.append(data)
            
        return jsonify(dataset), 200

    except Exception as e:
        print(f"Error reading Firestore: {e}")
        return jsonify({"error": f"Failed to retrieve dataset: {e}"}), 500

# --- (الكود القديم الخاص بك - كما هو) ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
