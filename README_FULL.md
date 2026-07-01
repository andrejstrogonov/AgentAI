# AgentAI - Project Analysis Tool

A Python-based project analysis tool that leverages Claude AI models for code analysis, error detection, and code reviews. Supports sequential processing, parallel processing, and comprehensive code review generation.

## Features

- **Project Context Building**: Automatically scans and analyzes project structure
- **Sequential Model Processing**: Process project through multiple AI models sequentially
- **Parallel Model Processing**: Process project through multiple AI models in parallel (async)
- **Code Review Generation**: Generate comprehensive code reviews based on analysis results
- **Results Formatting**: Beautiful console output and file-based result storage
- **JSON Export**: Export results in JSON format for programmatic processing

## Components

### ContextBuilder
Scans project directories and builds comprehensive context including:
- Project metadata
- Directory tree structure
- File contents (source code)
- Dependencies (requirements.txt, package.json)
- CI/CD configurations
- README and LICENSE files
- Statistics

### ModelProcessor
Handles AI model interactions with support for:
- Sequential processing (`process_with_models_sequential`)
- Parallel processing (`process_with_models_parallel` - async)
- Code review generation (`generate_code_review`)

### ResultFormatter
Formats and displays results with:
- Console output formatting
- File saving (text and JSON)
- Summary generation
- Structured code review display

### UIInput
User interface helper providing:
- Prompt templates
- Result display methods
- File saving utilities

## Setup

### 1. Clone the repository
```bash
git clone <repository_url>
cd AgentAI
```

### 2. Install dependencies
```bash
pip install anthropic
```

### 3. Configure API key

Create a `.env` file with your Anthropic API key:
```bash
cp .env.example .env
# Edit .env and add your API key
```

Or set environment variable:
```bash
export ANTHROPIC_API_KEY="your_api_key_here"
```

### 4. Update config.json (optional)
Customize models and parameters in `config.json`:
```json
{
    "base_url": "https://api.proxyapi.ru/anthropic",
    "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
    "max_tokens": 4096,
    "temperature": 0.2
}
```

## Usage

### Command Line Interface

#### Sequential Analysis
```bash
python main.py /path/to/project --mode sequential
```

#### Parallel Analysis (faster)
```bash
python main.py /path/to/project --mode parallel
```

#### Code Review
```bash
python main.py /path/to/project --mode review
```

#### Custom Output Directory
```bash
python main.py /path/to/project --mode sequential --output ./results
```

#### Custom Config File
```bash
python main.py /path/to/project --config custom_config.json
```

### Python API

```python
from main import ProjectAnalyzer
import asyncio

# Initialize analyzer
analyzer = ProjectAnalyzer('config.json')

# Sequential analysis
results = analyzer.analyze_project_sequential('/path/to/project')

# Parallel analysis (async)
results = asyncio.run(analyzer.analyze_project_parallel('/path/to/project'))

# Code review
review = analyzer.code_review('/path/to/project')

# Save results
analyzer.save_results(results, './output')
```

## Project Structure

```
AgentAI/
├── main.py                 # Main entry point with ProjectAnalyzer class
├── ContextBuilder.py       # Project context building
├── ModelProcessor.py       # AI model interactions (sequential/parallel/review)
├── ResultFormatter.py      # Result formatting and display
├── UIInput.py             # User interface helpers
├── config.json            # Configuration file
├── .env                   # API key (not in repo)
├── .env.example           # Example env file
└── README.md              # This file
```

## Output Files

- `analysis_sequential.txt` - Sequential analysis results (text)
- `analysis_sequential.json` - Sequential analysis results (JSON)
- `analysis_parallel.txt` - Parallel analysis results (text)
- `analysis_parallel.json` - Parallel analysis results (JSON)
- `code_review_review.txt` - Code review results (text)
- `code_review_review.json` - Code review results (JSON)

## Error Handling

The tool includes comprehensive error handling:
- Missing API key detection
- Empty model list validation
- File I/O error handling
- Model processing error catching and reporting
- Graceful failure recovery

## Logging

Logging output shows operation status with prefixes:
- `[*]` - Information
- `[OK]` - Success
- `[ERROR]` - Error
- `[!]` - Warning

## Requirements

- Python 3.8+
- anthropic (Claude API client)
- Standard library: asyncio, json, logging, pathlib, os

## Architecture

### Sequential Mode
1. Load project context
2. Process with model 1
3. Wait for completion
4. Process with model 2
5. Wait for completion
6. Display results

### Parallel Mode
1. Load project context
2. Create async tasks for each model
3. Execute all in parallel
4. Wait for all to complete
5. Aggregate results
6. Display results

### Code Review Mode
1. Load project context
2. Run initial analysis (sequential or parallel)
3. Generate comprehensive code review based on results
4. Display formatted review with recommendations

## Best Practices

1. **For Production Deployment**: Store API key in secure environment variables
2. **For Large Projects**: Use parallel mode for faster processing
3. **For Detailed Analysis**: Run both sequential and parallel modes for comparison
4. **For CI/CD Integration**: Check exit codes and log files
5. **For Sensitive Code**: Review file exclusions in ContextBuilder.ignore_dirs

## Troubleshooting

### API Key Not Found
```
Error: ANTHROPIC_API_KEY environment variable not set
```
Solution: Create `.env` file with your API key or set environment variable

### Model Not Available
```
Error: Model not supported
```
Solution: Check config.json for correct model names

### Memory Issues with Large Projects
Solution: Increase `max_file_size` threshold or exclude large directories

## Contributing

Issues and pull requests are welcome!

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs in output files
3. Check config.json settings
4. Verify API key configuration
