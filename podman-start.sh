#!/bin/bash
# Mew Assistant - Podman Startup Script

echo "🚀 Starting Mew Assistant with Podman"
echo "====================================="
echo ""

# Create a pod for the application
echo "Creating Podman pod..."
podman pod create --name mew-pod -p 8000:8000 -p 5432:5432

# Start PostgreSQL container in the pod
echo "Starting PostgreSQL..."
podman run -d \
  --pod mew-pod \
  --name mew-db \
  -e POSTGRES_USER=mew_user \
  -e POSTGRES_PASSWORD=mew_password \
  -e POSTGRES_DB=mew_assistant \
  -v mew-postgres-data:/var/lib/postgresql/data \
  docker.io/library/postgres:15-alpine

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 5

# Check if PostgreSQL is ready
echo "Checking PostgreSQL status..."
podman exec mew-db pg_isready -U mew_user -d mew_assistant

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ PostgreSQL is running!"
    echo ""
    echo "📋 Connection details:"
    echo "   Host: localhost"
    echo "   Port: 5432"
    echo "   Database: mew_assistant"
    echo "   User: mew_user"
    echo "   Password: mew_password"
    echo ""
    echo "🔧 Update your .env file:"
    echo "   DATABASE_URL=postgresql://mew_user:mew_password@localhost:5432/mew_assistant"
    echo ""
    echo "🚀 Start your app:"
    echo "   uvicorn app.main:app --reload"
    echo ""
else
    echo "⚠️  PostgreSQL not ready yet. Wait a few seconds and check:"
    echo "   podman ps"
fi
