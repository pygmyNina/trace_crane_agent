# Quick Start Guide

Get started with TRACE Training System in 5 minutes!

## Step 1: Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Configure API Key

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

Get your API key from: https://console.anthropic.com/

## Step 3: Run the System

### Option A: Interactive Menu

```bash
python main.py
```

This opens an interactive menu where you can:
- Start training sessions
- Take quizzes
- Practice specific categories
- Review your progress

### Option B: Direct Training

Start training immediately:

```bash
python main.py --mode interactive
```

### Option C: With a PDF

Load a crane schematic PDF:

```bash
python main.py --pdf path/to/schematic.pdf
```

## Your First Training Session

1. Select option **1** from the menu (Start Training Session)
2. The AI trainer will introduce itself and ask your first question
3. Answer to the best of your ability
4. Get immediate feedback and explanations
5. Type `quit` when done to see your session summary

## Example Interaction

```
╔══════════════════════════════════════════════════════════════╗
║   TRACE Training System for Crane Schematics                ║
╚══════════════════════════════════════════════════════════════╝

[AI Trainer]: Hello! Let's start with a fundamental question.

What does the shorthand notation =61/102.8 expand to in full format?

Your answer: =61/102.0.8

[AI Trainer]: Excellent! That's correct!

The shorthand =61/102.8 expands to =61/102.0.8 because when the
sheet minor digit (.Y) is 0, it can be omitted.

Let me ask you another question about wire tracing...
```

## Practice Categories

Focus on specific areas:

```bash
python main.py --mode practice --category index_format
```

Available categories:
- `index_format` - Index notation (=XX/YY.Y.Z)
- `wire_tracing` - Wire connections
- `component_identification` - Component ID
- `slave_sequence` - Slave order
- `module_counting` - Module counting
- `notation` - Shorthand notation
- `location` - Component locations

## Quiz Mode

Test your knowledge:

```bash
python main.py --mode quiz
```

You'll be asked a series of questions and get a score at the end.

## Review Your Progress

From the main menu, select option **4** to see:
- Past training sessions
- Your accuracy over time
- Questions you got wrong
- Areas for improvement

## View Foundation Knowledge

Select option **5** from the menu to review:
- Index format rules
- Wire tracing principles
- Slave sequence patterns
- Component examples

## Commands During Training

While in a training session:

- `quit` or `exit` - End the session
- `feedback` - See your current progress
- `help` - View foundation knowledge

## Tips for Success

1. **Start with the basics** - Review the foundation knowledge first
2. **Practice regularly** - Short, frequent sessions work best
3. **Review corrections** - Learn from mistakes
4. **Focus on problem areas** - Use category-specific practice
5. **Use real schematics** - Load PDFs for hands-on practice

## Foundation Knowledge Quick Reference

### Index Format
- **Format**: `=XX/YY.Y.Z`
  - XX = Section (2 digits)
  - YY.Y = Sheet (2 + 1 decimal)
  - Z = Column (1 digit)
- **Shorthand**: `=61/102.8` = `=61/102.0.8`

### Wire Tracing
- **Dots** = Connection
- **No dots** at perpendicular crossing = No connection

### Slave Sequence
Non-chronological: **22, 23, 60, 24, 61, 20**

### Slave 22 Example
- Location: **Cabinet E11**
- Modules: **45 total**
  - 1 IM151
  - 1 PM
  - 40 DI
  - 3 RTD

## Next Steps

1. Complete your first training session
2. Try a 10-question quiz
3. Practice your weakest category
4. Load a real PDF schematic
5. Review your statistics

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Review foundation knowledge (menu option 5)
- Run tests: `python tests/test_knowledge_base.py`

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
- Make sure you created `.env` file
- Check the API key is correct
- Or export: `export ANTHROPIC_API_KEY=your_key`

**PDF won't load**
- Check file path is correct
- Ensure PDF is not password-protected
- Verify PyMuPDF is installed: `pip install PyMuPDF`

**Database errors**
- Delete `data/training.db` to reset
- Session history will be lost

## Happy Training!

The TRACE system is designed to help you master crane schematics through:
- Interactive conversations
- Immediate feedback
- Progress tracking
- Personalized practice

Start your journey to becoming a crane schematic expert today!
