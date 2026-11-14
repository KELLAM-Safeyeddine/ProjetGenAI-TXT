FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_APP=run:app PORT=5000
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt && groupadd -g 10001 auto && useradd -m -u 10001 -g auto auto
# Copie explicite du code : aucun manuel, .env, volume ou document personnel.
COPY app/ app/
COPY migrations/ migrations/
COPY config/ config/
COPY data/ data/
COPY docker/ docker/
COPY tests/ tests/
COPY scripts/ scripts/
COPY config.py run.py pytest.ini .gitignore .env.example Dockerfile docker-compose.yml .dockerignore ./
RUN mkdir -p /app/instance /app/data/manuels && chown -R auto:auto /app
USER auto
EXPOSE 5000
HEALTHCHECK --interval=15s --timeout=4s --start-period=60s --retries=5 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','5000')+'/health', timeout=3)"
CMD ["python", "docker/start.py"]
