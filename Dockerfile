FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Do NOT initialize the database during image build.
# Database initialization (migrations or seeding) should run at runtime
# or be executed manually via `flask init-db` / `flask db upgrade`.

# Expose port
EXPOSE 5000

# Run application using WSGI entrypoint (wsgi.py exposes `app`)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
