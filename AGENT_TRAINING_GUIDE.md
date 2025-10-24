# Agent Training Guide

## Training Claude to Read YOUR Crane Schematics

This guide explains how to train Claude AI to accurately read and interpret your specific crane electrical schematics.

## 🎯 What is Agent Training?

Unlike the human training system (where YOU learn from Claude), **Agent Training teaches CLAUDE to read YOUR schematics**.

### The Process:

```
1. Claude analyzes your schematic (using Vision AI)
   ↓
2. You review Claude's analysis
   ↓
3. You correct any mistakes
   ↓
4. System learns from corrections
   ↓
5. Builds training data for improvement
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API key with vision access
- Your crane schematic PDFs (images)

### Step 1: Prepare Your PDFs

```bash
# Copy your section 61 PDFs
cp /path/to/your/pdfs/*.pdf data/pdfs/section_61/
```

### Step 2: Start Training

```bash
# Train on entire section 61
python3 scripts/train_agent.py --section 61

# Or train on a single PDF
python3 scripts/train_agent.py --pdf data/pdfs/section_61/61_1.pdf

# Or train on specific pages
python3 scripts/train_agent.py --pdf data/pdfs/section_61/61_1.pdf --pages 0,1,2
```

## 📖 Training Workflow

### What Happens During Training:

#### 1. **Claude Analyzes the Schematic**

Claude Vision looks at your schematic image and identifies:
- **Components**: HVC, Slaves, Cabinets, Modules, etc.
- **Index References**: =XX/YY.Y.Z notations
- **Wire Connections**: Wire labels and connection points
- **Labels**: Terminal numbers, specifications, notes

#### 2. **You Review the Analysis**

The system shows you Claude's findings:

```
╔═══════════════ Claude's Analysis ════════════════╗
║ COMPONENTS                                       ║
║ - HVC3 (High Voltage Contactor)                  ║
║ - Slave 22 in Cabinet E11                       ║
║ - IM151 module                                   ║
║                                                  ║
║ INDEX REFERENCES                                  ║
║ - =61/102.0.8                                    ║
║ - =61/103.0.7                                    ║
║                                                  ║
║ WIRE CONNECTIONS                                  ║
║ - W1 connects to W2 at terminal 5                ║
╚══════════════════════════════════════════════════╝
```

#### 3. **You Provide Corrections**

For each category, you can:

- ✅ **Confirm** - "Claude got this right"
- ❌ **Remove** - "Claude identified this incorrectly"
- ✏️ **Modify** - "Close, but should be..."
- ➕ **Add** - "Claude missed this"

**Example Interaction:**

```
Claude found: HVC3
Is this correct? [correct/wrong/modify/skip]: correct
✓ Confirmed

Claude found: Slave 22
Is this correct? [correct/wrong/modify/skip]: modify
Enter corrected version: Slave 23
✓ Updated to: Slave 23

Did Claude miss any components? [y/N]: y
Add item (or press Enter to finish): Cabinet E11
✓ Added: Cabinet E11
```

#### 4. **System Learns**

Your corrections are used to:

✅ Build a **training dataset** for fine-tuning
✅ Update the **knowledge base** with patterns
✅ Track **common mistakes**
✅ Generate **improved prompts** with examples

## 📊 Training Data Outputs

### 1. Training Examples (`data/training_data/training_examples.jsonl`)

Records every correction with:
- Original analysis
- Your corrections
- Ground truth
- Schematic image

### 2. Learned Knowledge (`data/training_data/learned_knowledge.json`)

Builds up knowledge including:
- Common mistakes to avoid
- Validated correct examples
- Component patterns
- Index reference patterns

### 3. Fine-tuning Dataset (`data/training_data/finetuning_dataset.jsonl`)

Ready-to-submit format for Anthropic fine-tuning:
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "source": {...}},
        {"type": "text", "text": "Analyze this schematic"}
      ]
    },
    {
      "role": "assistant",
      "content": "Correct analysis based on your corrections"
    }
  ]
}
```

## 🎓 Training Strategies

### Start Small

```bash
# Train on just one page first
python3 scripts/train_agent.py --pdf data/pdfs/section_61/61_1.pdf --pages 0

# Get comfortable with the correction process
# Then expand to more pages
```

### Train by Section

```bash
# Train on all of section 61
python3 scripts/train_agent.py --section 61

# This goes through each PDF sequentially
# You can skip PDFs if needed
```

### Focus on Problem Areas

If Claude struggles with specific things:

1. Train on examples with those components
2. Provide detailed corrections
3. Add explanatory feedback
4. System will learn the patterns

### Regular Review

```bash
# Check training progress
python3 scripts/train_agent.py --stats

# Shows:
# - Total training examples
# - Common mistakes tracked
# - Validation accuracy
```

## 📈 Improving Over Time

### Progressive Learning

The system improves with each correction:

**After 5-10 corrections:**
- Prompts include common mistake warnings
- Few-shot examples added

**After 20-30 corrections:**
- Strong pattern recognition
- Reduced false positives
- Better component identification

**After 50+ corrections:**
- Ready for fine-tuning submission
- Highly accurate on your schematics
- Specialized knowledge base

### Export for Fine-Tuning

Once you have enough examples (50+ recommended):

```bash
# Export training data
python3 scripts/train_agent.py --export

# File created: data/training_data/finetuning_ready.jsonl
```

Submit this to Anthropic for fine-tuning to create a custom model that knows YOUR schematics.

## 💡 Tips for Effective Training

### 1. Be Consistent

Use the same terminology every time:
- "Slave 22" not "slave 22" or "SLAVE 22"
- "=61/102.0.8" not "61/102.0.8" or "= 61/102.0.8"

### 2. Be Specific

When adding missing items:
```
Good: "HVC3 at top left, near =61/102.0.8"
Bad: "HVC3"
```

### 3. Explain Mistakes

Use the feedback field to explain why something was wrong:
```
"Slave number misread - the '3' looks like an '8' in this scan"
"Index reference partially obscured by wire label"
```

### 4. Validate Incrementally

Don't train on 100 pages at once. Do batches of 5-10, then:
- Review stats
- Check common mistakes
- Adjust approach if needed

### 5. Focus on Quality

10 high-quality corrections > 50 rushed corrections

Take time to:
- Carefully review each item
- Add all missing components
- Provide detailed feedback

## 🔍 Monitoring Progress

### View Statistics

```bash
python3 scripts/train_agent.py --stats
```

Shows:
```
╔════════════ Training Statistics ════════════╗
║ Total Training Examples: 25                 ║
║ Validated Examples: 25                      ║
║ Common Mistakes Tracked: 15                 ║
║ Last Updated: 2025-10-24T10:30:00          ║
╚═════════════════════════════════════════════╝

Common Mistakes:
  • components: 'Slave 22' → 'Slave 23'
  • index_references: '=61/102.8' → '=61/102.0.8'
```

### Review Training Data

```bash
# View training examples
cat data/training_data/training_examples.jsonl | head -1 | python3 -m json.tool

# View learned knowledge
cat data/training_data/learned_knowledge.json | python3 -m json.tool
```

## 🎯 What Can the Trained Agent Do?

After sufficient training, Claude will be able to:

✅ Accurately identify components in YOUR schematics
✅ Read index references in your specific format
✅ Trace wire connections
✅ Understand your labeling conventions
✅ Recognize section-specific patterns
✅ Avoid common misidentification mistakes

## 📦 Integration with Existing System

The agent training system works alongside the human training system:

**Human Training** (`main.py`):
- YOU learn crane schematic reading
- Claude quizzes you
- Tracks your progress

**Agent Training** (`scripts/train_agent.py`):
- CLAUDE learns your schematics
- You correct Claude
- Builds training dataset

Use both!
1. Train the agent on your schematics
2. Use improved prompts for analysis
3. Train yourself to verify agent's work

## 🚀 Next Steps

### Immediate Actions:

1. **Train on first PDF**:
   ```bash
   python3 scripts/train_agent.py --pdf data/pdfs/section_61/61_1.pdf
   ```

2. **Review first results**:
   ```bash
   python3 scripts/train_agent.py --stats
   ```

3. **Continue training**:
   ```bash
   python3 scripts/train_agent.py --section 61
   ```

### Long-term Goals:

1. **Collect 50+ training examples** from various pages
2. **Review and refine** learned knowledge
3. **Export for fine-tuning** when ready
4. **Submit to Anthropic** for custom model

## ❓ Troubleshooting

### "Analysis taking too long"

Large/high-resolution PDFs may take 10-30 seconds to analyze. This is normal.

### "Claude missing obvious components"

Provide detailed corrections and feedback. After 10-20 examples, accuracy improves significantly.

### "Same mistakes repeatedly"

Check `learned_knowledge.json` - system should be tracking these. If not, ensure corrections are being saved properly.

### "Want to start over"

```bash
# Backup existing data
mv data/training_data data/training_data_backup

# Fresh start
mkdir data/training_data
```

## 📚 Related Documentation

- [README.md](README.md) - Main system documentation
- [PDF_SETUP_GUIDE.md](PDF_SETUP_GUIDE.md) - PDF library setup
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide

---

**Ready to train Claude on your schematics?**

```bash
python3 scripts/train_agent.py --section 61
```

Let's make Claude an expert on YOUR crane schematics! 🎉
