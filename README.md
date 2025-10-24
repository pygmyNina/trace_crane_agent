# TRACE Training System for Crane Schematics

An intelligent, AI-powered training system for learning to read and interpret crane electrical schematics. Uses Claude AI for interactive conversational training.

## Features

### 1. **PDF Processing System**
- Import and analyze crane schematic PDFs
- Extract text and component references
- Identify index references (=XX/YY.Y.Z format)
- Find components and their locations
- Support for page-by-page analysis

### 2. **Conversational Training Interface**
- Interactive AI trainer powered by Claude
- Natural language Q&A
- Immediate feedback and explanations
- Context-aware question generation
- Multiple training modes:
  - Interactive training
  - Quiz mode
  - Category-specific practice

### 3. **Correction Logging System**
- Tracks all mistakes and corrections
- Categorizes errors by topic
- Identifies problem areas
- Generates improvement recommendations
- Exports correction reports

### 4. **Local Storage**
- SQLite database for structured data
- JSON files for detailed session logs
- Training history tracking
- Performance analytics
- Category-based statistics

### 5. **Foundation Knowledge Base**
Built on October 23 training foundations:
- **Index Format**: `=XX/YY.Y.Z` where XX=section, YY.Y=sheet, Z=column
- **Shorthand Notation**: `=61/102.8` means `=61/102.0.8`
- **Wire Tracing**: Dots indicate connections; perpendicular crossings without dots aren't connected
- **Slave Sequence**: Non-chronological order (22, 23, 60, 24, 61, 20)
- **Component Examples**: Detailed module configurations and locations

## Installation

### Prerequisites
- Python 3.8 or higher
- Anthropic API key (for Claude AI)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd trace_crane_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API Key**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_api_key_here
```

Alternatively, set the environment variable:
```bash
export ANTHROPIC_API_KEY=your_api_key_here
```

## PDF Library Setup (Optional)

The system includes a PDF library for organizing and training with crane schematic PDFs.

### Quick Setup

1. **Add your PDFs** to the appropriate section directory:
```bash
cp /path/to/your/*.pdf data/pdfs/section_61/
```

2. **Catalog the PDFs** to index them:
```bash
python scripts/catalog_pdfs.py --scan
```

3. **Train with a section**:
```bash
python scripts/train_with_section.py --section 61
```

**For detailed instructions**, see [PDF_SETUP_GUIDE.md](PDF_SETUP_GUIDE.md)

### PDF Library Features

- 📁 **Organized by section** - Keep PDFs organized (section_61/, section_10/, etc.)
- 📊 **Automatic cataloging** - Extract metadata, index references, components
- 🎯 **Section training** - Train with entire sections or specific sheets
- 📋 **Smart indexing** - Automatically detect index references and components
- 🔍 **Easy navigation** - List and browse available PDFs

### PDF Library Commands

```bash
# Catalog all PDFs
python scripts/catalog_pdfs.py --scan

# View catalog
python scripts/catalog_pdfs.py --show

# List available sections
python scripts/train_with_section.py --list

# Train with section 61
python scripts/train_with_section.py --section 61

# Train with specific sheets
python scripts/train_with_section.py --section 61 --sheets 1,2,3
```

## Usage

### Interactive Menu Mode

Start the application with the interactive menu:

```bash
python main.py
```

This will show a menu with options:
1. Start Training Session (Interactive)
2. Quiz Mode
3. Practice Specific Category
4. Review Past Sessions
5. View Foundation Knowledge
6. Load PDF Schematic
7. Statistics
8. Exit

### Command Line Options

**Start training with a PDF:**
```bash
python main.py --pdf path/to/schematic.pdf
```

**Quiz mode:**
```bash
python main.py --mode quiz
```

**Practice specific category:**
```bash
python main.py --mode practice --category index_format
```

### Training Categories

The system covers these categories:

- `index_format` - Index format interpretation (=XX/YY.Y.Z)
- `wire_tracing` - Wire tracing and connections
- `component_identification` - Component identification
- `slave_sequence` - Slave sequence understanding
- `module_counting` - Module counting and configuration
- `schematic_reading` - General schematic reading
- `notation` - Notation and shorthand
- `location` - Component location finding

## Project Structure

```
trace_crane_agent/
├── main.py                      # Main entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment config
├── README.md                    # This file
├── src/
│   ├── knowledge_base.py        # Foundation knowledge management
│   ├── storage.py               # Local storage system
│   ├── pdf_processor.py         # PDF processing utilities
│   ├── correction_logger.py     # Correction tracking
│   └── training_interface.py    # AI training interface
├── data/
│   ├── training_sessions/       # Session data
│   ├── corrections/             # Correction logs
│   ├── knowledge_base/          # Foundation knowledge
│   ├── pdfs/                    # Uploaded PDFs
│   └── training.db              # SQLite database
└── tests/                       # Test files
```

## How It Works

### 1. Foundation Knowledge

The system is pre-loaded with foundation knowledge from the October 23 training:

- Index format rules and examples
- Wire tracing principles
- Slave sequence patterns
- Component configurations
- Real-world examples (HVC3, Main Transformer, Slave 22, etc.)

### 2. Training Flow

1. **Start Session**: Creates a new training session in the database
2. **Load PDF** (optional): Import crane schematic for reference
3. **Interactive Training**: AI asks questions, user answers
4. **Correction Tracking**: System logs mistakes and provides feedback
5. **Review & Analytics**: View progress and identify improvement areas

### 3. AI Trainer

The AI trainer (Claude):
- Understands crane schematic notation
- Generates contextual questions
- Provides detailed explanations
- Adapts to user's skill level
- Tracks progress across categories

### 4. Data Storage

All training data is stored locally:
- **SQLite Database**: Structured queries and statistics
- **JSON Files**: Detailed session logs
- **JSONL Files**: Correction history
- No data leaves your machine (except API calls to Claude)

## Example Training Session

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   TRACE Training System for Crane Schematics                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

[AI Trainer]: Hello! I'm your TRACE training assistant. Let's start with
a fundamental question about index notation.

Question: What does the shorthand notation =61/102.8 expand to in full format?

Your answer: =61/102.8.0

[AI Trainer]: Not quite! The shorthand =61/102.8 actually expands to =61/102.0.8

Explanation: In shorthand notation, when the sheet minor digit (.Y) is 0,
it can be omitted. So =61/102.8 means section 61, sheet 102.0, column 8.

The format is =XX/YY.Y.Z where:
- XX = Section (61)
- YY.Y = Sheet (102.0)
- Z = Column (8)

Let's try another question...
```

## API Usage

You can also use the components programmatically:

```python
from dotenv import load_dotenv
from src.training_interface import TrainingInterface

load_dotenv()

# Create trainer
trainer = TrainingInterface()

# Start session
trainer.start_session(pdf_file="schematics/crane_01.pdf")

# Interactive training
trainer.interactive_training()

# Or send specific messages
response = trainer.chat("What is the index format?")
print(response)

# End session
trainer.end_session()
```

## Knowledge Base API

```python
from src.knowledge_base import KnowledgeBase

kb = KnowledgeBase()

# Get formatted knowledge
print(kb.format_for_training())

# Get specific information
print(kb.get_index_format_help())
print(kb.get_slave_sequence())
print(kb.get_wire_tracing_rules())
```

## PDF Processing API

```python
from src.pdf_processor import SchematicPDFProcessor

with SchematicPDFProcessor("schematic.pdf") as processor:
    # Extract text
    text = processor.extract_page_text(0)

    # Find index references
    refs = processor.find_index_references()

    # Find components
    components = processor.find_components()

    # Get page info
    info = processor.get_page_info(0)

    # Create training context
    context = processor.create_training_context(0)
```

## Statistics and Analytics

View your training statistics:

```bash
python main.py
# Select option 7 (Statistics)
```

This shows:
- Performance by category
- Overall accuracy
- Total questions answered
- Problem areas
- Improvement trends

## Reviewing Sessions

Review past training sessions:

```bash
python main.py
# Select option 4 (Review Past Sessions)
```

Shows:
- Session history
- Questions and answers
- Corrections made
- Session statistics

## Troubleshooting

### API Key Issues

If you see "ANTHROPIC_API_KEY not found":
1. Make sure you created a `.env` file
2. Check that it contains `ANTHROPIC_API_KEY=your_key`
3. Or export the variable: `export ANTHROPIC_API_KEY=your_key`

### PDF Loading Issues

If PDFs don't load:
1. Ensure PyMuPDF is installed: `pip install PyMuPDF`
2. Check file path is correct
3. Verify PDF is not password-protected

### Database Issues

If database errors occur:
- Delete `data/training.db` to reset
- Session history will be lost but foundation knowledge preserved

## Development

### Running Tests

```bash
# Test individual components
python src/knowledge_base.py
python src/storage.py
python src/pdf_processor.py path/to/test.pdf
```

### Adding New Categories

Edit `src/correction_logger.py` and add to the `CATEGORIES` dictionary:

```python
CATEGORIES = {
    "your_category": "Description of your category",
    # ... existing categories
}
```

### Extending Knowledge Base

```python
from src.knowledge_base import KnowledgeBase

kb = KnowledgeBase()
kb.add_rule("custom_category", {
    "rule": "Your rule",
    "description": "Detailed description"
})
kb.save()
```

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines here]

## Support

For issues and questions:
- Check the troubleshooting section
- Review the foundation knowledge (option 5 in menu)
- Examine the example sessions above

## Acknowledgments

Foundation knowledge based on October 23, 2025 crane schematic training session.

Built with:
- [Claude AI](https://www.anthropic.com/claude) - Conversational training
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Rich](https://rich.readthedocs.io/) - Terminal UI
- [SQLite](https://www.sqlite.org/) - Local storage
