# Agent Training - Quick Start

## Train Claude to Read YOUR Crane Schematics in 5 Minutes

### What is This?

This system **trains Claude AI** to accurately read and interpret YOUR crane electrical schematics through Vision AI and your corrections.

### Quick Setup

```bash
# 1. Make sure you have your API key set up
# (Already done if you completed the main setup)

# 2. Your PDFs should already be in place
ls data/pdfs/section_61/

# 3. Start training immediately
python3 scripts/train_agent.py --section 61
```

### What Happens:

1. **Claude analyzes your schematic** (using Vision AI to see the image)
2. **Claude identifies**: components, index references, wire connections
3. **You review** Claude's analysis
4. **You correct** any mistakes
5. **System learns** from your corrections
6. **Repeat** for more schematics

### Example Training Session:

```
╔═══════════ Claude's Analysis ═══════════╗
║ COMPONENTS:                             ║
║ - HVC3                                  ║
║ - Slave 22                              ║
║                                         ║
║ INDEX REFERENCES:                       ║
║ - =61/102.0.8                           ║
╚═════════════════════════════════════════╝

Is Claude's analysis completely correct? [y/N]: n

Review/correct COMPONENTS? [Y/n]: y

  Claude found: HVC3
  Is this correct? [correct/wrong/modify/skip]: correct
  ✓ Confirmed

  Claude found: Slave 22
  Is this correct? [correct/wrong/modify/skip]: modify
  Enter corrected version: Slave 23
  ✓ Updated to: Slave 23

  Did Claude miss any Components? [y/N]: y
  Add item: Cabinet E11
  ✓ Added: Cabinet E11

...

✓ Training data saved!
```

### After Training:

Your corrections build:
- ✅ **Training dataset** for fine-tuning
- ✅ **Knowledge base** of patterns
- ✅ **Improved prompts** with examples

### View Progress:

```bash
python3 scripts/train_agent.py --stats
```

### Export for Fine-Tuning:

After 50+ examples:

```bash
python3 scripts/train_agent.py --export
```

Submit the exported file to Anthropic for a custom model!

### Full Documentation:

See [AGENT_TRAINING_GUIDE.md](AGENT_TRAINING_GUIDE.md) for complete details.

### Commands:

```bash
# Train on section 61
python3 scripts/train_agent.py --section 61

# Train on single PDF
python3 scripts/train_agent.py --pdf data/pdfs/section_61/61_1.pdf

# Train on specific pages
python3 scripts/train_agent.py --pdf data/pdfs/section_61/61_1.pdf --pages 0,1

# View statistics
python3 scripts/train_agent.py --stats

# Export for fine-tuning
python3 scripts/train_agent.py --export
```

---

**Start training Claude on your schematics now:**

```bash
python3 scripts/train_agent.py --section 61
```
