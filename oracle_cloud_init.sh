#!/bin/bash
set -e

echo "=== Unissons la Main - Oracle Cloud Init ==="
echo "Starting deployment..."

# Update system packages
apt-get update
apt-get upgrade -y
apt-get install -y git docker.io curl wget

# Add current user to docker group
usermod -aG docker ubuntu || usermod -aG docker $USER || true

# Create app directory
mkdir -p /home/ubuntu/app
cd /home/ubuntu/app

# Clone or update repository
if [ -d "FRANCK" ]; then
  cd FRANCK && git pull origin main && cd ..
else
  git clone https://github.com/Fanckeinstein/FRANCK.git
fi

cd FRANCK

# Create uploads directory
mkdir -p static/uploads/receipts
chmod 777 static/uploads/receipts

# Build Docker image
echo "Building Docker image..."
docker build -t unissons:latest .

# Stop and remove old container if exists
docker rm -f unissons || true

# Run container
echo "Starting container..."
docker run -d \
  --restart unless-stopped \
  --name unissons \
  -p 80:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY='unissons-secret-key-change-in-prod' \
  -e DATABASE_URL='sqlite:////home/ubuntu/app/FRANCK/unissons.db' \
  -v /home/ubuntu/app/FRANCK:/app \
  unissons:latest

# Wait for app to start
sleep 3

# Run migrations and seed (optional)
echo "Running database migrations..."
docker exec -it unissons flask db upgrade || echo "Migration completed or skipped"

echo "Seeding database with test users..."
docker exec -it unissons flask seed_db || echo "Database already seeded"

# Get public IP
PUBLIC_IP=$(curl -s https://checkip.amazonaws.com || echo "IP_DETECTION_FAILED")

echo ""
echo "======================================"
echo "✓ Deployment complete!"
echo "======================================"
echo "App is running at: http://$PUBLIC_IP"
echo "Database: /home/ubuntu/app/FRANCK/unissons.db"
echo ""
echo "Test credentials:"
echo "  username: president1 / password: password123"
echo "  username: member1 / password: password123"
echo ""
echo "To view logs:"
echo "  docker logs -f unissons"
echo ""
echo "To access container shell:"
echo "  docker exec -it unissons /bin/sh"
echo "======================================"
