#!/bin/bash
# Mew Assistant - Podman Startup Script

echo "🚀 Starting Mew Assistant with Podman"
echo "====================================="
echo ""

# Start PostgreSQL container (standalone - fixes rootless networking)
echo "Starting PostgreSQL..."
podman run -d \
  --name mew-db \
  -e POSTGRES_USER=mew_user \
  -e POSTGRES_PASSWORD=mew_password \
  -e POSTGRES_DB=mew_assistant \
  -p 5432:5432 \
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
    
    # Start the app container
    echo "Starting Mew Assistant app..."
    podman run -d \
      --name mew-app \
      -p 8888:8000 \
      -e DATABASE_URL="postgresql://mew_user:mew_password@host.containers.internal:5432/mew_assistant" \
      localhost/mew-assistant:latest
    
    sleep 3
    
    echo ""
    echo "✅ Mew Assistant is starting!"
    echo ""
    echo "📋 Access the app:"
    echo "   API Docs: http://localhost:8888/docs"
    echo "   Health: http://localhost:8888/health"
    echo ""
    echo "📋 Database Connection details:"
    echo "   Host: 127.0.0.1"
    echo "   Port: 5432"
    echo "   Database: mew_assistant"
    echo "   User: mew_user"
    echo "   Password: mew_password"
    echo ""
else
    echo "⚠️  PostgreSQL not ready yet. Wait a few seconds and check:"
    echo "   podman ps"
fi
