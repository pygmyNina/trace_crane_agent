# TRACE Second Computer Setup - Quick Start

Complete setup instructions for getting TRACE running on your second computer with automatic knowledge and PDF sync.

## What Will Sync Automatically

✅ **Your training data** - Everything you taught TRACE
✅ **PDF indexes** - Vision AI extracted data (no re-indexing needed!)
✅ **Schematic PDFs** - Via Git LFS (automatic download)
✅ **All knowledge** - Slaves, connections, sequences, learnings

## Prerequisites

- Mac with macOS (or Linux/Windows with adjustments)
- Your Anthropic API key from console.anthropic.com
- GitHub account access (pygmyNina)

---

## Setup Steps (30 Minutes)

### Step 1: Install Required Software

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Git LFS
brew install git-lfs

# Install Poppler (for PDF conversion)
brew install poppler

# Verify installations
git --version
git lfs version
python3 --version
```

### Step 2: Clone the Repository

```bash
# Navigate to where you want TRACE
cd ~/Documents

# Clone the repository
git clone https://github.com/pygmyNina/trace_crane_agent2.git

# Navigate into it
cd trace_crane_agent2

# Switch to the correct branch
git checkout claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### Step 3: Initialize Git LFS

```bash
# Initialize Git LFS
git lfs install

# Verify LFS is tracking PDFs
cat .gitattributes
# Should show: schematics/**/*.pdf filter=lfs diff=lfs merge=lfs -text

# Pull PDFs from LFS (automatic download!)
git lfs pull

# Verify PDFs downloaded
ls -lh schematics/electrical/
# Should see: 10.pdf (802 KB) and 61.pdf (14.8 MB)
```

### Step 4: Install Python Dependencies

```bash
# Install Python packages
pip3 install -r requirements.txt

# Verify installations
python3 -c "import anthropic; print('✓ anthropic installed')"
python3 -c "from pdf2image import convert_from_path; print('✓ pdf2image installed')"
```

### Step 5: Configure Your API Key

```bash
# Run the interactive setup
python3 configure_api_key.py
```

When prompted:
1. Paste your Anthropic API key
2. Script will test the connection
3. API key saved to `.env` file

**Note:** Each computer has its own API key in `.env` (not synced via git)

### Step 6: Verify Everything Works

```bash
# Run tests
python3 test_vision_system.py
```

Should show:
```
✓ All tests passed! System is ready.
```

### Step 7: Launch TRACE

```bash
# Start TRACE
python3 trace_cli.py
```

Should show:
```
============================================================
  TRACE - Crane Schematic Assistant & Copilot
  Version 0.2.0 - Vision Enabled
============================================================

✓ Vision API: Ready
```

### Step 8: Verify Your Data Is There!

```bash
TRACE> summary
# Should show October 23 training data

TRACE> section electrical
# Should show: 10.pdf (3 pages) and 61.pdf (76 pages)
# Should show: [✓ Indexed] if Computer 1 indexed them

TRACE> query slave 22
# Should find Slave 22 data from Computer 1!

TRACE> show slaves
# Shows all slaves trained on Computer 1
```

**Everything from Computer 1 is automatically here!** 🎉

---

## Daily Workflow on Computer 2

### Before Using TRACE

```bash
cd ~/Documents/trace_crane_agent2

# Pull latest knowledge and training
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### Use TRACE

```bash
python3 trace_cli.py

# Train, query, analyze as normal
TRACE> train
Training> [your training]
Training> done

TRACE> quit
```

### After Training (Share with Computer 1)

```bash
# Commit your training
git add trace_knowledge.json schematic_registry.json
git commit -m "Trained: [what you added]"

# Push to share with Computer 1
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

---

## What Each Computer Needs

### Computer 1 (Already Set Up) ✅
- Has repository cloned
- Has API key configured
- PDFs in Git LFS
- Knowledge trained

### Computer 2 (Setting Up Now)
- Clone repository → Gets code
- Git LFS pull → Gets PDFs automatically
- Configure API key → Your own key
- Pull → Gets all knowledge from Computer 1

---

## Troubleshooting

### "PDFs not found" after cloning

```bash
# Pull PDFs from LFS
git lfs pull

# Verify
ls schematics/electrical/
```

### "Vision API not configured"

```bash
# Run configuration
python3 configure_api_key.py
```

### "Knowledge not syncing"

```bash
# Pull latest
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# Check if knowledge files updated
ls -l trace_knowledge.json schematic_registry.json
```

### PDFs are tiny (few KB) instead of MB

These are LFS pointer files. Download them:
```bash
git lfs pull
```

---

## Verify Multi-Computer Sync Works

### On Computer 2 (After Setup)

```bash
python3 trace_cli.py
TRACE> query slave 22
```

**Should find Slave 22** (trained on Computer 1!)

```bash
TRACE> section electrical
```

**Should show both PDFs** with indexed status from Computer 1!

### Train Something New on Computer 2

```bash
TRACE> train
Training> Slave 61 powers the trolley drive
Training> done
TRACE> quit

git add trace_knowledge.json
git commit -m "Trained: Slave 61 purpose"
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

### On Computer 1 (Pull Computer 2's Training)

```bash
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

python3 trace_cli.py
TRACE> query slave 61
# Should see "Slave 61 powers the trolley drive" ✅
```

**It worked! Knowledge syncs both ways!** 🎉

---

## Quick Reference

### First Time Setup
```bash
brew install git-lfs poppler
git clone https://github.com/pygmyNina/trace_crane_agent2.git
cd trace_crane_agent2
git checkout claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
git lfs install
git lfs pull
pip3 install -r requirements.txt
python3 configure_api_key.py
python3 test_vision_system.py
```

### Daily Use
```bash
git pull  # Get latest knowledge
python3 trace_cli.py  # Use TRACE
# After training:
git add trace_knowledge.json schematic_registry.json
git commit -m "Update knowledge"
git push
```

---

## What Makes This Work

1. **Git** - Syncs code and knowledge files
2. **Git LFS** - Syncs large PDF files via cloud
3. **JSON files** - Store knowledge in git-trackable format
4. **Your API key** - Each computer has its own (not shared)

---

## Need Help?

See these guides:
- `MULTI_COMPUTER_SYNC.md` - Full multi-computer guide
- `LOCAL_SETUP.md` - Detailed setup instructions
- `CLOUD_PDF_STORAGE.md` - How Git LFS works
- `GIT_LFS_SETUP.md` - Git LFS details

---

**You're Ready!** Set up Computer 2 with these steps and both computers will stay in sync automatically! 🚀
