# Use official lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
# (Ensure requirements.txt exists with: fastapi, uvicorn, pymongo, firebase-admin, python-dotenv)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY api.py .
COPY serviceAccountKey.json . 
# ^ IMPORTANT: In production, use Google Secrets Manager instead of copying keys!

# Expose port
EXPOSE 8080

# Run the API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]