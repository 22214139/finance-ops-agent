# Finance Ops Agent -- Gradio app, Python 3.11.
FROM python:3.11-slim

# matplotlib/scipy wheels need these at import time on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# GOOGLE_API_KEY is required at runtime, not build time -- pass it with
# `docker run --env-file .env` (or -e GOOGLE_API_KEY=...), never bake it into the image.
EXPOSE 7860

CMD ["python", "main.py"]
