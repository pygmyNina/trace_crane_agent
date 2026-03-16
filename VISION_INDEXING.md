# Vision-Based Auto-Indexing for TRACE

## The Better Approach: Vision for BOTH Indexing AND Analysis

Since your PDFs contain some text, we can use Claude Vision to:
1. **Read the text** (references, labels, component names)
2. **Understand the visual context** (what's connected where)
3. **Build a searchable index** automatically
4. **Answer questions** using both the index and visual analysis

## How Claude Vision Reads Text in Images

Claude Vision is excellent at:
- Reading printed text (even small labels)
- Understanding technical notation (=XX/YY.Y.Z format)
- Extracting component IDs (Slave 22, Cabinet E11)
- Reading terminal labels (1U, 2V, etc.)
- Identifying wire numbers and connection points

**Better than traditional OCR because:**
- Understands context ("This is a reference" vs "This is a wire label")
- Handles rotated/angled text
- Reads text on complex backgrounds
- Understands symbols AND text together

## Recommended Workflow: Auto-Index on Load

### Step 1: Load PDF with Auto-Indexing

```bash
TRACE> load section electrical main_power.pdf --index
📄 Loading electrical/main_power.pdf (15 pages)
🔍 Auto-indexing with Vision AI...

Page 1: Analyzing...
  ✓ Found: Main breaker panel
  ✓ References: =10/1.1.1 to =10/5.3.2
  ✓ Components: Breakers B1-B12

Page 2: Analyzing...
  ✓ Found: Power distribution
  ✓ References: =10/10.0.1 to =10/15.2.3
  ✓ Connections: Main bus to subfeeders

Page 3: Analyzing...
  ✓ Found: Main transformer
  ✓ References: =10/102.0.3
  ✓ Terminals: 1U, 2V, 3W
  ✓ Components: Transformer T1

...

✓ Indexed 15 pages in 45 seconds
✓ Found: 156 references, 45 components, 12 cabinets
✓ Created searchable index
```

### Step 2: Fast Searches Using Index

```bash
TRACE> query =10/102.0.3
📊 Index Results:
  → electrical/main_power.pdf, Page 3
    Component: Main transformer T1
    Terminal: 1U
    Context: "Primary power feed connection"

TRACE> query transformer
📊 Index Results:
  → electrical/main_power.pdf, Page 3 - Main transformer T1
  → electrical/control_circuits.pdf, Page 8 - Control transformer T2
  → hydraulic/pump_system.pdf, Page 2 - Pump isolation transformer
```

### Step 3: Deep Analysis When Needed

```bash
TRACE> ask "How does the main transformer connect to the breaker panel?"

🔍 Checking index... Found on pages 1 and 3
🔍 Analyzing visual connections...

Answer: The main transformer (T1 at =10/102.0.3) connects to
the main breaker panel via three-phase conductors:
- Terminal 1U → Main breaker B1 input (=10/1.1.1)
- Terminal 2V → Main breaker B1 input (=10/1.1.2)
- Terminal 3W → Main breaker B1 input (=10/1.1.3)

[Shows combined view of pages 1 and 3 with path highlighted]
```

## Implementation Approach

### Two-Phase Indexing Strategy

**Phase 1: Initial Load (One-time per PDF)**
```python
For each page in PDF:
  1. Convert to image
  2. Send to Claude Vision with prompt:
     "Extract all references (=XX/YY.Y.Z format),
      component labels, terminal IDs, cabinet numbers,
      and wire numbers from this schematic page"
  3. Parse response into structured index
  4. Store in registry.json
```

**Phase 2: Query Time (Fast)**
```python
When mechanic asks question:
  1. Search index for relevant pages (instant)
  2. If found in index → return quick answer
  3. If needs visual analysis → send images to Vision
  4. Combine index data + visual analysis = complete answer
```

## Index Structure

```json
{
  "sections": {
    "electrical": {
      "main_power.pdf": {
        "pages": {
          "1": {
            "references": ["=10/1.1.1", "=10/1.1.2", ...],
            "components": ["Breaker B1", "Breaker B2", ...],
            "cabinets": ["E11"],
            "terminals": [],
            "summary": "Main breaker panel with 12 breakers",
            "indexed_at": "2024-10-24T14:30:00"
          },
          "3": {
            "references": ["=10/102.0.3"],
            "components": ["Main transformer T1"],
            "terminals": ["1U", "2V", "3W"],
            "summary": "Main transformer primary connections",
            "indexed_at": "2024-10-24T14:30:15"
          }
        },
        "total_pages": 15,
        "indexed": true
      }
    }
  }
}
```

## Cost Analysis

### Initial Indexing Cost
- 100 pages @ $0.02/page = $2.00 (one-time)
- 500 pages @ $0.02/page = $10.00 (one-time)
- 1000 pages @ $0.02/page = $20.00 (one-time)

### Query Cost
- Most queries: $0 (use index only)
- Complex visual questions: $0.01-0.05 per query
- Monthly cost: $5-20 (mostly complex questions)

### Total First Month
- Index 500 pages: $10
- 200 queries: $5-10
- **Total: ~$15-20**

### Following Months
- No re-indexing needed (PDFs don't change)
- Only query costs: $5-20/month
- **Ongoing: ~$5-20/month**

## Advantages of This Approach

✅ **Best of Both Worlds**
- Fast text searches (using index)
- Visual understanding (when needed)
- Automatic indexing (no manual work)

✅ **Smart Cost Management**
- Pay once to index each PDF
- Most queries use free index lookup
- Vision only for complex questions

✅ **High Quality Index**
- Better than OCR (understands context)
- Gets references even on busy backgrounds
- Understands technical notation

✅ **No Manual Maintenance**
- Auto-indexes when loading
- Updates if PDFs change
- Self-documenting

## Example: Real Mechanic Workflow

```bash
# Day 1: Load all schematics (one-time setup)
TRACE> load section electrical *.pdf --index
🔍 Indexing 5 PDFs (73 pages)...
✓ Complete in 2m 30s
Cost: ~$1.50

TRACE> load section hydraulic *.pdf --index
🔍 Indexing 3 PDFs (45 pages)...
✓ Complete in 1m 30s
Cost: ~$0.90

# Day 2-365: Fast queries
TRACE> query slave 22
📊 Found in: electrical/main_power.pdf, Page 5
   Slave 22, Cabinet E11, 45 modules
Cost: $0 (index lookup)

TRACE> query HVC3
📊 Found in: electrical/control_circuits.pdf, Page 12
   HVC3 breaker signal → =61/4.1.3
Cost: $0 (index lookup)

# Complex question requires Vision
TRACE> ask "Trace the emergency stop circuit from button to relay"
🔍 Analyzing 3 pages...
[Detailed answer with visual path]
Cost: ~$0.06
```

## Should I Implement This?

This auto-indexing approach gives you:

1. **Automatic page indexing** when you load PDFs
2. **Fast text searches** using the index
3. **Visual analysis** for complex questions
4. **Low ongoing cost** (~$5-20/month after initial indexing)
5. **No manual maintenance** required

The implementation would add:
- Vision-based page analyzer
- Structured index builder
- Smart query router (index vs. vision)
- Section-based PDF storage
- `load section` command with `--index` flag
- `ask` command for complex visual questions
- `query` command for fast index searches

**Ready to proceed with implementation?**
