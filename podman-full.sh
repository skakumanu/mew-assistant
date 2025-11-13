#!/bin/bash
# Run Mew Assistant completely in Podman (API + PostgreSQL)

echo "🐳 Starting Full Mew Assistant Stack with Podman"
echo "================================================"
echo ""

# Create a pod
echo "Creating Podman pod..."
podman pod create --name mew-pod -p 8000:8000 -p 5432:5432

# Start PostgreSQL
echo "Starting PostgreSQL..."
podman run -d \
  --pod mew-pod \
  --name mew-db \
  -e POSTGRES_USER=mew_user \
  -e POSTGRES_PASSWORD=mew_password \
  -e POSTGRES_DB=mew_assistant \
  -v mew-postgres-data:/var/lib/postgresql/data \
  docker.io/library/postgres:15-alpine

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
sleep 8

# Build the API image
echo ""
echo "Building Mew Assistant API image..."
podman build -t mew-assistant:latest .

# Run the API container
echo ""
echo "Starting Mew Assistant API..."
podman run -d \
  --pod mew-pod \
  --name mew-api \
  -e DATABASE_URL=postgresql://mew_user:mew_password@localhost:5432/mew_assistant \
  mew-assistant:latest

# Show status
echo ""
echo "✅ All services started!"
echo ""
echo "📊 Status:"
podman pod ps
echo ""
podman ps --filter pod=mew-pod
echo ""
echo "🌐 Access the API:"
echo "   http://localhost:8000/docs"
echo ""
echo "📝 View logs:"
echo "   podman logs mew-api"
echo "   podman logs mew-db"
echo ""
echo "🛑 To stop:"
echo "   ./podman-stop.sh"
