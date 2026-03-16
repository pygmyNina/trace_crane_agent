# TRACE Quick Start Guide

Get up and running with TRACE in 5 minutes!

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Import October 23 training data
python import_oct23_training.py

# 3. (Optional) Run demo to see features
python demo_trace.py

# 4. Launch TRACE
python trace_cli.py
```

## Your First Session

### 1. View What TRACE Already Knows

```bash
TRACE> summary
```

This shows the October 23 training data that's already loaded.

### 2. Query Existing Information

```bash
TRACE> show slave 22
TRACE> query HVC3
TRACE> query cabinet E11
```

### 3. Teach TRACE New Information

```bash
TRACE> train
Training> Slave 60 has 25 modules in Cabinet E15
Training> Motor M1 breaker goes to =20/50.3.2
Training> Emergency stop sequence: 10,11,12
Training> done
```

### 4. Verify TRACE Learned It

```bash
TRACE> show slave 60
TRACE> query motor M1
```

## Common Training Patterns

### Teaching About Slaves
```
Slave 24 has 35 modules (2 IM151, 1 PM, 30 DI, 2 AI) in Cabinet E13
```

### Teaching About Connections
```
Main contactor M1 goes to =15/200.5.1
Emergency stop button connects to =20/50.1.2
HVC3 breaker signal → =61/4.1.3
```

### Teaching Sequences
```
Hoist slave sequence: 22,23,24
Drive sequence: 60,61,62
Safety chain order: 10,11,12,13
```

### Teaching Rules
```
Wire rule: blue wires are neutral
Index format: sheet number / zone.row.column
Cabinet layout: E11 is main control, E12 is drives
```

### Making Corrections
```
Actually, Slave 22 is in Cabinet E10
Correction: the breaker goes to =61/4.1.4, not 4.1.3
I meant Cabinet E15, not E11
```

## Loading PDFs

```bash
# Place PDFs in schematics/ directory
TRACE> list

# Or load from anywhere
TRACE> load /path/to/crane_electrical.pdf
```

## Tips

1. **Be Specific**: Include all details (slave numbers, cabinet IDs, exact references)
2. **Use Actual Notation**: Use the real format (=XX/YY.Y.Z) from your schematics
3. **Train Often**: Quick sessions are better than trying to input everything at once
4. **Correct Immediately**: Fix mistakes right away so TRACE learns correctly
5. **Export Regularly**: Use `export backup.json` to save your work

## What TRACE Can Remember

- Slave configurations and module details
- Electrical connections and signal paths
- Component sequences and ordering
- Cabinet layouts and locations
- Wire colors and conventions
- Schematic notation rules
- Breaker and transformer locations
- Any corrections you make

## Next Steps

- Read the full [README.md](README.md) for all features
- Add your schematic PDFs to the `schematics/` directory
- Start training TRACE with your specific crane's configuration
- Use TRACE as your quick reference during maintenance

---

**Remember**: TRACE learns from YOU. The more you teach it, the more useful it becomes!
