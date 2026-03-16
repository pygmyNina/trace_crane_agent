# TRACE - Crane Schematic Assistant & Copilot

**T**raining **R**etention and **A**ssistance for **C**rane **E**lectrical systems

TRACE is an intelligent assistant designed to help crane mechanics understand, document, and navigate complex crane electrical schematics. It learns from your training and builds a searchable knowledge base of crane components, connections, and schematic conventions.

## Features

- **Knowledge Base**: Persistent storage of crane schematic information
  - Slave configurations and module details
  - Electrical connections and signal routing
  - Component sequences
  - Schematic notation rules

- **Conversational Training**: Teach TRACE through natural language
  - "Slave 22 has 45 modules in Cabinet E11"
  - "HVC3 breaker signal goes to =61/4.1.3"
  - "Slave sequence: 22,23,60,24,61,20"

- **PDF Schematic Loader**: Import and extract data from schematic PDFs

- **Search & Query**: Quickly find information about slaves, connections, and components

- **Corrections & Learning**: TRACE remembers your corrections and improves over time

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd trace_crane_agent2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Import the initial training data (October 23):
```bash
python import_oct23_training.py
```

## Quick Start

Launch TRACE:
```bash
python trace_cli.py
```

You'll see the TRACE prompt:
```
TRACE>
```

### Basic Commands

```bash
# Get help
TRACE> help

# View knowledge summary
TRACE> summary

# Show all known slaves
TRACE> show slaves

# Show specific slave details
TRACE> show slave 22

# Search the knowledge base
TRACE> query cabinet E11
TRACE> query breaker

# Enter training mode
TRACE> train
```

## Training TRACE

Enter training mode to teach TRACE about your crane schematics:

```bash
TRACE> train
Training> Slave 23 has 30 modules in Cabinet E12
  ✓ Slave 23: 30 modules in E12
✓ Learned about Slave 23

Training> The main contactor goes to =15/200.5.1
  ✓ Connection: main contactor → =15/200.5.1
✓ Learned connection from main contactor to =15/200.5.1

Training> done
✓ Training session saved
```

### Training Input Examples

**Slave Configuration:**
```
Slave 60 has 20 modules (2 IM151, 1 PM, 15 DI, 2 DO) in Cabinet E15
```

**Connections:**
```
Emergency stop button goes to =20/50.1.2
Motor M1 connects to =10/102.0.5
```

**Sequences:**
```
Hoist sequence: 10,11,12,13
Drive slave sequence: 20,21,22
```

**Rules and Notation:**
```
Wire rule: red wires indicate 24V DC power
Index format: first number is drawing sheet, second is zone
```

**Corrections:**
```
Actually, Slave 22 is in Cabinet E10, not E11
Correction: the breaker signal goes to =61/4.1.4
```

## Loading PDF Schematics

Place PDF files in the `schematics/` directory or load from any path:

```bash
TRACE> load schematics/crane_electrical.pdf
Loading PDF: schematics/crane_electrical.pdf
✓ Loaded 15 pages from crane_electrical.pdf

Extracted:
  Slaves: 22, 23, 60
  Cabinets: E11, E12, E15
  References: 47 found
```

## October 23 Training Data

The system comes pre-loaded with training data from October 23:

- **Index Format**: =XX/YY.Y.Z
- **Slave Sequence**: 22, 23, 60, 24, 61, 20
- **Slave 22**: 45 modules (1 IM151, 1 PM, 40 DI, 3 RTD) in Cabinet E11
- **HVC3 Connection**: Breaker signal → =61/4.1.3
- **Main Transformer**: Located at =10/102.0.3, terminal 1U
- **Wire Rules**:
  - Dots = connections
  - Perpendicular crossings without dots = no connection

## Knowledge Base Structure

TRACE stores knowledge in `trace_knowledge.json` with these categories:

- **schema_rules**: Notation formats and wire connection rules
- **components**: Slaves, modules, cabinets, breakers, transformers
- **connections**: Signal paths and electrical connections
- **sequences**: Ordered component sequences
- **learnings**: Training notes and corrections
- **training_sessions**: History of training activities

## Command Reference

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `train` | Enter training mode |
| `query <text>` | Search knowledge base |
| `load <pdf>` | Load PDF schematic |
| `list` | List available schematics |
| `show slaves` | Display all slaves |
| `show slave <N>` | Show slave N details |
| `show connections` | Display all connections |
| `summary` | Knowledge base summary |
| `export [file]` | Export knowledge to file |
| `quit` | Exit TRACE |

## Use Cases

### Finding Component Information
```bash
TRACE> query slave 22
[Slave 22]
  Cabinet: E11
  Modules: 45
  Types: IM151, PM, DI, DI, DI...
```

### Tracing Signal Paths
```bash
TRACE> query HVC3
[Connection]
  From: HVC3 breaker signal
  To: =61/4.1.3
  Type: breaker_signal
```

### Understanding Notation
```bash
TRACE> query index format
[Learning: index_format]
  Index format: =XX/YY.Y.Z - This is the standard reference format...
```

## Architecture

TRACE consists of four main components:

1. **KnowledgeBase** (`trace/knowledge_base.py`)
   - JSON-based persistent storage
   - CRUD operations for components
   - Search and retrieval

2. **PDFSchematicLoader** (`trace/pdf_loader.py`)
   - PDF text extraction
   - Reference pattern matching
   - Component detection

3. **TrainingInterface** (`trace/training_interface.py`)
   - Natural language parsing
   - Knowledge extraction
   - Session management

4. **TRACECLI** (`trace_cli.py`)
   - Command-line interface
   - Interactive training mode
   - Query and display functions

## Future Enhancements

- AI-powered natural language understanding (Claude integration)
- Visual schematic annotation and markup
- Multi-crane project support
- Export to documentation formats
- Mobile companion app
- Real-time collaboration features

## Contributing

This project is designed for crane mechanics. Suggestions and improvements are welcome!

## License

Copyright 2024 - TRACE Crane Assistant Project

---

**Built for crane mechanics, by crane mechanics.**
