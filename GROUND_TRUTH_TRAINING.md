# Ground Truth Training

## The Best Way to Train Claude on YOUR Schematics

Ground Truth Training means **YOU label everything first**, then Claude learns from YOUR labels.

## 🎯 Why Ground Truth is Better

### Traditional Correction-Based Training:
1. Claude analyzes (might miss things)
2. You correct what Claude found
3. **Problem**: If Claude missed something, you might not add it

### Ground Truth Training:
1. **YOU label EVERYTHING comprehensively**
2. Claude analyzes same schematic
3. System compares: Claude vs YOU
4. **Result**: Nothing missed, complete training data

## 🚀 Quick Start

```bash
# Train on one page with ground truth
python3 scripts/train_agent_with_ground_truth.py --pdf data/pdfs/section_61/61_1.pdf --page 0

# Train on entire section with ground truth
python3 scripts/train_agent_with_ground_truth.py --section 61
```

## 📋 Ground Truth Workflow

### Step 1: YOU Label the Schematic

The system will ask you to label:

**Components:**
```
Labeling: Components
Examples: HVC3, Slave 22, Cabinet E11, IM151, etc.

Enter items one per line:
  [1]: HVC3
    ✓ Added: HVC3
  [2]: Slave 23
    ✓ Added: Slave 23
  [3]: Cabinet E11
    ✓ Added: Cabinet E11
  [4]: IM151
    ✓ Added: IM151
  [5]: <Enter to finish>

4 Components labeled
```

**Index References:**
```
Labeling: Index References
Examples: =61/102.0.8, =10/103.0.7, etc.

  [1]: =61/102.0.8
  [2]: =61/103.0.7
  [3]: =61/104.0.5
  [4]: <Enter to finish>

3 Index References labeled
```

**Wire Connections:**
```
Labeling: Wire Connections
Examples: W1 connects to W2 at terminal 5

  [1]: W1 connects to HVC3 terminal 1
  [2]: W2 connects to Slave 23 input 5
  [3]: <Enter to finish>

2 Wire Connections labeled
```

### Step 2: Claude Analyzes

Claude Vision AI analyzes the same schematic and finds what it can.

### Step 3: Comparison & Metrics

```
╔════════ Analysis vs Ground Truth Comparison ════════╗

Overall Performance:
  Precision: 85.7%  (6 correct out of 7 found)
  Recall: 66.7%     (6 correct out of 9 in ground truth)
  F1 Score: 75.0%

By Category:
┌─────────────────┬────────┬───────┬─────────┬────────┬────────┐
│ Category        │ GT     │ Found │ Correct │ Missed │ False+ │
├─────────────────┼────────┼───────┼─────────┼────────┼────────┤
│ Components      │   4    │   3   │    3    │   1    │   0    │
│ Index Refs      │   3    │   3   │    2    │   1    │   1    │
│ Wire Connect    │   2    │   1   │    1    │   1    │   0    │
└─────────────────┴────────┴───────┴─────────┴────────┴────────┘

Missed Items:
  • components: IM151
  • index_references: =61/104.0.5
  • wire_connections: W2 connects to Slave 23 input 5

False Positives:
  • index_references: =61/102.8 (should be =61/102.0.8)
```

### Step 4: Training Data Created

Your ground truth labels become the training data:

✅ **Training example** with your complete labels
✅ **Schematic image** included
✅ **Performance metrics** tracked
✅ **What Claude missed** documented

## 💡 Best Practices

### 1. Be Comprehensive

Label EVERYTHING you see:
- All components (don't skip obvious ones)
- All index references (even partial ones)
- All wire connections you can identify

### 2. Be Consistent

Use same format every time:
```
Good:
  - HVC3
  - Slave 23
  - =61/102.0.8

Inconsistent:
  - hvc3
  - slave 23
  - 61/102.0.8
```

### 3. Be Specific

Include location details when useful:
```
Good:
  - HVC3 at top left near =61/102.0.8
  - Slave 23 in Cabinet E11

Basic:
  - HVC3
  - Slave 23
```

### 4. Add Context

Use the notes field:
```
Notes: "This page shows main power distribution.
Wire W1 partially obscured by fold in scan."
```

## 📊 What You Get

### High-Quality Training Data

Your labels create:
- **Complete examples** (nothing missed)
- **Accurate ground truth** (you're the expert)
- **Context-rich data** (with notes and details)

### Performance Metrics

Track Claude's improvement:
- **Precision**: What % of Claude's finds are correct?
- **Recall**: What % of actual items does Claude find?
- **F1 Score**: Overall performance metric

### Learning Insights

See exactly what Claude needs to learn:
- **Missed items**: What Claude can't find yet
- **False positives**: What Claude hallucinates
- **Common patterns**: What types of items are hard

## 🎓 Training Strategy

### Phase 1: Baseline (Pages 1-10)

- Label 10 diverse pages completely
- Establish baseline metrics
- Identify common misses

### Phase 2: Focused Training (Pages 11-30)

- Focus on pages with items Claude struggles with
- Add more examples of challenging components
- Build up difficult categories

### Phase 3: Validation (Pages 31-50)

- Test on new pages
- Measure improvement
- Refine as needed

### Phase 4: Fine-tuning Ready (50+ pages)

- Export dataset
- Submit for fine-tuning
- Create custom model

## 📈 Tracking Progress

View statistics at any time:

```bash
python3 scripts/train_agent_with_ground_truth.py --stats
```

Shows:
- Total ground truth examples
- Average Claude performance
- Most common misses
- Category-specific metrics

## 🔄 Comparison: Two Training Methods

### Correction-Based (`train_agent.py`)

**Pros:**
- Faster (just correct what Claude found)
- Good for quick iterations

**Cons:**
- Might miss items Claude doesn't find
- Less comprehensive
- Lower quality training data

**Best for:** Quick training, fewer examples

### Ground Truth (`train_agent_with_ground_truth.py`)

**Pros:**
- Comprehensive (label everything)
- Higher quality training data
- Clear performance metrics
- Nothing missed

**Cons:**
- Takes more time per page
- More labeling effort

**Best for:** High-quality dataset, fine-tuning preparation

## 💡 Which Should You Use?

### Use Ground Truth Training When:

✅ Building dataset for fine-tuning
✅ Need highest quality training data
✅ Want comprehensive coverage
✅ Need performance metrics
✅ Creating validation set

### Use Correction-Based Training When:

✅ Quick iterations
✅ Claude is already ~70% accurate
✅ Just refining existing model
✅ Time-constrained

## 🚀 Recommended Approach

**Best Strategy:**

1. **Start with Ground Truth** (first 10-20 pages)
   - Establish high-quality baseline
   - Get comprehensive labels
   - Measure Claude's starting performance

2. **Switch to Correction-Based** (if Claude improves)
   - Once Claude is 70%+ accurate
   - Faster iterations
   - Fine-tune remaining issues

3. **Return to Ground Truth** (for validation)
   - Test final performance
   - Validate on new schematics
   - Prepare final fine-tuning dataset

## 📁 Output Files

Ground truth training creates:

```
data/
├── ground_truth/
│   ├── 61_1_page0_gt.json
│   ├── 61_1_page1_gt.json
│   └── ...
└── training_data/
    ├── training_examples.jsonl
    ├── learned_knowledge.json
    └── finetuning_dataset.jsonl
```

## 🎯 Example Session

```bash
# Start training
python3 scripts/train_agent_with_ground_truth.py --pdf data/pdfs/section_61/61_1.pdf

# Label components
Components: HVC3, Slave 23, Cabinet E11, IM151

# Label index references
Index References: =61/102.0.8, =61/103.0.7, =61/104.0.5

# Label wire connections
Wire Connections: W1 to HVC3 terminal 1, W2 to Slave 23 input 5

# Claude analyzes...
# Comparison shows:
#   - Claude found 3/4 components (missed IM151)
#   - Claude found 2/3 index refs correctly
#   - Claude found 1/2 wire connections

# Training data saved with YOUR labels as ground truth!
```

## ✅ Start Now

```bash
# Train your first page
python3 scripts/train_agent_with_ground_truth.py --pdf data/pdfs/section_61/61_1.pdf --page 0
```

Your comprehensive labels will create the best possible training data for Claude!
