#!/bin/bash
# Quick start script for Unissons la Main

set -e

echo "🚀 Unissons la Main - Quick Start"
echo "=================================="
echo ""

# Check Python
echo "✓ Checking Python..."
python --version

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo ""
echo "🗄️  Initializing database..."
python init_db.py

# Start server
echo ""
echo "🎉 Starting server..."
echo "📍 Access: http://127.0.0.1:5000"
echo ""
python app.py
