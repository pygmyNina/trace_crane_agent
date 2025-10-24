# PDF Schematic Library

This directory contains crane schematic PDFs organized by section for training purposes.

## Directory Structure

```
pdfs/
├── section_61/          # Section 61 schematics (61.1 - 61.8)
├── section_10/          # Section 10 schematics
├── other_sections/      # Other section schematics
└── catalog.json         # PDF catalog and metadata
```

## Adding PDFs

### Section 61 PDFs

Place your section 61 PDFs in `section_61/` directory:

```bash
# Copy your PDFs to the section_61 directory
cp /path/to/your/61.1.pdf data/pdfs/section_61/
cp /path/to/your/61.2.pdf data/pdfs/section_61/
# ... etc for 61.1 through 61.8
```

### Recommended Naming Convention

Use clear, consistent names:
```
section_61/
  ├── 61.1_sheet_description.pdf
  ├── 61.2_sheet_description.pdf
  ├── 61.3_sheet_description.pdf
  ├── 61.4_sheet_description.pdf
  ├── 61.5_sheet_description.pdf
  ├── 61.6_sheet_description.pdf
  ├── 61.7_sheet_description.pdf
  └── 61.8_sheet_description.pdf
```

Or simply:
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

## Cataloging PDFs

After adding PDFs, run the catalog script to index them:

```bash
python scripts/catalog_pdfs.py
```

This will:
- Scan all PDF directories
- Extract metadata (pages, size, etc.)
- Detect index references
- Find components
- Update catalog.json

## Using PDFs in Training

### Load a specific PDF
```bash
python main.py --pdf data/pdfs/section_61/61_1.pdf
```

### Load an entire section (using helper script)
```bash
python scripts/train_with_section.py --section 61
```

### Load specific sheets from a section
```bash
python scripts/train_with_section.py --section 61 --sheets 1,2,3
```

## PDF Catalog Format

The `catalog.json` file contains:

```json
{
  "section_61": [
    {
      "filename": "61_1.pdf",
      "path": "data/pdfs/section_61/61_1.pdf",
      "sheet": "61.1",
      "pages": 1,
      "size_bytes": 245678,
      "added_date": "2025-10-24T00:10:00",
      "index_references": ["=61/102.0.8", "=61/103.0.7"],
      "components": ["HVC3", "Slave 22"],
      "description": "Optional description"
    }
  ]
}
```

## Tips

1. **Keep original filenames** if they're descriptive
2. **Add descriptions** in catalog.json for clarity
3. **Run catalog script** after adding new PDFs
4. **Backup PDFs** - they're in .gitignore by default
5. **Test PDFs** with the PDF processor before training

## Example Workflow

```bash
# 1. Add your PDFs
cp ~/Downloads/section_61/*.pdf data/pdfs/section_61/

# 2. Catalog them
python scripts/catalog_pdfs.py

# 3. View what was added
cat data/pdfs/catalog.json

# 4. Start training with section 61
python scripts/train_with_section.py --section 61

# Or load a specific sheet
python main.py --pdf data/pdfs/section_61/61_1.pdf
```

## Troubleshooting

**PDFs not found**
- Check file paths are correct
- Ensure PDFs are in the right directory
- Run catalog script to update index

**PDF processing errors**
- Verify PDFs aren't password-protected
- Check PDF format compatibility
- Try opening in a PDF reader first

**Missing metadata**
- Re-run catalog script
- Check PDF isn't corrupted
- Verify PyMuPDF can open the file
