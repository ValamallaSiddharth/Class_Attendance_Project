# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY my-react-website/package*.json ./
RUN npm ci
COPY my-react-website/ ./
RUN npm run build

# Stage 2: Python Backend with OpenCV
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files and models
COPY app.py api_server.py ./
COPY models/ ./models/
COPY scripts/ ./scripts/
COPY templates/ ./templates/
COPY timetable/ ./timetable/
COPY exports/ ./exports/
COPY data/ ./data/

# Copy built frontend dist from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./my-react-website/dist

# Expose Flask port
EXPOSE 5000

ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
