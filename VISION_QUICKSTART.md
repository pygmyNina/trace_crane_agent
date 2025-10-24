# TRACE Vision Features - Quick Start

Get up and running with TRACE Vision in 10 minutes!

## What's New in Vision-Enabled TRACE

TRACE can now:
- **Automatically index** image/vector-based schematic PDFs
- **Read text** from schematics (references, components, terminals)
- **Answer questions** about your schematics using AI
- **Trace connections** visually between components
- **Search across** both indexed text and visual content

## Setup

### 1. Install Dependencies

```bash
./setup_trace.sh
```

Or manually:
```bash
# Install Python packages
pip install -r requirements.txt

# Install poppler (for PDF conversion)
# Ubuntu/Debian:
sudo apt-get install poppler-utils

# macOS:
brew install poppler
```

### 2. Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Create an account (if needed)
3. Generate an API key

### 3. Configure API Key

Create a `.env` file:
```bash
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

Or export it:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

### 4. Launch TRACE

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
```

## First Steps

### 1. Organize Your PDFs by Section

TRACE uses five sections:
- `electrical` - Electrical schematics
- `hydraulic` - Hydraulic systems
- `mechanical` - Mechanical drawings
- `controls` - Control systems
- `general` - Other documentation

### 2. Load and Index a PDF

```bash
TRACE> load section electrical main_power.pdf --index
```

What happens:
1. PDF is copied to `schematics/electrical/`
2. Each page is converted to an image
3. Vision AI extracts references, components, terminals
4. Searchable index is created

This will take about 2-3 seconds per page.

**Cost:** ~$0.02 per page (one-time, not recurring)

### 3. Search the Index

```bash
TRACE> query slave 22
```

Returns:
```
🔍 Searching for 'slave 22'...
============================================================

📄 Schematic Index Results (2 pages):

  [ELECTRICAL] main_power.pdf, Page 5
    Slave 22 configuration in Cabinet E11 with 45 modules
    • Component: Slave 22
    • Cabinet: E11

  [ELECTRICAL] slave_wiring.pdf, Page 2
    Slave 22 wiring connections to main bus
    • Component: Slave 22
```

**Cost:** Free (uses stored index)

### 4. Ask a Question

```bash
TRACE> ask Where is terminal 1U on the main transformer?
```

What happens:
1. TRACE searches index for "transformer" and "terminal"
2. Finds relevant page(s)
3. Converts to images
4. Sends to Vision AI with your question
5. Returns detailed answer

**Cost:** ~$0.02-0.05 per question

### 5. Trace a Connection

```bash
TRACE> trace HVC3 breaker
```

Or trace between two points:
```bash
TRACE> trace HVC3 breaker to =61/4.1.3
```

**Cost:** ~$0.02-0.05 per trace

### 6. Analyze a Specific Page

```bash
TRACE> analyze electrical main_power.pdf 3
```

Gets detailed analysis of that specific page.

## Example Workflow

```bash
# Start TRACE
python trace_cli.py

# Load your main electrical schematic and index it
TRACE> load section electrical crane_electrical_2024.pdf --index
📄 Loading crane_electrical_2024.pdf into section 'electrical'...
🔍 Auto-indexing with Vision AI...
  Page 1/15: Analyzing... ✓ (12 refs, 8 components)
  Page 2/15: Analyzing... ✓ (15 refs, 6 components)
  ...
✓ Indexed 15 pages

# Load hydraulic schematics
TRACE> load section hydraulic pump_system.pdf --index

# Search for a component
TRACE> query slave 22
📄 Found on electrical/crane_electrical_2024.pdf, Page 5

# Ask a question
TRACE> ask How many modules does Slave 22 have?
🔍 Analyzing electrical/crane_electrical_2024.pdf page 5...
📖 Answer: Slave 22 has 45 modules total, consisting of...

# Train TRACE about what you learned
TRACE> train
Training> Slave 22 powers the hoist motors
✓ Learned about Slave 22

# View all sections
TRACE> sections
📁 ELECTRICAL
   • crane_electrical_2024.pdf
📁 HYDRAULIC
   • pump_system.pdf

# Export your knowledge
TRACE> export my_crane_knowledge.json
```

## Command Cheat Sheet

### Loading PDFs
```bash
load section electrical <file.pdf>         # Load without indexing
load section electrical <file.pdf> --index # Load and auto-index
index electrical <file.pdf>                # Index later
```

### Searching
```bash
query <search term>    # Search both knowledge base and index
ask <question>         # Ask AI about schematics
analyze <section> <pdf> <page>  # Deep analysis of one page
trace <component>      # Trace component connections
```

### Organization
```bash
sections               # List all sections
section electrical     # Show electrical section details
```

### Training (Legacy)
```bash
train                  # Enter training mode
show slaves            # Show all known slaves
summary                # Knowledge base summary
```

### System
```bash
cache stats            # Show image cache size
cache clear            # Clear cache to free disk space
help                   # Show all commands
```

## Cost Management

### One-Time Costs (Indexing)
- Small project (100 pages): ~$2
- Medium project (500 pages): ~$10
- Large project (1000 pages): ~$20

### Ongoing Costs (Queries)
- Text searches: **FREE** (uses index)
- AI questions: ~$0.02-0.05 each
- Typical monthly use: $5-20

### Tips to Minimize Costs
1. **Index once** - PDFs rarely change, so you only pay to index once
2. **Search first** - Use `query` (free) before `ask` (paid)
3. **Be specific** - Better questions = fewer follow-ups
4. **Cache images** - Converted images are cached for reuse

## Troubleshooting

### "Vision API not configured"
```bash
# Check if API key is set
echo $ANTHROPIC_API_KEY

# If not, set it
export ANTHROPIC_API_KEY=your-key-here

# Or create .env file
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### "pdf2image not installed"
```bash
pip install pdf2image
# Also need poppler
sudo apt-get install poppler-utils  # Linux
brew install poppler                # macOS
```

### "Failed to convert page"
- Check poppler is installed
- Verify PDF is not corrupted
- Try a different PDF

### Slow indexing
- Normal: 2-3 seconds per page
- Reduce DPI: Edit `pdf_image_converter.py`, change default dpi=200 to dpi=150

## What's Next?

1. **Index all your schematics** - One-time investment
2. **Train TRACE** - Add your specific knowledge
3. **Ask questions** - Get instant answers with page references
4. **Trace connections** - Understand signal paths
5. **Build knowledge** - TRACE learns from your corrections

## Need Help?

- See full documentation: `README.md`
- Vision solution design: `VISION_SOLUTION.md`
- Architecture details: `VISION_INDEXING.md`

---

**You now have an AI assistant that can read your crane schematics!**
