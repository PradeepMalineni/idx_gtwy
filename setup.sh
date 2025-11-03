#!/bin/bash

# Gateway Governance Agent - Setup Script
# This script sets up the development environment for the Gateway Governance Agent

set -e

echo "🚀 Gateway Governance Agent - Setup"
echo "===================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check for API keys
echo ""
echo "🔑 Checking for API keys..."
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: No LLM API key found in environment"
    echo ""
    echo "Please set one of the following:"
    echo "  export OPENAI_API_KEY='your-openai-key'"
    echo "  export ANTHROPIC_API_KEY='your-anthropic-key'"
    echo ""
    echo "Add this to your ~/.bashrc or ~/.zshrc to persist"
else
    if [ -n "$OPENAI_API_KEY" ]; then
        echo "✅ OpenAI API key found"
    fi
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        echo "✅ Anthropic API key found"
    fi
fi

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p ~/.gateway-governance/audit-logs
echo "✅ Audit log directory created: ~/.gateway-governance/audit-logs"

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Set your LLM API key (if not already set):"
echo "   export OPENAI_API_KEY='your-key'"
echo ""
echo "3. Run the MCP server:"
echo "   python server.py"
echo ""
echo "4. Configure your IDE to connect to this MCP server"
echo ""

