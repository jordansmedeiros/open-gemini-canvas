#!/bin/bash

# OpenRouter Migration Setup Script for Open Gemini Canvas
echo "=== Open Gemini Canvas - OpenRouter Migration Setup ==="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the agent/ directory."
    exit 1
fi

echo "🔧 Setting up Python environment for OpenRouter..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies from pyproject.toml using pip
echo "📚 Installing dependencies..."
python -m pip install \
    "openai>=1.50.0,<2.0.0" \
    "python-dotenv>=1.0.0,<2.0.0" \
    "fastapi>=0.115.0,<0.116.0" \
    "uvicorn>=0.35.0,<0.36.0" \
    "langgraph>=1.0.0,<2.0.0" \
    "langchain-core>=0.3.78,<0.4.0" \
    "langchain-openai>=0.2.0,<0.3.0" \
    "copilotkit==0.1.58" \
    "requests>=2.31.0,<3.0.0" \
    "httpx>=0.27.0,<0.28.0"

# Check installation
echo "✅ Checking installation..."
python -c "import openai, langchain_openai, fastapi; print('✅ All dependencies installed successfully!')"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure your OpenRouter API key"
echo "2. Run the backend with: python main.py"
echo ""
echo "Environment variables needed:"
echo "- OPENROUTER_API_KEY=your_openrouter_api_key_here"
echo "- OPENROUTER_MODEL=google/gemini-2.5-pro"
echo "- OPENROUTER_BASE_URL=https://openrouter.ai/api/v1"