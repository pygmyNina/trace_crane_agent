# TRACE Training System - Technical Overview

## System Architecture

The TRACE (Training and Recognition for Advanced Crane Electronics) system is a comprehensive AI-powered training platform for learning crane electrical schematics.

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                         │
│                         (main.py)                            │
│                   Rich CLI / Menu System                     │
└──────────────────────┬───────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
┌──────────▼──────────┐  ┌────────▼─────────┐
│  Training Interface │  │  PDF Processor    │
│  (Claude AI)        │  │  (PyMuPDF)        │
└──────────┬──────────┘  └────────┬─────────┘
           │                       │
           └───────────┬───────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
┌────────▼────┐ ┌──────▼──────┐ ┌───▼────────┐
│  Knowledge  │ │  Correction │ │  Storage   │
│    Base     │ │   Logger    │ │  System    │
└─────────────┘ └─────────────┘ └────┬───────┘
                                      │
                        ┌─────────────┼─────────────┐
                        │             │             │
                   ┌────▼────┐  ┌─────▼─────┐ ┌────▼────┐
                   │ SQLite  │  │   JSON    │ │  JSONL  │
                   │   DB    │  │  Session  │ │ Correct.│
                   └─────────┘  └───────────┘ └─────────┘
```

## Core Components

### 1. Knowledge Base (`knowledge_base.py`)

**Purpose**: Stores and manages foundation knowledge from October 23 training.

**Key Features**:
- Pre-loaded with crane schematic rules
- Index format definitions
- Wire tracing principles
- Slave sequence patterns
- Component examples
- Extensible for new rules

**Data Structure**:
```json
{
  "version": "1.0",
  "index_format": { ... },
  "wire_tracing": { ... },
  "slave_sequence": { ... },
  "component_examples": { ... }
}
```

**API**:
- `get_index_format_help()` - Get index format guide
- `get_slave_sequence()` - Get slave order
- `get_wire_tracing_rules()` - Get wiring rules
- `format_for_training()` - Get formatted context for AI

### 2. Storage System (`storage.py`)

**Purpose**: Local data persistence using SQLite + JSON.

**Database Schema**:

```sql
-- Training sessions
CREATE TABLE training_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    start_time TEXT,
    end_time TEXT,
    pdf_file TEXT,
    total_questions INTEGER,
    correct_answers INTEGER,
    status TEXT
);

-- Questions and answers
CREATE TABLE qa_log (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    question TEXT,
    user_answer TEXT,
    correct_answer TEXT,
    is_correct INTEGER,
    category TEXT
);

-- Corrections
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    timestamp TEXT,
    question TEXT,
    incorrect_answer TEXT,
    correct_answer TEXT,
    category TEXT,
    notes TEXT
);

-- PDF metadata
CREATE TABLE pdf_metadata (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE,
    upload_date TEXT,
    num_pages INTEGER,
    description TEXT,
    processed INTEGER
);
```

**API**:
- `create_session()` - Start new session
- `end_session()` - End session
- `log_question()` - Record Q&A
- `log_correction()` - Record mistake
- `get_session_stats()` - Get statistics
- `get_category_stats()` - Category performance

### 3. PDF Processor (`pdf_processor.py`)

**Purpose**: Extract and analyze crane schematic PDFs.

**Capabilities**:
- Text extraction from PDFs
- Index reference detection (`=XX/YY.Y.Z`)
- Component identification
- Page rendering to images
- Region extraction
- Search functionality

**Pattern Recognition**:
```python
# Index patterns
full_pattern = r'=(\d{2})/(\d{2})\.(\d)\.(\d)'      # =XX/YY.Y.Z
short_pattern = r'=(\d{2})/(\d{2})\.(\d)(?!\.)'     # =XX/YY.Z

# Component patterns
HVC: r'(HVC\d+)'                    # High Voltage Contactors
Slave: r'(Slave\s*\d+)'             # Slave controllers
Cabinet: r'(Cabinet\s*[A-Z]\d+)'    # Cabinets
```

**API**:
- `extract_page_text(page_num)` - Get text
- `find_index_references()` - Find indices
- `find_components()` - Find components
- `render_page_image()` - Render as image
- `create_training_context()` - Format for AI

### 4. Correction Logger (`correction_logger.py`)

**Purpose**: Track mistakes and provide feedback.

**Features**:
- Categorized error tracking
- Problem area identification
- Review question generation
- Feedback reports
- Export capabilities

**Categories**:
```python
CATEGORIES = {
    "index_format": "Index format interpretation",
    "wire_tracing": "Wire tracing and connections",
    "component_identification": "Component identification",
    "slave_sequence": "Slave sequence understanding",
    "module_counting": "Module counting",
    "schematic_reading": "General schematic reading",
    "notation": "Notation and shorthand",
    "location": "Component location finding"
}
```

**API**:
- `log_correction()` - Record mistake
- `get_problem_areas()` - Identify weak areas
- `generate_feedback()` - Create feedback
- `generate_review_questions()` - Create review
- `format_correction_report()` - Export report

### 5. Training Interface (`training_interface.py`)

**Purpose**: Conversational AI training using Claude.

**Features**:
- Interactive Q&A
- Context-aware questions
- Immediate feedback
- Progress tracking
- Multiple training modes

**Training Modes**:
1. **Interactive Training** - Free-form conversation
2. **Quiz Mode** - Structured assessment
3. **Category Practice** - Focused practice
4. **PDF Training** - PDF-based questions

**System Prompt Structure**:
```
You are a TRACE training assistant...

# Foundation Knowledge
[Knowledge base context]

# Training Approach
- Ask clear questions
- Provide detailed explanations
- Categorize questions
- Be encouraging

# Question Types
- Index format
- Wire tracing
- Component locations
- Slave configurations
- Module counting
```

**API**:
- `start_session()` - Begin training
- `end_session()` - Complete training
- `chat()` - Send/receive messages
- `interactive_training()` - Interactive mode
- `quiz_mode()` - Quiz mode
- `practice_category()` - Category practice

### 6. Main Application (`main.py`)

**Purpose**: CLI interface and application orchestration.

**Menu System**:
```
1. Start Training Session
2. Quiz Mode
3. Practice Category
4. Review Sessions
5. View Knowledge Base
6. Load PDF
7. Statistics
8. Exit
```

**Command Line Options**:
```bash
python main.py                              # Interactive menu
python main.py --pdf file.pdf               # With PDF
python main.py --mode quiz                  # Quiz mode
python main.py --mode practice --category X # Practice
```

## Data Flow

### Training Session Flow

```
1. User starts session
   └─> Storage creates session record
   └─> Correction logger initializes
   └─> Knowledge base loaded

2. AI asks question
   └─> Question generated from knowledge base
   └─> Category assigned
   └─> Context from PDF (if loaded)

3. User answers
   └─> Answer recorded in database
   └─> Correctness evaluated
   └─> If wrong: correction logged

4. AI provides feedback
   └─> Explanation generated
   └─> Category noted
   └─> Next question prepared

5. Session ends
   └─> Statistics calculated
   └─> Feedback generated
   └─> Data persisted
```

### Correction Flow

```
User makes mistake
  │
  ├─> Log to database (corrections table)
  ├─> Log to JSON session file
  ├─> Log to JSONL corrections file
  │
  └─> Analysis
      ├─> Category identified
      ├─> Problem area flagged
      └─> Review question added
```

## File System Structure

```
trace_crane_agent/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── .env.example               # Config template
├── .gitignore                 # Git ignore rules
│
├── README.md                  # Main documentation
├── QUICKSTART.md              # Quick start guide
├── EXAMPLES.md                # Training examples
├── SYSTEM_OVERVIEW.md         # This file
│
├── src/                       # Source code
│   ├── __init__.py
│   ├── knowledge_base.py      # Knowledge management
│   ├── storage.py             # Data persistence
│   ├── pdf_processor.py       # PDF handling
│   ├── correction_logger.py   # Error tracking
│   └── training_interface.py  # AI interface
│
├── tests/                     # Test suite
│   ├── test_knowledge_base.py
│   └── test_storage.py
│
└── data/                      # Local data storage
    ├── training.db            # SQLite database
    ├── knowledge_base/        # Foundation knowledge
    │   └── foundation.json
    ├── training_sessions/     # Session data
    │   └── session_*/
    │       └── metadata.json
    ├── corrections/           # Corrections
    │   └── session_*_corrections.jsonl
    └── pdfs/                  # Uploaded PDFs
```

## Technology Stack

### Core Technologies
- **Python 3.8+** - Programming language
- **Anthropic Claude** - AI training assistant
- **SQLite** - Structured data storage
- **PyMuPDF (fitz)** - PDF processing
- **Rich** - Terminal UI
- **Pillow** - Image processing

### Libraries
```
anthropic>=0.25.0     # Claude AI API
PyMuPDF>=1.23.0       # PDF processing
python-dotenv>=1.0.0  # Environment config
pillow>=10.0.0        # Image handling
rich>=13.0.0          # CLI interface
```

## API Integration

### Anthropic Claude API

**Model**: `claude-3-5-sonnet-20241022`

**Request Structure**:
```python
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2048,
    system=system_prompt,    # Knowledge + instructions
    messages=conversation    # User/assistant history
)
```

**Context Management**:
- System prompt includes foundation knowledge
- Conversation history maintained
- PDF context added when available
- Category information included

## Security & Privacy

### API Key Management
- Stored in `.env` file (not committed)
- Never logged or displayed
- Environment variable support

### Data Privacy
- All training data stored locally
- No data uploaded to cloud (except Claude API calls)
- Sessions isolated
- No PII collection

### PDF Handling
- Processed locally
- Never uploaded to external services
- Metadata stored locally only

## Performance Considerations

### Database Optimization
- Indexed on session_id, timestamp
- Prepared statements used
- Connection pooling for tests

### PDF Processing
- Lazy loading of pages
- Configurable zoom levels
- Region extraction for efficiency
- Text caching

### AI Calls
- Context limited to 2048 tokens
- Conversation history pruned if needed
- Efficient system prompt

## Extensibility

### Adding New Categories
```python
# In correction_logger.py
CATEGORIES["new_category"] = "Description"
```

### Adding New Knowledge Rules
```python
kb = KnowledgeBase()
kb.add_rule("category", {"rule": "...", "description": "..."})
kb.save()
```

### Custom Training Modes
```python
class CustomTrainer(TrainingInterface):
    def custom_mode(self):
        # Implement custom training logic
        pass
```

## Testing

### Test Coverage
- Knowledge base creation and retrieval
- Storage operations (CRUD)
- Session management
- Correction logging
- PDF processing (manual)

### Running Tests
```bash
python tests/test_knowledge_base.py
python tests/test_storage.py
```

## Monitoring & Analytics

### Available Metrics
- Questions per session
- Accuracy per category
- Overall accuracy
- Problem areas
- Improvement trends
- Time per session

### Statistics Queries
```python
storage.get_session_stats(session_id)
storage.get_category_stats()
storage.list_sessions()
```

## Future Enhancements

### Potential Additions
1. **Web Interface** - Browser-based UI
2. **Image Recognition** - Analyze schematic images directly
3. **Spaced Repetition** - Optimize learning schedule
4. **Multi-user Support** - Multiple user profiles
5. **Export to Anki** - Flashcard generation
6. **Voice Interface** - Speech recognition
7. **Mobile App** - iOS/Android support
8. **Collaborative Learning** - Share sessions
9. **Advanced Analytics** - Learning curves, predictions
10. **Integration** - LMS integration

## Troubleshooting

### Common Issues

**Database locked**
- Close all connections
- Delete `.db-journal` file

**API rate limits**
- Reduce request frequency
- Implement backoff strategy

**PDF extraction fails**
- Check PDF format
- Update PyMuPDF
- Try different zoom level

**Out of memory**
- Process PDFs page by page
- Limit conversation history
- Use region extraction

## Version History

### v1.0.0 (October 23, 2025)
- Initial release
- Foundation knowledge from October 23 training
- All core features implemented
- Full test coverage
- Complete documentation

## License

[Specify license]

## Contributors

[List contributors]

---

**Last Updated**: October 23, 2025
**Version**: 1.0.0
**Status**: Production Ready
