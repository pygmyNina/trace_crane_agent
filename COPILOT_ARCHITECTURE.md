# Crane Mechanic AI Copilot - System Architecture

## Vision: Save Mechanics Hours of Time

### The Problem:
Crane mechanics waste hours:
- 📄 Flipping through hundreds of schematic pages
- 🔍 Searching for specific components
- 🔌 Tracing wire paths manually
- 🤔 Figuring out what to check when troubleshooting
- 📝 Documenting component locations

### The Solution: AI Copilot
Ask natural language questions, get instant answers:
- "Where is Slave 23?" → Instant location + connections
- "Trace power from HVC3 to Slave 23" → Complete path visualization
- "Slave 23 not responding, what should I check?" → Diagnostic checklist
- "Show all components in Cabinet E11" → Complete list with locations

---

## System Architecture

### Phase 1: Training ✅ (COMPLETE)
**Purpose**: Teach Claude to read YOUR schematics

```
Training Data Collection:
├─ Ground Truth Labeling (YOU label schematics)
├─ Claude Vision Analysis
├─ Comparison & Metrics
└─ High-Quality Training Dataset

Output:
├─ 50+ labeled schematic pages
├─ Training examples with images
└─ Fine-tuning dataset
```

**Status**: ✅ Complete - Ready to use

---

### Phase 2: Knowledge Base Builder (NEXT)
**Purpose**: Extract and structure all schematic data

```
Component Extraction:
├─ Parse all training data
├─ Extract components, locations, specs
├─ Build component registry
└─ Create searchable index

Connection Mapping:
├─ Identify all wire connections
├─ Map component-to-component links
├─ Classify: power vs signal
└─ Build connection graph

Output:
├─ Component Database (SQLite)
├─ Connection Graph
└─ Searchable Index
```

**Components to Build**:
1. `database_builder.py` - Extract training data → database
2. `component_registry.py` - Manage component catalog
3. `connection_graph.py` - Wire connection mapping
4. `schematic_index.py` - Search indexing

---

### Phase 3: Wire Path Tracer
**Purpose**: Follow electrical paths component-to-component

```
Path Tracing:
├─ Power path tracing
├─ Signal path tracing
├─ Multi-hop connections
└─ Path visualization

Features:
├─ "Trace power from X to Y"
├─ "What feeds Slave 23?"
├─ "Show signal path for W1"
└─ "Find all components on Circuit 5"

Output:
├─ Visual path diagrams
├─ Component chain lists
└─ Connection details
```

**Components to Build**:
1. `wire_tracer.py` - Path finding algorithms
2. `path_visualizer.py` - Generate path diagrams
3. `circuit_analyzer.py` - Circuit-level analysis

---

### Phase 4: Search & Query Interface
**Purpose**: Fast component and connection lookup

```
Search Capabilities:
├─ Component search by name/type
├─ Location-based search
├─ Connection search
└─ Full-text search

Query Types:
├─ "Find Slave 23"
├─ "Show all HVC components"
├─ "What's in Cabinet E11?"
├─ "Components on page 61.5"
└─ "Search for IM151 modules"

Output:
├─ Instant search results
├─ Component details
└─ Related connections
```

**Components to Build**:
1. `search_engine.py` - Component search
2. `query_parser.py` - Natural language queries
3. `result_formatter.py` - Format search results

---

### Phase 5: Troubleshooting Copilot
**Purpose**: AI assistant for diagnostics

```
Troubleshooting Workflows:
├─ Symptom analysis
├─ Component dependency checking
├─ Diagnostic suggestions
└─ Check sequence generation

Copilot Features:
├─ "Slave 23 not responding" → Check power, check connections, verify modules
├─ "HVC3 tripped" → Related components, reset sequence, safety checks
├─ "No communication to Cabinet E11" → Bus trace, module check, cable test
└─ "Signal loss on W1" → Wire trace, connector check, component status

AI Capabilities:
├─ Understand symptoms
├─ Generate diagnostic steps
├─ Reference schematic data
└─ Provide context-aware help

Output:
├─ Step-by-step diagnostics
├─ Component check lists
└─ Related schematic references
```

**Components to Build**:
1. `troubleshooting_agent.py` - AI diagnostic assistant
2. `diagnostic_rules.py` - Troubleshooting logic
3. `symptom_analyzer.py` - Problem classification

---

### Phase 6: Interactive Copilot Interface
**Purpose**: Natural language chat interface

```
Chat Interface:
├─ Natural language questions
├─ Context-aware responses
├─ Multi-turn conversations
└─ Visual outputs

Example Conversation:

Mechanic: "Where is Slave 23?"
Copilot: "Slave 23 is located at =61/102.0.8 in Cabinet E11.
         It has 45 modules: 1 IM151, 1 PM, 40 DI, 3 RTD.
         Would you like to see its connections?"

Mechanic: "Yes, show power connections"
Copilot: "Power path to Slave 23:
         HVC3 → W1 → Terminal 5 → W2 → Slave 23 PM module

         [Diagram showing path]

         Do you need to troubleshoot something?"

Mechanic: "Slave 23 not responding"
Copilot: "Let's diagnose. Check in this order:
         1. Verify HVC3 is energized (red light on)
         2. Check W1 connection at HVC3 terminal 1
         3. Check W2 at Slave 23 input
         4. Verify PM module LED is green
         5. Check IM151 communication (green blink)

         Which step failed?"
```

**Components to Build**:
1. `copilot_interface.py` - Chat interface
2. `conversation_manager.py` - Context tracking
3. `response_generator.py` - AI response formatting
4. `visual_output.py` - Diagrams and illustrations

---

## Database Schema

### Components Table
```sql
CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT,  -- HVC, Slave, Cabinet, Module, etc.
    index_reference TEXT,  -- =61/102.0.8
    section INTEGER,
    sheet TEXT,
    column INTEGER,
    page_number INTEGER,
    cabinet TEXT,
    specifications JSON,
    notes TEXT
);
```

### Connections Table
```sql
CREATE TABLE connections (
    id INTEGER PRIMARY KEY,
    from_component_id INTEGER,
    to_component_id INTEGER,
    wire_label TEXT,
    connection_type TEXT,  -- power, signal, ground
    from_terminal TEXT,
    to_terminal TEXT,
    specifications TEXT,
    FOREIGN KEY (from_component_id) REFERENCES components(id),
    FOREIGN KEY (to_component_id) REFERENCES components(id)
);
```

### Wire Paths Table
```sql
CREATE TABLE wire_paths (
    id INTEGER PRIMARY KEY,
    wire_label TEXT,
    path_type TEXT,  -- power, signal
    components JSON,  -- Ordered list of components in path
    terminals JSON,
    page_references TEXT
);
```

### Schematic Pages Table
```sql
CREATE TABLE schematic_pages (
    id INTEGER PRIMARY KEY,
    pdf_filename TEXT,
    page_number INTEGER,
    section INTEGER,
    sheet TEXT,
    components_count INTEGER,
    indexed_at TIMESTAMP
);
```

---

## Technology Stack

### Backend:
- **Python 3.8+** - Core language
- **SQLite** - Component database
- **NetworkX** - Graph database for connections
- **Anthropic Claude** - AI copilot
- **FastAPI** (optional) - API for web interface

### Frontend (Future):
- **Rich** - Terminal UI (current)
- **Web UI** (optional) - Browser interface
- **Mobile** (future) - Field use

---

## Data Flow

### Training → Database → Copilot

```
1. Training Phase (Current):
   Ground Truth Labels → Claude Analysis → Training Dataset

2. Database Building:
   Training Dataset → Parser → Component DB + Connection Graph

3. Indexing:
   Components + Connections → Search Index

4. Copilot Ready:
   Mechanic Question → AI + Database → Answer + Context
```

---

## Usage Examples

### Scenario 1: Component Lookup
```bash
$ python copilot.py

> Where is Slave 23?

Slave 23 Location:
├─ Index: =61/102.0.8
├─ Cabinet: E11
├─ Page: Section 61, Sheet 102.0
└─ Modules: 45 total (1 IM151, 1 PM, 40 DI, 3 RTD)

> Show connections

Slave 23 Connections:
Power:
├─ HVC3 → W1 → Slave 23 PM
└─ Voltage: 24VDC

Signal:
├─ Main Controller → W5 → Slave 23 IM151 (Profibus)
└─ Bus Address: 23

> Open schematic page

Opening: section_61/sheet_102.0.pdf (page highlighted)
```

### Scenario 2: Troubleshooting
```bash
> Slave 23 not responding to commands

Troubleshooting Slave 23:

Primary Checks:
1. ✓ Power Supply
   - Check HVC3 is energized
   - Verify 24VDC at Slave 23 PM module
   - Expected: Green LED on PM

2. ✓ Communication
   - Check Profibus connection at IM151
   - Verify green blink on IM151 LED
   - Check bus termination

3. ✓ Physical Connections
   - W1: HVC3 terminal 1 → Slave 23 PM input
   - W5: Main Controller → Slave 23 IM151

Diagnostic Sequence:
Step 1: Measure voltage at HVC3 terminal 1
Step 2: Check W1 continuity
Step 3: Verify 24VDC at Slave 23 PM input
Step 4: Check IM151 LED status
Step 5: Verify bus address = 23

Related Components:
├─ HVC3 (power source)
├─ Main Controller (signal source)
└─ Cabinet E11 bus terminator

> Voltage OK, IM151 not blinking

IM151 Not Communicating:

Likely Causes:
1. Profibus cable W5 issue
2. Wrong bus address
3. IM151 module fault
4. Main Controller not sending

Next Steps:
1. Check W5 connection at both ends
2. Verify bus address switch = 23
3. Try replacing IM151 module
4. Check Main Controller diagnostics

Would you like schematic references for any of these?
```

### Scenario 3: Wire Tracing
```bash
> Trace power from HVC3 to all slaves

Power Distribution from HVC3:

HVC3 → Slave 22:
├─ W1 → Terminal 5 → W6 → Slave 22 PM
└─ Status: ✓ Connected

HVC3 → Slave 23:
├─ W1 → Terminal 5 → W2 → Slave 23 PM
└─ Status: ✓ Connected

HVC3 → Slave 60:
├─ W1 → Terminal 5 → W8 → Slave 60 PM
└─ Status: ✓ Connected

[Visual diagram of power tree]

Total devices powered by HVC3: 6
Circuit protection: 10A breaker at HVC3

> Show diagram

[ASCII or graphical diagram of power tree]
```

---

## Development Roadmap

### Sprint 1: Database Builder (Week 1)
- [ ] Parse training data
- [ ] Extract components to database
- [ ] Map connections
- [ ] Build search index

### Sprint 2: Search & Query (Week 2)
- [ ] Component search
- [ ] Connection lookup
- [ ] Natural language query parsing
- [ ] Result formatting

### Sprint 3: Wire Tracer (Week 3)
- [ ] Path finding algorithms
- [ ] Power vs signal classification
- [ ] Visual path output
- [ ] Multi-hop tracing

### Sprint 4: Copilot AI (Week 4)
- [ ] Troubleshooting logic
- [ ] AI integration
- [ ] Diagnostic suggestions
- [ ] Context awareness

### Sprint 5: Interface (Week 5)
- [ ] Interactive chat
- [ ] Visual outputs
- [ ] Conversation management
- [ ] Polish and testing

---

## Success Metrics

### Time Savings:
- **Component lookup**: 5 min → 10 sec (30x faster)
- **Wire tracing**: 15 min → 30 sec (30x faster)
- **Troubleshooting start**: 20 min → 2 min (10x faster)

### Accuracy:
- Component identification: 95%+
- Connection mapping: 90%+
- Path tracing: 95%+

### User Experience:
- Natural language queries
- Instant responses
- Context-aware help
- Visual diagrams

---

## Next Steps

**Immediate**: Build Database Builder (Phase 2)

**Then**: Wire Tracer, Search, Copilot AI

**Goal**: Working copilot for crane mechanics in 4-5 weeks

---

**This is what we're building!** 🚀
