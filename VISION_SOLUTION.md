# TRACE Vision Solution for Image/Vector-Based Schematics

## Problem Statement

Crane schematic PDFs are:
- Image and vector-based (CAD drawings), not text-based
- Static reference documents organized by section
- Needed for answering mechanics' questions
- Cannot be processed with simple text extraction

## Recommended Solution: AI Vision-Powered Reference System

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    TRACE System                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Section-Based PDF Storage                           │
│     - Electrical/                                        │
│     - Hydraulic/                                         │
│     - Mechanical/                                        │
│     - Controls/                                          │
│                                                          │
│  2. PDF Registry & Index                                │
│     - Tracks sections, PDFs, and page content           │
│     - Metadata: references, components, locations       │
│                                                          │
│  3. On-Demand Image Conversion                          │
│     - Converts PDF pages to images when needed          │
│     - Caches converted images                           │
│                                                          │
│  4. AI Vision Analysis (Claude)                         │
│     - Analyzes schematic images on request              │
│     - Extracts references, traces connections           │
│     - Answers questions about specific sections         │
│                                                          │
│  5. Knowledge Base Integration                          │
│     - Links learned knowledge to PDF sources            │
│     - Cross-references between sections                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Solution Options

#### Option 1: AI Vision Primary (RECOMMENDED)
**Best for: Mechanics asking questions about schematics**

**How it works:**
1. Store PDFs organized by section (Electrical, Hydraulic, etc.)
2. Maintain a lightweight index of what's in each PDF
3. When mechanic asks a question, identify relevant sections
4. Convert relevant PDF pages to images
5. Send images to Claude Vision API with the question
6. Return AI-analyzed answer with page references

**Pros:**
- Understands complex diagrams and symbols
- Can trace connections visually
- Answers questions naturally
- No pre-processing needed
- Handles updates easily

**Cons:**
- Requires API key and internet connection
- Small cost per query (~$0.01-0.05)
- Slight delay for analysis

#### Option 2: OCR + Vision Hybrid
**Best for: Building searchable index + answering questions**

**How it works:**
1. Pre-process PDFs with OCR to extract text/references
2. Build searchable index of components and references
3. Use OCR index to quickly find relevant pages
4. Use Vision for complex questions about those pages

**Pros:**
- Fast text-based searches
- Lower ongoing costs
- Works offline for searches

**Cons:**
- OCR quality varies on technical drawings
- Requires pre-processing time
- Two-step process

#### Option 3: Manual Indexing + Vision
**Best for: Small number of well-known schematics**

**How it works:**
1. Manually document what's in each section/PDF
2. Train TRACE about the organization
3. Use Vision API only when specific page analysis needed

**Pros:**
- Most accurate index
- Full control over organization
- Lowest API costs

**Cons:**
- Manual effort required
- Needs maintenance
- Slower to scale

## Recommended Implementation

### Phase 1: Section-Based Storage
```
schematics/
├── electrical/
│   ├── main_power.pdf
│   ├── control_circuits.pdf
│   └── slave_22_detail.pdf
├── hydraulic/
│   ├── pump_system.pdf
│   └── valve_control.pdf
├── mechanical/
│   └── hoist_assembly.pdf
└── registry.json  # Index of all sections
```

### Phase 2: Vision-Powered Assistant

**Workflow:**
```python
Mechanic: "Where does the HVC3 breaker connect?"

TRACE:
1. Checks knowledge base (instant)
   → "HVC3 breaker signal → =61/4.1.3"

2. Asks: "Want me to show you on the schematic?"

3. If yes:
   - Opens electrical/control_circuits.pdf, page 12
   - Converts to image
   - Highlights the connection using Vision AI
   - Shows reference location
```

### Phase 3: Learning from Schematics

When training:
```python
Mechanic: "Look at electrical/main_power.pdf page 5"

TRACE:
1. Converts page to image
2. Analyzes with Vision AI
3. Extracts: "Found Slave 22, Cabinet E11,
   references =22/1.1.1 through =22/45.8.3"
4. Asks: "What would you like me to learn?"

Mechanic: "Remember that Slave 22 is on page 5"

TRACE: ✓ Saved: Slave 22 → electrical/main_power.pdf:5
```

## Technical Requirements

### Required Libraries
```
pdf2image>=1.16.0       # Convert PDF to images
Pillow>=10.0.0          # Image processing
anthropic>=0.18.0       # Claude Vision API
python-dotenv>=1.0.0    # API key management
```

### System Requirements
- Poppler (for pdf2image)
- ~500MB disk space per 100-page PDF (for image cache)
- Internet connection for Vision API

### Optional Enhancements
```
pytesseract>=0.3.10     # OCR for text extraction
opencv-python>=4.8.0    # Advanced image processing
fitz (PyMuPDF)>=1.23.0  # Vector graphics extraction
```

## Cost Estimate

### Claude Vision API Pricing (Approximate)
- Cost per image: ~$0.01-0.05 (depending on resolution)
- Typical query: 1-3 pages = $0.01-0.15
- 100 queries/month = $1-15/month
- Heavy use (500 queries) = $5-75/month

Compare to:
- Time saved finding information: Priceless
- Reduced errors: Priceless
- Faster troubleshooting: Priceless

## Next Steps

1. **Choose Solution**: Option 1 (AI Vision Primary) recommended
2. **Setup API**: Get Anthropic API key
3. **Organize PDFs**: Create section directories
4. **Build Registry**: Index what's in each PDF
5. **Implement Vision**: Add Claude Vision integration
6. **Test Workflow**: Try with real mechanic questions

## Example Usage (After Implementation)

```bash
TRACE> load section electrical main_power.pdf
✓ Loaded: Electrical / Main Power (15 pages)
  Found: Slaves 22, 23, 60
  References: =10/*, =22/*, =23/*

TRACE> ask "Where is terminal 1U on the main transformer?"
🔍 Analyzing electrical/main_power.pdf...
📄 Found on page 3, zone 102.0.3

Answer: Terminal 1U is located on the main transformer at
reference =10/102.0.3. It connects to the primary power
feed from the main breaker panel. [View: page 3]

TRACE> show page 3
[Displays converted image of page 3]
```

Would you like me to implement Option 1 (AI Vision Primary)?
