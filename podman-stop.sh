#!/bin/bash
# Stop Mew Assistant Podman containers

echo "🛑 Stopping Mew Assistant..."

# Stop and remove containers
podman stop mew-db 2>/dev/null
podman rm mew-db 2>/dev/null

# Stop and remove pod
podman pod stop mew-pod 2>/dev/null
podman pod rm mew-pod 2>/dev/null

echo "✅ Stopped!"
echo ""
echo "To start again: ./podman-start.sh"
