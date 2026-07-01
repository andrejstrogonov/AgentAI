# AgentAI - Quick Start Guide

## Installation & Setup

```bash
# 1. Install dependencies
pip install anthropic

# 2. Set API key (Windows PowerShell)
$env:ANTHROPIC_API_KEY='your_key_here'

# Or create .env file
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

## Usage Examples

### 1️⃣ Sequential Analysis (One model at a time)
```bash
python main.py . --mode sequential
```
**Output:** `analysis_sequential.txt` and `analysis_sequential.json`

### 2️⃣ Parallel Analysis (All models simultaneously) - FASTER!
```bash
python main.py . --mode parallel
```
**Output:** `analysis_parallel.txt` and `analysis_parallel.json`

### 3️⃣ Code Review (Full analysis + comprehensive review)
```bash
python main.py . --mode review
```
**Output:** `code_review_code_review.txt` and `code_review_code_review.json`

### 4️⃣ Analyze External Project
```bash
python main.py C:\path\to\project --mode sequential
```

### 5️⃣ Custom Output Directory
```bash
python main.py . --mode parallel --output ./results
```

## Architecture

### Three Processing Modes:

**Sequential Mode**
```
Project → Model 1 → Result 1 → Model 2 → Result 2 → Done
   (slower but resource-efficient)
```

**Parallel Mode**
```
Project → [Model 1, Model 2] (concurrent) → Results → Done
   (faster - all models run simultaneously)
```

**Code Review Mode**
```
Project → Analysis (seq/par) → Code Review → Results → Done
   (comprehensive feedback on findings)
```

## File Structure

```
AgentAI/
├── main.py              ← Entry point (ProjectAnalyzer class)
├── ContextBuilder.py    ← Scans and builds project context
├── ModelProcessor.py    ← Handles AI model interactions
├── ResultFormatter.py   ← Formats and displays results
├── UIInput.py          ← User interface helpers
├── config.json         ← Configuration (models, API URL)
├── .env                ← API key (not in repo)
└── .env.example        ← Template for .env
```

## Key Features

✅ **Unified Prompts** - system_prompt and user_query combined  
✅ **3 Processing Modes** - Sequential, Parallel, Code Review  
✅ **Async Support** - Fast parallel processing with asyncio  
✅ **Secure** - API key in environment variables  
✅ **JSON Export** - Results in JSON format  
✅ **Error Handling** - Graceful failure recovery  
✅ **Cross-platform** - Windows/Linux/Mac compatible  

## Classes Overview

### ProjectAnalyzer (main.py)
- `analyze_project_sequential()` - Sequential mode
- `analyze_project_parallel()` - Parallel mode (async)
- `code_review()` - Code review mode
- `save_results()` - Save to files

### ContextBuilder
- `build_project_context()` - Full project analysis
- `build_prompt_context()` - Context as string for prompts

### ModelProcessor
- `process_with_models_sequential()` - Sync processing
- `process_with_models_parallel()` - Async processing
- `generate_code_review()` - Code review generation

### ResultFormatter
- `format_results()` - Format analysis results
- `display_results()` - Print to console
- `save_to_file()` - Save text results
- `save_json()` - Save JSON results

## Configuration

Edit `config.json`:
```json
{
    "base_url": "https://api.proxyapi.ru/anthropic",
    "models": ["claude-sonnet-4-6", "claude-opus-4-1"],
    "max_tokens": 4096,
    "temperature": 0.2
}
```

## Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-...

# Optional
ANTHROPIC_API_URL=https://api.proxyapi.ru/anthropic
```

## Output Files

**Sequential Mode:**
- `analysis_sequential.txt` - Human-readable results
- `analysis_sequential.json` - Machine-readable results

**Parallel Mode:**
- `analysis_parallel.txt` - Human-readable results
- `analysis_parallel.json` - Machine-readable results

**Code Review Mode:**
- `code_review_code_review.txt` - Full review
- `code_review_code_review.json` - Structured data

## Command Line Help

```bash
python main.py --help
```

Options:
- `project_dir` (positional) - Directory to analyze
- `--mode` - sequential | parallel | review (default: sequential)
- `--output` - Output directory (default: current directory)
- `--config` - Config file path (default: config.json)

## Troubleshooting

**Q: API key not found**
```bash
# Set environment variable
$env:ANTHROPIC_API_KEY='your_key'
```

**Q: Model not supported**
- Check config.json models match your API provider
- Check ProxyAPI supported models list

**Q: Large project causes memory issues**
- Increase `max_file_size` in ContextBuilder
- Exclude large directories in `ignore_dirs`

**Q: Results look truncated**
- Check output files (*.txt, *.json)
- Results in console may be abbreviated

## Performance Tips

1. **Use Parallel Mode** - 2x faster than sequential
2. **Limit File Size** - Reduce context size for faster processing
3. **Monitor Token Usage** - Set `max_tokens` appropriately
4. **Exclude Directories** - Add to `ignore_dirs` in ContextBuilder

## Python API Usage

```python
from main import ProjectAnalyzer
import asyncio

# Initialize
analyzer = ProjectAnalyzer('config.json')

# Sequential
results = analyzer.analyze_project_sequential('./project')

# Parallel
results = asyncio.run(analyzer.analyze_project_parallel('./project'))

# Code Review
review = analyzer.code_review('./project')

# Save
analyzer.save_results(results, './output')
```

## Support & Documentation

- Full docs: See `README_FULL.md`
- Issues: Check `analysis_result.txt` for AI-generated insights
- Examples: Run with `--help` flag

---

**Version:** 2.0  
**Status:** All modes working ✅  
**Last Updated:** 2026-07-01
