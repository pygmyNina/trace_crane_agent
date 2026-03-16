# Git LFS Setup Instructions

Git LFS is now enabled! Follow these steps on your Mac.

## Step 1: Install Git LFS (One Time)

```bash
brew install git-lfs
```

If you don't have Homebrew, install it first:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Step 2: Initialize Git LFS in Your Repo

```bash
# Navigate to your TRACE directory
cd ~/trace_crane_agent2

# Initialize Git LFS
git lfs install

# Pull the LFS configuration
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

You should see a message: `Git LFS initialized.`

## Step 3: Add Your PDF Files

```bash
# Create the electrical directory if it doesn't exist
mkdir -p schematics/electrical

# Copy your PDFs
cp ~/Desktop/trace_pdfs/10.pdf schematics/electrical/
cp ~/Desktop/trace_pdfs/61.pdf schematics/electrical/

# Or copy all at once
cp ~/Desktop/trace_pdfs/*.pdf schematics/electrical/
```

## Step 4: Commit and Push PDFs

```bash
# Add the PDFs (Git LFS will handle them automatically)
git add schematics/

# Commit
git commit -m "Add schematic PDFs: 10 and 61"

# Push (this uploads to LFS)
git push origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux
```

You'll see LFS upload messages like:
```
Uploading LFS objects: 100% (2/2), 15 MB | 0 B/s
```

## Step 5: Verify It Worked

```bash
# Check LFS status
git lfs ls-files

# You should see your PDFs listed
```

## On Your Second Computer (When Ready)

```bash
# 1. Install Git LFS
brew install git-lfs
git lfs install

# 2. Clone or pull
git pull origin claude/trace-crane-assistant-setup-011CUS8veJfeQ3PtL77rK1Ux

# 3. PDFs download automatically!
ls schematics/electrical/
# You'll see: 10.pdf  61.pdf
```

## Verify in TRACE

```bash
python3 trace_cli.py
TRACE> sections
TRACE> section electrical
```

You should see your PDFs listed!

## Troubleshooting

### "git-lfs: command not found"
Install Git LFS: `brew install git-lfs`

### PDFs not uploading
Run: `git lfs install` in your repo directory

### PDFs not downloading on Computer 2
Run: `git lfs pull`

### Check LFS status
```bash
git lfs ls-files  # List tracked files
git lfs env       # Show LFS environment
```

## What Just Happened?

✅ `.gitattributes` file created - tells git to use LFS for PDFs
✅ Pattern configured: `schematics/**/*.pdf`
✅ When you add PDFs and push, they go to GitHub LFS
✅ When others pull, PDFs download automatically
✅ No more manual PDF copying between computers!

## Next Steps

1. Run the commands above to add your PDFs
2. Push them to GitHub
3. On Computer 2, just `git pull` - PDFs appear!

---

**You're all set!** PDFs will now sync automatically between computers. 🎉
