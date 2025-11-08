import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

BACKEND_API_URL = os.environ.get("BACK_END_API")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <title>Python Frontend (Proxy Upload)</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; background: #f4f4f9; }
        main { max-width: 800px; margin: auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        pre { background: #eee; padding: 1rem; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }
        .error { color: #D8000C; background: #FFD2D2; }
        .success { color: #4F8A10; background: #DFF2BF; }
        .msg { padding: 1rem; border-radius: 5px; margin-bottom: 1rem; }
        input[type="file"], input[type="submit"] { display: block; margin-top: 1rem; }
    </style>
</head>
<body>
    <main>
        <h1>Upload System (GCP Event Media Pipeline)</h1>
        
        {% if upload_message %}
            <div class="msg {{ 'success' if success else 'error' }}">
                {{ upload_message }}
            </div>
        {% endif %}

        <h2>1. Upload New Image</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label for="file_to_upload">Choose an image to upload:</label>
            <input type="file" name="file_to_upload" id="file_to_upload" accept="image/*" required>
            <input type="submit" value="Upload Image">
        </form>

        <hr style="margin-top: 2rem;">

        <h2>2. Backend Connection Test</h2>
        <p><b>Backend URL (from environment):</b> {{ backend_url }}</p>
        {% if connection_error %}
            <div class="msg error">
                <strong>Connection Error:</strong> {{ connection_error }}
            </div>
        {% else %}
            <div class="msg success">
                <strong>Connection Status:</strong> {{ connection_data }}
            </div>
        {% endif %}
    </main>
</body>
</html>
"""

def get_connection_status():
    if not BACKEND_API_URL:
        return {
            "backend_url": "Not Set",
            "connection_error": "Environment variable BACKEND_API_URL is not configured."
        }
    
    try:
        response = requests.get(BACKEND_API_URL, timeout=5)
        response.raise_for_status()
        return {
            "backend_url": BACKEND_API_URL,
            "connection_data": response.json().get("message", "Connected Successfully")
        }
    except requests.exceptions.RequestException as e:
        return {
            "backend_url": BACKEND_API_URL,
            "connection_error": f"Failed to connect to backend: {str(e)}"
        }

@app.route('/')
def home():
    context = get_connection_status()
    return render_template_string(HTML_TEMPLATE, **context)

@app.route('/upload', methods=['POST'])
def upload_file():
    context = get_connection_status()
    
    if 'file_to_upload' not in request.files:
        context['upload_message'] = "No file selected."
        context['success'] = False
        return render_template_string(HTML_TEMPLATE, **context), 400

    file = request.files['file_to_upload']

    if file.filename == '':
        context['upload_message'] = "Empty file submitted."
        context['success'] = False
        return render_template_string(HTML_TEMPLATE, **context), 400

    if not BACKEND_API_URL:
        context['upload_message'] = "Critical Error: Backend URL not configured."
        context['success'] = False
        return render_template_string(HTML_TEMPLATE, **context), 500

    try:
        files_to_proxy = {'image_file': (file.filename, file.stream, file.mimetype)}
        upload_url = f"{BACKEND_API_URL}/upload-to-gcs"
        
        response = requests.post(upload_url, files=files_to_proxy, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()
        context['upload_message'] = f"Upload successful! Unique filename: {response_data.get('filename')}"
        context['success'] = True
        
    except requests.exceptions.RequestException as e:
        context['upload_message'] = f"Failed to upload to backend: {str(e)}"
        context['success'] = False
    
    return render_template_string(HTML_TEMPLATE, **context)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
