FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .

# تثبيت التبعيات باستخدام pip
RUN pip install --user -r requirements.txt 

FROM python:3.12-slim AS final

WORKDIR /app

# نسخ التبعيات المثبتة إلى البيئة النهائية
COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY main.py .

EXPOSE 8080

# تشغيل التطبيق باستخدام Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT main:app