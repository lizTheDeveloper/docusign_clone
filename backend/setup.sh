#!/bin/bash

# Setup script for DocuSign Clone Backend
# This script sets up the development environment

set -e

echo "🚀 Setting up DocuSign Clone Backend..."

# Check if Python 3.10+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✓ .env file already exists"
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL client not found. Please install PostgreSQL."
else
    echo "✓ PostgreSQL client found"
fi

# Create database if it doesn't exist
echo "🗄️  Setting up database..."
read -p "Do you want to create the database? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter database name (default: docusign_clone): " DB_NAME
    DB_NAME=${DB_NAME:-docusign_clone}
    
    psql -U postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database may already exist"
    
    # Create test database
    psql -U postgres -c "CREATE DATABASE ${DB_NAME}_test;" 2>/dev/null || echo "Test database may already exist"
fi

# Run migrations
echo "🔄 Running database migrations..."
read -p "Do you want to run migrations? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    alembic upgrade head
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run development server: uvicorn app.main:app --reload"
echo "4. Run tests: pytest"
echo "5. Access API docs: http://localhost:8000/docs"
echo ""
