# Multi-Computer Sync Guide for TRACE

Guide for using TRACE across multiple computers with synchronized knowledge.

## Overview

TRACE stores knowledge in local JSON files that can be synced via git. This allows multiple users/computers to share training data and schematic indexes.

## What Gets Synced

✅ **Synced via Git:**
- `trace_knowledge.json` - Manual training data (slaves, connections, sequences)
- `schematic_registry.json` - PDF indexes (Vision AI extracted data)
- Code and scripts

❌ **NOT Synced (Local Only):**
- `.env` - Your API key (each computer has its own)
- `.trace_cache/` - Cached images (regenerated automatically)
- `schematics/**/*.pdf` - Original PDFs (too large, copy manually)

## Setup: Two-Computer Workflow

### Computer A - Primary Training Station

**Initial Setup:**
```bash
# 1. Clone repository
git clone https://github.com/pygmyNina/trace_crane_agent2.git
cd trace_crane_agent2

# 2. Switch to Vision branch
git checkout claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# 3. Install dependencies
pip3 install -r requirements.txt
brew install poppler  # Mac

# 4. Configure API key
python3 configure_api_key.py

# 5. Copy PDFs to schematics/
mkdir -p schematics/electrical
cp ~/Desktop/trace_pdfs/*.pdf schematics/electrical/
```

**Daily Workflow:**
```bash
# 1. Pull latest knowledge from other computer
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# 2. Use TRACE
python3 trace_cli.py
# Train, query, analyze...

# 3. Commit and push knowledge updates
git add trace_knowledge.json schematic_registry.json
git commit -m "Update TRACE knowledge: [describe what you added]"
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### Computer B - Secondary Station

**Initial Setup:**
```bash
# 1. Clone repository
git clone https://github.com/pygmyNina/trace_crane_agent2.git
cd trace_crane_agent2

# 2. Switch to Vision branch
git checkout claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# 3. Install dependencies
pip3 install -r requirements.txt
brew install poppler  # Mac

# 4. Configure API key (use your own key)
python3 configure_api_key.py

# 5. Copy same PDFs to schematics/
mkdir -p schematics/electrical
cp ~/Desktop/trace_pdfs/*.pdf schematics/electrical/

# 6. Pull existing knowledge from Computer A
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

**Daily Workflow:**
```bash
# 1. Pull latest knowledge
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# 2. Use TRACE
python3 trace_cli.py

# 3. If you add knowledge, commit and push
git add trace_knowledge.json schematic_registry.json
git commit -m "Update TRACE knowledge: [your changes]"
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

## Sync Workflow Examples

### Example 1: Training on Computer A

```bash
# Computer A
python3 trace_cli.py
TRACE> train
Training> Schematic 10 page 2 shows control circuits
Training> Emergency stop button is at =10/20.1.1
Training> done
TRACE> quit

# Commit the training
git add trace_knowledge.json
git commit -m "Trained: schematic 10 control circuits and e-stop"
git push
```

```bash
# Computer B (later)
git pull  # Gets the training data

python3 trace_cli.py
TRACE> query emergency stop
# Sees the training from Computer A! ✓
```

### Example 2: Indexing PDF on Computer A

```bash
# Computer A
python3 manual_index.py "schematic_61.pdf" electrical 76
# Vision AI indexes all 76 pages

# Commit the index
git add schematic_registry.json
git commit -m "Indexed: schematic 61 (76 pages)"
git push
```

```bash
# Computer B (later)
# Copy schematic_61.pdf to schematics/electrical/
cp ~/Desktop/schematic_61.pdf schematics/electrical/

git pull  # Gets the index data

python3 trace_cli.py
TRACE> query =61
# Can search schematic 61 without re-indexing! ✓
```

### Example 3: Both Computers Training

```bash
# Computer A (morning)
TRACE> train
Training> Slave 60 powers the hoist motors
Training> done

git add trace_knowledge.json
git commit -m "Added Slave 60 purpose"
git push
```

```bash
# Computer B (afternoon)
git pull  # Gets Slave 60 info

TRACE> train
Training> Slave 61 powers the trolley drive
Training> done

git add trace_knowledge.json
git commit -m "Added Slave 61 purpose"
git push
```

```bash
# Computer A (evening)
git pull  # Gets Slave 61 info

TRACE> show slaves
# Sees both Slave 60 AND Slave 61! ✓
```

## Important Notes

### PDFs Must Be on Each Computer

The PDF files themselves are NOT synced (too large). You must:
1. Copy PDFs to each computer manually
2. Put them in the SAME location: `schematics/electrical/`
3. Use the SAME filenames

**Why?** The registry stores paths like `schematics/electrical/10.pdf`. If the PDF isn't there, TRACE can still search the index but can't re-analyze pages.

### API Keys Are Separate

Each computer needs its own `.env` file with its own API key:
```bash
# On each computer
python3 configure_api_key.py
```

The `.env` file is in `.gitignore` so API keys never get committed.

### Cache Is Local

The `.trace_cache/` directory stores converted images. Each computer generates its own cache. Don't sync this directory - it's large and machine-specific.

### Merge Conflicts

If both computers edit knowledge at the same time, you may get merge conflicts:

```bash
git pull
# CONFLICT in trace_knowledge.json

# Resolve manually or:
git checkout --theirs trace_knowledge.json  # Use remote version
# or
git checkout --ours trace_knowledge.json    # Use local version

git add trace_knowledge.json
git commit -m "Resolved merge conflict"
```

**Best Practice:** Coordinate who's training when, or pull before every session.

## Quick Reference

### Before Each TRACE Session
```bash
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
python3 trace_cli.py
```

### After Training or Indexing
```bash
git add trace_knowledge.json schematic_registry.json
git commit -m "Update: [what you added]"
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### Check Sync Status
```bash
# See what's changed
git status

# See what's different from remote
git diff origin/claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# View commit history
git log --oneline -10
```

## Troubleshooting

### "Your branch is behind"
```bash
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### "Your branch is ahead"
```bash
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### "PDF not found" error in TRACE
Copy the PDF to `schematics/electrical/` on this computer.

### Knowledge not syncing
Make sure you committed AND pushed:
```bash
git add trace_knowledge.json schematic_registry.json
git commit -m "Update knowledge"
git push
```

---

**Summary:** Pull before starting, push after training/indexing. Both computers stay in sync! 🔄
