FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY ./shared /app/shared

# Copy worker code
COPY ./app /app/app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app/worker.py"]
