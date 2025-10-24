#!/bin/bash
# TRACE Setup Script

echo "=================================="
echo "  TRACE Setup - Vision Enabled"
echo "=================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi
echo "✓ Python 3 found"
echo ""

# Install Python dependencies
echo "2. Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "⚠ Some packages failed to install. Continuing anyway..."
fi
echo "✓ Python packages installed"
echo ""

# Check for poppler (required for pdf2image)
echo "3. Checking for poppler-utils (required for PDF conversion)..."
if command -v pdftoppm &> /dev/null; then
    echo "✓ poppler-utils found"
else
    echo "⚠ poppler-utils not found"
    echo ""
    echo "PDF-to-image conversion requires poppler-utils."
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  macOS: brew install poppler"
    echo "  Fedora: sudo dnf install poppler-utils"
    echo ""
fi

# Check for API key
echo "4. Checking for Anthropic API key..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠ ANTHROPIC_API_KEY not set"
    echo ""
    echo "Vision features require an Anthropic API key."
    echo ""
    echo "To set up:"
    echo "  1. Get API key from: https://console.anthropic.com/"
    echo "  2. Create .env file: echo 'ANTHROPIC_API_KEY=your-key-here' > .env"
    echo "  Or export: export ANTHROPIC_API_KEY=your-key-here"
    echo ""
else
    echo "✓ ANTHROPIC_API_KEY is set"
fi
echo ""

# Import initial training data
echo "5. Importing October 23 training data..."
python3 import_oct23_training.py
if [ $? -eq 0 ]; then
    echo "✓ Training data imported"
else
    echo "⚠ Failed to import training data"
fi
echo ""

# Create .env template if it doesn't exist
if [ ! -f .env ]; then
    echo "6. Creating .env template..."
    cat > .env << 'EOF'
# Anthropic API Key for Vision features
# Get your key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-api-key-here
EOF
    echo "✓ Created .env template"
    echo "  Edit .env and add your Anthropic API key"
else
    echo "6. .env file already exists"
fi
echo ""

echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your Anthropic API key (if not done)"
echo "  2. Run TRACE: python3 trace_cli.py"
echo "  3. Try: help, sections, load section electrical <pdf> --index"
echo ""
echo "For help: See README.md and QUICKSTART.md"
echo ""
