# TRACE Local Setup Guide

Step-by-step instructions to get TRACE running on your local machine.

## Step 1: Clone the Repository

Open your terminal and run:

```bash
# Clone the repository
git clone <your-repository-url> trace_crane_agent2

# Navigate into the directory
cd trace_crane_agent2

# Check the branch
git branch -a
```

If you need to switch to the Vision-enabled branch:

```bash
git checkout claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

## Step 2: Verify Files

Check that you have all the files:

```bash
ls -la
```

You should see:
- `trace_cli.py` - Main CLI
- `requirements.txt` - Python dependencies
- `setup_trace.sh` - Setup script
- `configure_api_key.py` - API key configuration
- `trace/` - Core modules directory
- Documentation files (README.md, VISION_QUICKSTART.md, etc.)

## Step 3: Install Dependencies

### Option A: Automated Setup (Recommended)

Run the setup script:

```bash
chmod +x setup_trace.sh
./setup_trace.sh
```

This will:
- Check Python version
- Install Python packages
- Check for poppler-utils
- Import initial training data
- Create .env template

### Option B: Manual Setup

```bash
# Install Python packages
pip install -r requirements.txt

# Install poppler (required for PDF conversion)
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler

# Fedora:
sudo dnf install poppler-utils

# Windows (via Chocolatey):
choco install poppler

# Import training data
python import_oct23_training.py
```

## Step 4: Configure API Key

### Interactive Method (Easiest)

```bash
python configure_api_key.py
```

Paste your Anthropic API key when prompted. The script will:
- Save it to `.env`
- Test the connection
- Confirm it's working

### Manual Method

Create a `.env` file:

```bash
echo "ANTHROPIC_API_KEY=your-key-from-console-anthropic" > .env
```

**Important:** Replace `your-key-from-console-anthropic` with your actual API key!

### Environment Variable Method

```bash
export ANTHROPIC_API_KEY=your-key-from-console-anthropic
```

(This only lasts for the current session)

## Step 5: Verify Installation

Run the test suite:

```bash
python test_vision_system.py
```

You should see:
```
✓ All tests passed! System is ready.
```

## Step 6: Launch TRACE

Start the CLI:

```bash
python trace_cli.py
```

You should see:

```
============================================================
  TRACE - Crane Schematic Assistant & Copilot
  Version 0.2.0 - Vision Enabled
============================================================

✓ Vision API: Ready

Type 'help' for available commands.

TRACE>
```

## Step 7: Quick Test

Try these commands:

```bash
# See what TRACE knows (October 23 training data)
TRACE> summary

# Search for Slave 22
TRACE> query slave 22

# View sections
TRACE> sections

# Get help
TRACE> help
```

## Step 8: Load Your First Schematic

```bash
# Create a test directory (if you have PDFs)
mkdir -p schematics/electrical

# Copy your PDF to the directory
cp /path/to/your/schematic.pdf schematics/electrical/

# Load and index it
TRACE> load section electrical schematic.pdf --index
```

TRACE will:
1. Convert each page to an image
2. Use Vision AI to extract references, components, terminals
3. Build a searchable index
4. Allow you to query and ask questions

## Troubleshooting

### "git: command not found"
Install git:
- Ubuntu/Debian: `sudo apt-get install git`
- macOS: `xcode-select --install`
- Windows: Download from https://git-scm.com/

### "python3: command not found"
Install Python 3.8 or higher:
- Ubuntu/Debian: `sudo apt-get install python3 python3-pip`
- macOS: `brew install python3`
- Windows: Download from https://www.python.org/

### "ModuleNotFoundError: No module named 'X'"
```bash
pip install -r requirements.txt
```

### "Vision API: Not configured"
Make sure you've set your API key:
```bash
python configure_api_key.py
```

### "Failed to convert page" or "pdf2image not installed"
Install poppler:
- Ubuntu/Debian: `sudo apt-get install poppler-utils`
- macOS: `brew install poppler`
- Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/

### Repository URL

If you don't know your repository URL, check:
- GitHub web interface → Click "Code" button → Copy URL
- Or ask your GitHub admin for the repository URL

It will look like:
- HTTPS: `https://github.com/username/trace_crane_agent2.git`
- SSH: `git@github.com:username/trace_crane_agent2.git`

## Quick Reference

### Essential Commands

```bash
# Start TRACE
python trace_cli.py

# Configure API key
python configure_api_key.py

# Run tests
python test_vision_system.py

# Run setup
./setup_trace.sh

# Update from repository
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### File Structure

```
trace_crane_agent2/
├── trace_cli.py              # Main CLI
├── configure_api_key.py      # API key setup
├── setup_trace.sh            # Automated setup
├── requirements.txt          # Dependencies
├── .env                      # Your API key (you create this)
├── trace/                    # Core modules
│   ├── knowledge_base.py
│   ├── vision_analyzer.py
│   ├── section_manager.py
│   └── pdf_image_converter.py
├── schematics/               # Your PDF files
│   ├── electrical/
│   ├── hydraulic/
│   ├── mechanical/
│   ├── controls/
│   └── general/
└── Documentation files
```

## Next Steps

Once you're set up:

1. **Load your schematics**: `load section electrical <pdf> --index`
2. **Search**: `query <term>`
3. **Ask questions**: `ask <question>`
4. **Train TRACE**: `train` (add your knowledge)
5. **Trace connections**: `trace <component>`

See **VISION_QUICKSTART.md** for detailed usage examples!

---

**Need help?** Check the documentation files or run `help` in TRACE.
