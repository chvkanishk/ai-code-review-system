FROM python:3.11-slim

WORKDIR /app

# Copy shared utilities
COPY ./shared /app/shared

# Copy API Gateway code
COPY ./app /app/app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
