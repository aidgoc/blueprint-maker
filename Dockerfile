FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py generator.py renderer.py research.py questionnaire.py server.py ./
COPY firebase_config.py auth.py db.py storage.py session_store.py ./
COPY start.sh .
COPY static/ static/

# Create runtime directories and unprivileged user
RUN mkdir -p output workspace && \
    useradd -m -u 8888 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8770

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8770", "--timeout-graceful-shutdown", "30"]
