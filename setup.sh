#!/bin/bash
# Mew Assistant - Quick Start Script
# This script helps new contributors get started quickly

set -e

echo "🎉 Welcome to Mew Assistant!"
echo "================================"
echo ""

# Check Python version
echo "📋 Checking prerequisites..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if Podman is installed
if command -v podman &> /dev/null; then
    echo "✓ Podman is installed"
    HAS_PODMAN=true
else
    echo "⚠️  Podman not found. PostgreSQL will use SQLite instead."
    echo "   To install Podman: https://podman.io/getting-started/installation"
    HAS_PODMAN=false
fi

echo ""
echo "🔧 Setting up development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --quiet --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install --quiet -r requirements.txt
echo "✓ Dependencies installed"

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ "$HAS_PODMAN" = true ]; then
        # Configure for PostgreSQL with Podman
        cat > .env << 'EOF'
# Mew Assistant Configuration - PostgreSQL with Podman
# Set DATABASE_URL environment variable before running
# Example: postgresql://user:password@localhost:5432/mew_assistant
DATABASE_URL=${DATABASE_URL:-postgresql://localhost:5432/mew_assistant}
APP_NAME=Mew Assistant
DEBUG=True
CORS_ORIGINS=*
DEFAULT_COOLDOWN_HOURS=24
EOF
        echo "✓ .env configured for PostgreSQL (Podman)"
    else
        # Configure for SQLite
        cat > .env << 'EOF'
# Mew Assistant Configuration - SQLite
DATABASE_URL=sqlite:///./mew_assistant.db
APP_NAME=Mew Assistant
DEBUG=True
CORS_ORIGINS=*
DEFAULT_COOLDOWN_HOURS=24
EOF
        echo "✓ .env configured for SQLite"
    fi
else
    echo "✓ .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo ""

if [ "$HAS_PODMAN" = true ]; then
    echo "1. Start PostgreSQL with Podman:"
    echo "   ./podman-start.sh"
    echo ""
    echo "2. Run the application:"
    echo "   source .venv/bin/activate"
    echo "   uvicorn app.main:app --reload"
    echo ""
    echo "3. Open API documentation:"
    echo "   http://localhost:8000/docs"
    echo ""
    echo "4. Read PODMAN_GUIDE.md for Podman usage"
else
    echo "1. Run the application (SQLite - no database setup needed):"
    echo "   source .venv/bin/activate"
    echo "   uvicorn app.main:app --reload"
    echo ""
    echo "2. Open API documentation:"
    echo "   http://localhost:8000/docs"
    echo ""
    echo "3. To use PostgreSQL later, install Podman and run ./podman-start.sh"
fi

echo ""
echo "5. Read CONTRIBUTING.md for development guidelines"
echo ""
echo "Happy coding! 🚀"

