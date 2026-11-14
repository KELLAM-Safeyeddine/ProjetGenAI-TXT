FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_APP=run:app PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && groupadd -g 10001 auto && useradd -m -u 10001 -g auto auto
COPY . .
RUN mkdir -p /app/instance /run/app-secrets && chown -R auto:auto /app /run/app-secrets
USER auto
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=4s --start-period=60s --retries=5 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health', timeout=3)"
CMD ["python", "docker/start.py"]
