# Database Builder Guide - Phase 2

## Building a Searchable Component Database

Phase 2 of the Crane Mechanic Copilot system extracts your training data into a **searchable database** that powers the troubleshooting copilot.

## 🎯 What Does It Do?

The Database Builder:
1. **Reads your training data** (ground truth labels and training examples)
2. **Extracts components** with locations, types, and specifications
3. **Builds connection graph** showing how components wire together
4. **Creates searchable index** for fast lookups
5. **Enables copilot features** like wire tracing and troubleshooting

## 🚀 Quick Start

### Build Database from Training Data

```bash
# Build database from all training sources
python3 scripts/build_database.py --build

# Build and show what's in it
python3 scripts/build_database.py --build --show

# Build and test search functionality
python3 scripts/build_database.py --build --test

# Or just run with no args (does all of the above)
python3 scripts/build_database.py
```

### View Database Contents

```bash
# Show statistics and contents
python3 scripts/build_database.py --show
```

### Rebuild from Scratch

```bash
# Delete existing database and rebuild
python3 scripts/build_database.py --rebuild
```

## 📊 What Gets Extracted?

### 1. Components

From ground truth labels like:
```
"Slave 23 in Cabinet E11"
"HVC3 at =61/102.0.8"
"Slave 23: 45 modules, IM151-1, PM, DI40, RTD3"
```

The builder extracts:
- **Name**: "Slave 23", "HVC3"
- **Type**: "Slave", "HVC"
- **Location**: Index reference (=61/102.0.8)
- **Cabinet**: "Cabinet E11"
- **Specifications**: Module counts, model numbers
- **Page Reference**: Which PDF page it's on

### 2. Wire Connections

From connection labels like:
```
"W1 connects to W2 at terminal 5"
"Power from HVC3 pin 1 to Slave 23 PM input"
"Signal wire W105 from sensor to DI module terminal 3"
```

The builder extracts:
- **From Component** → **To Component**
- **Wire Label**: W1, W105, etc.
- **Connection Type**: power, signal, ground
- **Terminals**: Pin numbers and labels
- **Direction**: Incoming vs outgoing

### 3. Schematic Pages

Tracks which pages have been indexed:
- PDF filename
- Page number
- Section (e.g., 61)
- Components on that page
- Ground truth source file

## 🔍 Database Schema

The database has 5 main tables:

### `components`
```
- id (auto-increment primary key)
- name (e.g., "Slave 23")
- type (e.g., "Slave", "HVC")
- index_reference (e.g., "=61/102.0.8")
- section, sheet, column (parsed from index)
- cabinet (e.g., "Cabinet E11")
- specifications (JSON - module counts, etc.)
- pdf_filename, page_number
```

### `connections`
```
- id
- from_component_id → to_component_id
- wire_label (e.g., "W1")
- connection_type (power/signal/ground)
- from_terminal, to_terminal
- specifications, notes
```

### `wire_paths`
```
- id
- wire_label
- path_type (power/signal)
- components (full path as JSON)
- terminals
- page_references
```

### `schematic_pages`
```
- id
- pdf_filename, page_number
- section, sheet
- components_count
- ground_truth_file (source)
```

### `training_sources`
```
- id
- source_file
- source_type (ground_truth / training_example)
- components_added, connections_added
- processed_at
```

## 📈 Example Output

When you build the database, you'll see:

```
Building Searchable Component Database
============================================================

Processing ground truth files...
  ✓ 61_1_page_0.json: 8 components, 3 connections
  ✓ 61_1_page_1.json: 12 components, 5 connections
  ✓ 61_2_page_0.json: 6 components, 2 connections

✓ Processed 3 ground truth files

Processing training examples from data/training_data/training_examples.jsonl...
✓ Processed 15 training examples

============================================================
Database Build Statistics
============================================================

Data Sources Processed: 18
Pages Indexed: 18
Components Added: 156
Connections Added: 45

Database Totals:
  Total Components: 156
  Component Types: 5
  Total Connections: 45
  Cabinets: 3
  Indexed Pages: 18

Components by Type:
  Slave: 82
  HVC: 35
  Module: 24
  Cabinet: 12
  IM151: 3
```

## 🔎 Search Examples

Once built, you can search the database:

### Search by Component Name

```python
from database_schema import SchematicDatabase

with SchematicDatabase() as db:
    # Find all slaves
    results = db.search_component("Slave", search_type="name")
    for comp in results:
        print(f"{comp['name']} at {comp['index_reference']}")
```

Output:
```
Slave 22 at =61/102.0.8
Slave 23 at =61/103.0.7
Slave 60 at =61/104.0.6
...
```

### Search by Component Type

```python
# Find all HVC components
results = db.search_component("HVC", search_type="type")
```

### Search by Cabinet

```python
# Find everything in Cabinet E11
results = db.search_component("E11", search_type="cabinet")
```

### Get Component Connections

```python
# Find all connections for Slave 23
connections = db.get_component_connections("Slave 23")

print("Outgoing connections:")
for conn in connections['outgoing']:
    print(f"  → {conn['to_component_name']} via {conn['wire_label']}")

print("Incoming connections:")
for conn in connections['incoming']:
    print(f"  ← {conn['from_component_name']} via {conn['wire_label']}")
```

## 🛠️ How Parsing Works

### Component String Parsing

The builder intelligently parses various component formats:

**Simple name:**
```
"HVC3" → {name: "HVC3", type: "HVC"}
```

**With cabinet:**
```
"Slave 23 in Cabinet E11"
→ {name: "Slave 23", type: "Slave", cabinet: "Cabinet E11"}
```

**With index reference:**
```
"HVC3 at =61/102.0.8"
→ {name: "HVC3", type: "HVC", index_reference: "=61/102.0.8",
   section: 61, sheet: "102.0", column: 8}
```

**With specifications:**
```
"Slave 23: 45 modules, IM151-1, PM, DI40, RTD3"
→ {name: "Slave 23", type: "Slave",
   specifications: {modules: 45, "IM151-1": 1, PM: 1, DI40: 1, RTD3: 1}}
```

### Connection String Parsing

**Simple connection:**
```
"HVC3 to Slave 23"
→ {from_component: "HVC3", to_component: "Slave 23"}
```

**With wire label:**
```
"W1 from HVC3 to Slave 23"
→ {from_component: "HVC3", to_component: "Slave 23", wire_label: "W1"}
```

**With connection type:**
```
"Power from HVC3 pin 1 to Slave 23 PM input"
→ {from_component: "HVC3", to_component: "Slave 23",
   connection_type: "power", from_terminal: "1", to_terminal: "PM input"}
```

## 💡 Data Quality Tips

### 1. Consistent Component Names

Use the same name format in all labels:
```
✅ "Slave 23" (always)
❌ "slave 23", "SLAVE 23", "Slave23" (inconsistent)
```

### 2. Full Component Details

Include as much info as possible:
```
✅ "Slave 23 in Cabinet E11: 45 modules, IM151-1, PM, DI40, RTD3"
❌ "Slave 23"
```

### 3. Explicit Connections

Be specific about connections:
```
✅ "Power from HVC3 terminal 1 to Slave 23 PM input via W105"
❌ "HVC3 connected to Slave 23"
```

### 4. Index References

Always use proper format:
```
✅ "=61/102.0.8" or "=61/102.8" (shorthand)
❌ "61/102.0.8" (missing =) or "= 61/102.0.8" (space)
```

## 🔄 Workflow Integration

### Step 1: Label Schematics (Phase 1)

```bash
# Create ground truth labels
python3 scripts/train_agent_with_ground_truth.py --pdf data/pdfs/section_61/61_1.pdf
```

This creates: `data/ground_truth/61_1_page_0.json`

### Step 2: Build Database (Phase 2)

```bash
# Extract into searchable database
python3 scripts/build_database.py --build
```

This populates: `data/copilot/schematic_knowledge.db`

### Step 3: Use for Copilot (Phases 3-6)

The database now powers:
- **Wire Path Tracer** (Phase 3)
- **Search Interface** (Phase 4)
- **Troubleshooting AI** (Phase 5)
- **Chat Copilot** (Phase 6)

## 📊 Monitoring Database Growth

As you label more schematics, the database grows:

```bash
# After labeling 5 pages
python3 scripts/build_database.py --show
# → 45 components, 12 connections

# After labeling 20 pages
python3 scripts/build_database.py --rebuild
# → 180 components, 65 connections

# After labeling 100 pages
python3 scripts/build_database.py --rebuild
# → 850 components, 320 connections
```

## 🎯 What Can You Do with the Database?

### Current Capabilities (Phase 2):

✅ **Component Search**: Find any component by name, type, cabinet, or index
✅ **Connection Lookup**: See what connects to what
✅ **Page Navigation**: Find which page a component is on
✅ **Cabinet Inventory**: List all components in a cabinet
✅ **Type Filtering**: Get all slaves, all HVCs, etc.

### Upcoming Capabilities:

⏳ **Wire Tracing** (Phase 3): Follow power/signal paths end-to-end
⏳ **Natural Language Search** (Phase 4): "Find the slave in cabinet E11"
⏳ **Troubleshooting** (Phase 5): "Why isn't HVC3 getting power?"
⏳ **AI Chat** (Phase 6): Conversational interface for mechanics

## 🐛 Troubleshooting

### "No ground truth files found"

Make sure you've labeled some schematics first:
```bash
python3 scripts/train_agent_with_ground_truth.py --pdf data/pdfs/section_61/61_1.pdf
```

### "Could not parse component"

Check your component string format. Examples:
```
✅ "Slave 23 in Cabinet E11"
✅ "HVC3 at =61/102.0.8"
❌ "The slave 23 component" (too wordy)
```

### "Component not found" when adding connection

Make sure both components exist in the database first. The builder processes components before connections.

### Want to start over

```bash
# Rebuild from scratch
python3 scripts/build_database.py --rebuild
```

## 📚 Related Documentation

- [COPILOT_ARCHITECTURE.md](COPILOT_ARCHITECTURE.md) - Overall system design
- [GROUND_TRUTH_TRAINING.md](GROUND_TRUTH_TRAINING.md) - Phase 1: Creating labels
- [AGENT_TRAINING_GUIDE.md](AGENT_TRAINING_GUIDE.md) - Alternative training method

---

## ✅ Phase 2 Complete!

Your training data is now in a **searchable database** ready for:
- Wire path tracing
- Troubleshooting assistance
- AI copilot features

**Next**: Phase 3 - Wire Path Tracer

```bash
# Build the database
python3 scripts/build_database.py

# Ready for Phase 3!
```
