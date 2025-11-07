import os
import requests 
from flask import Flask, render_template_string 

app = Flask(__name__)

BACKEND_API_URL = os.environ.get("BACK_END_API")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Python Frontend</title>
    <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; background: #f4f4f9; }
        main { max-width: 800px; margin: auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
        pre { background: #eee; padding: 1rem; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }
        .error { color: #D8000C; background: #FFD2D2; padding: 1rem; border-radius: 5px; }
    </style>
</head>
<body>
    <main>
        <h1>الاتصال المباشر (Python Flask)</h1>
        <p>
            تم جلب هذه البيانات بواسطة سيرفر البايثون (الكونتينر) 
            قبل إرسال الصفحة للمتصفح.
        </p>
        <p><b>رابط الباك إند المستخدم:</b> {{ backend_url }}</p>
        
        {% if error %}
            <div class="error">
                <strong>خطأ:</strong> {{ error }}
            </div>
        {% else %}
            <h3>الرد من الباك إند:</h3>
            <pre>{{ data }}</pre>
        {% endif %}
    </main>
</body>
</html>
"""

@app.route('/')
def home():
    if not BACKEND_API_URL:
        return render_template_string(
            HTML_TEMPLATE,
            backend_url="غير مُعرّف (Not Set)",
            error="متغير البيئة BACKEND_API_URL غير مُعدّ في الكونتينر."
        )

    try:
        response = requests.get(BACKEND_API_URL, timeout=5)
        
        response.raise_for_status() 
        
        return render_template_string(
            HTML_TEMPLATE,
            backend_url=BACKEND_API_URL,
            data=response.text 
        )

    except requests.exceptions.RequestException as e:
        return render_template_string(
            HTML_TEMPLATE,
            backend_url=BACKEND_API_URL,
            error=f"فشل الاتصال بالباك إند: {str(e)}"
        )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))