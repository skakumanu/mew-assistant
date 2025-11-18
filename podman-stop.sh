#!/bin/bash
# Stop Mew Assistant Podman containers

echo "🛑 Stopping Mew Assistant..."

# Stop and remove app container
podman stop mew-app 2>/dev/null
podman rm mew-app 2>/dev/null

# Stop and remove database container
podman stop mew-db 2>/dev/null
podman rm mew-db 2>/dev/null

echo "✅ Stopped!"
echo ""
echo "To start again: ./podman-start.sh"
