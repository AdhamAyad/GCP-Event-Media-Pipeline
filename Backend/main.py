import os
from flask import Flask, request, jsonify, render_template_string
from google.cloud import storage, firestore
from werkzeug.utils import secure_filename

app = Flask(_name_)

RAW_BUCKET_NAME = os.environ.get("RAW_BUCKET_NAME")
PROCESSED_BUCKET_NAME = os.environ.get("PROCESSED_BUCKET_NAME")
COLLECTION_NAME = os.environ.get("FIRESTORE_COLLECTION_NAME")
FIRESTORE_DB_NAME = os.environ.get("FIRESTORE_DB_NAME")


@app.route('/upload-to-gcs', methods=['POST'])
def upload_to_gcs():
    if 'image_file' not in request.files:
        return jsonify({"error": "No image_file part"}), 400

    file = request.files['image_file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        try:
            storage_client = storage.Client()
            bucket = storage_client.get_bucket(RAW_BUCKET_NAME)
            
            file_name = secure_filename(file.filename) 
            blob = bucket.blob(file_name)
            
            file_content = file.read()
            file_mimetype = file.content_type
            
            blob.upload_from_string(
                file_content,
                content_type=file_mimetype
            )
            
            return jsonify({
                "message": "File uploaded successfully",
                "filename": file_name,
                "bucket": RAW_BUCKET_NAME
            }), 200

        except Exception as e:
            print(f"Error during GCS upload: {e}")
            return jsonify({"error": f"Internal Server Error: {e}"}), 500

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
                    <!-- (نستخدم الباكيت الجديد وصورة الـ Thumbnail) -->
                    <img src="https://storage.googleapis.com/{{ processed_bucket }}/{{ item.doc_id }}_thumb.jpg" 
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
    """
    HTML Endpoint: يعرض الداتا ست كصفحة ويب.
    """
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
            
        return render_template_string(
            GALLERY_TEMPLATE, 
            dataset=dataset, 
            processed_bucket=PROCESSED_BUCKET_NAME
        )

    except Exception as e:
        print(f"Error reading Firestore for gallery: {e}")
        return render_template_string(GALLERY_TEMPLATE, error=f"فشل جلب الداتا ست: {e}")


@app.route('/')
def home():
    return jsonify({"message": "Backend API is running and ready to process uploads or serve the gallery."}), 200

if _name_ == '_main_':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))