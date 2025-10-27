# Changelog

## [Unreleased] - 2025-10-27

### Fixed
- **Continuous Processing Loop Issue**: The interactive training and practice modes were running in infinite loops without automatic exit conditions
  - Added configurable question limits to `interactive_training()` method (default: 10 questions)
  - Added configurable question limits to `practice_category()` method (default: 5 questions)
  - After reaching the question limit, users are prompted to continue or end the session (defaults to ending)
  - Added `--max-questions` CLI argument to configure limits from command line
  - Users can set unlimited questions by entering "unlimited", "none", or "0" when prompted

### Changed
- Training sessions now automatically prompt for continuation after a set number of questions
- Default behavior is to stop after 10 questions in interactive mode and 5 in practice mode
- Question limit is displayed when starting each training mode

### Usage Examples

**Command Line:**
```bash
# Use default 10 question limit
python main.py --mode interactive

# Set custom limit
python main.py --mode interactive --max-questions 20

# Unlimited questions
python main.py --mode interactive --max-questions 0

# Practice mode with custom limit
python main.py --mode practice --category wire_tracing --max-questions 5
```

**Interactive Menu:**
When selecting option 1 (Start Training), you'll be prompted to configure the question limit.

### Technical Details
- Modified `/src/training_interface.py:170` - Added `max_questions` parameter to `interactive_training()`
- Modified `/src/training_interface.py:304` - Added `max_questions` parameter to `practice_category()`
- Modified `/main.py:64` - Updated `start_training()` to support question limits
- Modified `/main.py:312-317` - Added CLI argument for `--max-questions`
