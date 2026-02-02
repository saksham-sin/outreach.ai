FROM python:3.11-slim

WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the entire project
COPY . /app

# Expose port
EXPOSE 8000

# Set environment variables (ensure Python can import backend 'app' package)
ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONPATH=/app/backend

# Run migrations and start server from backend directory
CMD ["bash", "-c", "cd /app/backend && python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
