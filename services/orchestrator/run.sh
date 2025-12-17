#!/bin/bash

echo "🚀 Starting Project Management Orchestrator..."

# Check if PostgreSQL is running
echo "📊 Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Please install PostgreSQL."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "DATABASE_URL=postgresql+asyncpg://admin:secure_password@localhost:5432/project_management" > .env
fi

# Run the application
echo ""
echo "✅ Starting orchestrator on http://localhost:9000"
echo "📖 API Documentation: http://localhost:9000/docs"
echo ""
python main.py
