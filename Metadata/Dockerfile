FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y libjpeg-dev zlib1g-dev

COPY requirements.txt .

RUN pip install --user -r requirements.txt

FROM python:3.12-slim AS final

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY main.py .

EXPOSE 8080

CMD ["gunicorn","--bind","0.0.0.0:$PORT","main:app"]
