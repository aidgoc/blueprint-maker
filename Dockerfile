FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py generator.py renderer.py research.py questionnaire.py server.py ./
COPY start.sh .
COPY static/ static/

# Create runtime directories
RUN mkdir -p output workspace

EXPOSE 8770

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8770"]
