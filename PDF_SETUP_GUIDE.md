# PDF Library Setup Guide

Complete guide for adding your section 61 crane schematics to the TRACE training system.

## Quick Start

Follow these 4 simple steps to add your PDFs:

### Step 1: Copy Your PDFs

Copy your section 61 PDFs (61.1 through 61.8) to the `data/pdfs/section_61/` directory:

```bash
# If all PDFs are in one folder:
cp /path/to/your/section_61/*.pdf data/pdfs/section_61/

# Or copy individually:
cp /path/to/61.1.pdf data/pdfs/section_61/
cp /path/to/61.2.pdf data/pdfs/section_61/
cp /path/to/61.3.pdf data/pdfs/section_61/
# ... etc
```

### Step 2: Catalog the PDFs

Run the catalog script to index your PDFs:

```bash
python scripts/catalog_pdfs.py --scan
```

This will:
- ✅ Scan all PDFs in section_61/
- ✅ Extract metadata (pages, size, etc.)
- ✅ Detect index references (=XX/YY.Y.Z)
- ✅ Find components (HVC, Slave, etc.)
- ✅ Create `data/pdfs/catalog.json`

### Step 3: Verify the Catalog

View what was cataloged:

```bash
python scripts/catalog_pdfs.py --show
```

You should see a table showing:
- Filenames
- Page counts
- Index references found
- Components found

### Step 4: Start Training!

Train with your section 61 PDFs:

```bash
# Option A: Train with entire section 61
python scripts/train_with_section.py --section 61

# Option B: Train with specific sheets
python scripts/train_with_section.py --section 61 --sheets 1,2,3

# Option C: Train with a single PDF
python main.py --pdf data/pdfs/section_61/61_1.pdf
```

---

## Detailed Instructions

### PDF Naming Conventions

For best results, use consistent naming:

**Recommended:**
```
section_61/
  ├── 61_1.pdf
  ├── 61_2.pdf
  ├── 61_3.pdf
  ├── 61_4.pdf
  ├── 61_5.pdf
  ├── 61_6.pdf
  ├── 61_7.pdf
  └── 61_8.pdf
```

**Also works:**
```
section_61/
  ├── section_61.1.pdf
  ├── section_61.2.pdf
  └── ...
```

**With descriptions:**
```
section_61/
  ├── 61.1_main_power.pdf
  ├── 61.2_control_circuits.pdf
  └── ...
```

### Directory Structure

The system supports multiple sections:

```
data/pdfs/
├── section_61/        # Your section 61 PDFs go here
├── section_10/        # Future: section 10 PDFs
├── other_sections/    # Future: other sections
├── catalog.json       # Auto-generated catalog
└── README.md          # PDF library documentation
```

### Catalog File Format

After running the catalog script, `catalog.json` will contain:

```json
{
  "section_61": [
    {
      "filename": "61_1.pdf",
      "path": "data/pdfs/section_61/61_1.pdf",
      "pages": 1,
      "size_bytes": 245678,
      "added_date": "2025-10-24T00:15:00",
      "index_references": [
        "=61/102.0.8",
        "=61/103.0.7"
      ],
      "components": [
        "HVC3",
        "Slave 22",
        "Cabinet E11"
      ],
      "title": "",
      "description": ""
    }
  ]
}
```

### Adding Descriptions (Optional)

You can manually edit `catalog.json` to add descriptions:

```json
{
  "filename": "61_1.pdf",
  ...
  "description": "Main power distribution for section 61"
}
```

Then PDFs will show descriptions during training.

---

## Training Workflows

### Workflow 1: Train with Entire Section

Best for comprehensive practice:

```bash
python scripts/train_with_section.py --section 61
```

This will:
1. Show all PDFs in section 61
2. Ask for confirmation
3. Train with each PDF sequentially
4. Track progress across all sheets

### Workflow 2: Train with Specific Sheets

Focus on particular sheets:

```bash
# Train with sheets 1, 2, and 3
python scripts/train_with_section.py --section 61 --sheets 1,2,3

# Train with just sheet 8 (the new one you're adding)
python scripts/train_with_section.py --section 61 --sheets 8
```

### Workflow 3: Train with Single PDF

Deep dive into one schematic:

```bash
python main.py --pdf data/pdfs/section_61/61_8.pdf
```

### Workflow 4: Interactive Selection

Let the system guide you:

```bash
# Run without arguments for interactive mode
python scripts/train_with_section.py --list

# Select section interactively
python scripts/train_with_section.py
```

---

## Catalog Management

### View Current Catalog

```bash
python scripts/catalog_pdfs.py --show
```

### Re-scan All PDFs

If you add more PDFs later:

```bash
python scripts/catalog_pdfs.py --scan
```

### Scan Specific Section

Only update one section:

```bash
python scripts/catalog_pdfs.py --scan --section 61
```

### List Available Sections

```bash
python scripts/train_with_section.py --list
```

---

## Training Tips

### 1. Start with One PDF

Test the system with a single PDF first:

```bash
python main.py --pdf data/pdfs/section_61/61_1.pdf
```

Verify:
- PDF loads correctly
- Index references are detected
- Components are found
- Training questions make sense

### 2. Progress Through Section Sequentially

Train in order (61.1, 61.2, 61.3...):

```bash
python scripts/train_with_section.py --section 61
```

### 3. Review Problem Areas

After training, check your corrections:

```bash
python main.py
# Select option 4: Review Past Sessions
```

### 4. Practice Weak Sheets

If sheet 61.5 gave you trouble:

```bash
python scripts/train_with_section.py --section 61 --sheets 5
```

---

## Troubleshooting

### "No PDFs found"

**Problem:** Catalog script doesn't find your PDFs

**Solutions:**
- Verify PDFs are in correct directory: `ls data/pdfs/section_61/`
- Check file extensions are `.pdf` (lowercase)
- Ensure PDFs aren't in subdirectories

### "Error processing PDF"

**Problem:** PDF fails to process

**Solutions:**
- Check PDF isn't password-protected
- Try opening PDF in a viewer first
- Verify file isn't corrupted
- Check PyMuPDF is installed: `pip install PyMuPDF`

### "Catalog is empty"

**Problem:** `catalog.json` has no entries

**Solutions:**
- Run catalog script: `python scripts/catalog_pdfs.py --scan`
- Check PDFs are in section directories
- Verify directory structure is correct

### "Index references not found"

**Problem:** PDF processed but no index references detected

**Solutions:**
- Check if PDF is image-based (needs OCR)
- Verify index references follow =XX/YY.Y.Z format
- Text might not be extractable from PDF

---

## Advanced Usage

### Custom Catalog Entries

Edit `catalog.json` manually to add:

```json
{
  "filename": "61_8.pdf",
  "path": "data/pdfs/section_61/61_8.pdf",
  "description": "Final sheet completing section 61 set",
  "notes": "Added Oct 24, 2025 - completes the section"
}
```

### Organize by Date

Keep track when PDFs were added:

```bash
# After adding new PDFs
python scripts/catalog_pdfs.py --scan
# Catalog automatically timestamps additions
```

### Export Catalog

Share catalog without PDFs:

```bash
cp data/pdfs/catalog.json section_61_catalog_backup.json
```

---

## Complete Example

Here's a complete workflow for adding your section 61 PDFs:

```bash
# 1. Navigate to project
cd trace_crane_agent

# 2. Copy your PDFs
cp ~/Downloads/crane_schematics/61.*.pdf data/pdfs/section_61/

# 3. Verify files copied
ls -lh data/pdfs/section_61/

# 4. Catalog the PDFs
python scripts/catalog_pdfs.py --scan

# 5. View what was cataloged
python scripts/catalog_pdfs.py --show

# 6. Test with one PDF first
python main.py --pdf data/pdfs/section_61/61_1.pdf
# Answer a few questions to verify it works

# 7. Train with the section
python scripts/train_with_section.py --section 61

# 8. Review your progress
python main.py
# Select option 7 (Statistics)
```

---

## Next Steps

After adding your PDFs:

1. ✅ **Verify catalog** - Check all 8 PDFs are indexed
2. ✅ **Test one PDF** - Ensure processing works
3. ✅ **Start training** - Begin with section 61
4. ✅ **Track progress** - Review statistics regularly
5. ✅ **Focus practice** - Use category practice for weak areas

---

## Questions?

- **Where are PDFs stored?** `data/pdfs/section_61/`
- **What's in catalog.json?** Metadata and index of all PDFs
- **Can I add more sections?** Yes! Create `section_10/`, `section_20/`, etc.
- **Are PDFs committed to git?** No, they're in `.gitignore`
- **Can I share PDFs?** Yes, but catalog separately from PDFs

---

**Ready to add your section 61 PDFs? Follow Step 1 above!**
