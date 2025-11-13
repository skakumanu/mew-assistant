#!/bin/bash
# Legacy Docker Compose script
# NOTE: This project now uses Podman. Please use ./podman-start.sh instead
# This file is kept for Docker users who prefer docker-compose

echo "⚠️  NOTICE: This project now uses Podman"
echo "   Recommended: ./podman-start.sh"
echo "   Or for full stack: ./podman-full.sh"
echo ""
echo "Continuing with Docker Compose..."
echo ""

docker-compose up -d db
sleep 5
docker-compose ps

echo ""
echo "✅ PostgreSQL is running!"
echo ""
echo "Restart your FastAPI app:"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Or run everything in Docker:"
echo "  docker-compose up -d"
