import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

from ContextBuilder import ContextBuilder
from ModelProcessor import ModelProcessor
from ResultFormatter import ResultFormatter
from UIInput import UIInput


logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.context_builder = ContextBuilder()
        self.model_processor = ModelProcessor(self.config)
        self.formatter = ResultFormatter()
        self.ui = UIInput()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from config.json.

        Tries the provided path first, then searches parent directories (cwd and
        script location). If no config file is found, falls back to sensible
        defaults and continues. The ANTHROPIC_API_KEY environment variable is
        loaded if present; otherwise a warning is logged and api_key is left
        unset (None).
        """
        cfg_path = Path(config_path)

        # If the provided path doesn't exist, search upward from cwd and script dir
        if not cfg_path.exists():
            searched = False
            for base in (Path.cwd(), Path(__file__).resolve().parent):
                for parent in (base, *base.parents):
                    candidate = parent / config_path
                    if candidate.exists():
                        cfg_path = candidate
                        searched = True
                        break
                if searched:
                    break

        if cfg_path.exists():
            try:
                with open(cfg_path, 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to parse config file '{cfg_path}': {e}")
                raise
        else:
            logger.warning(f"Config file '{config_path}' not found. Using defaults.")
            # Defaults mirror the repository's example config
            config = {
                "base_url": None,
                "models": ["claude-sonnet-4-6", "claude-opus-4-1"],
                "max_tokens": 4096,
                "temperature": 0.2
            }

        # Load API key from environment variable if present
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            config['api_key'] = api_key
        else:
            logger.warning("ANTHROPIC_API_KEY environment variable not set. API calls will fail unless provided.")
            config.setdefault('api_key', None)

        return config

    def analyze_project_sequential(self, project_dir: str) -> Dict[str, Any]:
        """Analyze project using sequential model processing"""
        logger.info(f"[*] Analyzing project sequentially: {project_dir}")
        
        # Build project context
        logger.info("[*] Building project context...")
        project_context = self.context_builder.build_prompt_context(project_dir)
        
        # Process with models sequentially
        logger.info("[*] Processing with models sequentially...")
        results = self.model_processor.process_with_models_sequential(project_context)
        
        # Display results (support both dict and list return types)
        display_items = results.get('results', results) if isinstance(results, dict) else results
        self.formatter.display_results(display_items)
        
        return {
            "mode": "sequential",
            "results": results.get('results', results) if isinstance(results, dict) else results,
            "project_dir": project_dir
        }

    async def analyze_project_parallel(self, project_dir: str) -> Dict[str, Any]:
        """Analyze project using parallel model processing"""
        logger.info(f"[*] Analyzing project in parallel: {project_dir}")
        
        # Build project context
        logger.info("[*] Building project context...")
        project_context = self.context_builder.build_prompt_context(project_dir)
        
        # Process with models in parallel
        logger.info("[*] Processing with models in parallel...")
        results = await self.model_processor.process_with_models_parallel(project_context)
        
        # Display results (support both dict and list return types)
        display_items = results.get('results', results) if isinstance(results, dict) else results
        self.formatter.display_results(display_items)
        
        return {
            "mode": "parallel",
            "results": results.get('results', results) if isinstance(results, dict) else results,
            "project_dir": project_dir
        }

    def code_review(self, project_dir: str, analysis_results: list = None) -> Dict[str, Any]:
        """Generate code review for the project"""
        logger.info(f"[*] Generating code review: {project_dir}")
        
        # Build project context
        if not analysis_results:
            logger.info("[*] Building project context...")
            project_context = self.context_builder.build_prompt_context(project_dir)
            
            # First run analysis if not provided
            logger.info("[*] Running initial analysis...")
            analysis_results = self.model_processor.process_with_models_sequential(project_context)
        else:
            project_context = self.context_builder.build_prompt_context(project_dir)

        quality_data = analysis_results if isinstance(analysis_results, dict) else {}
        model_results = quality_data.get("model_results", quality_data.get("results", analysis_results))
        
        # Generate code review
        logger.info("[*] Generating code review...")
        review = self.model_processor.generate_code_review(
            project_context,
            model_results,
            quality_data.get("mutation_testing"),
            quality_data.get("genetic_improvement"),
        )
        
        # Display review
        self.formatter.display_code_review(review)
        
        return {
            "mode": "code_review",
            "review": review,
            "project_dir": project_dir
        }

    def save_results(self, results: Dict[str, Any], output_dir: str = ".") -> None:
        """Save analysis results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        mode = results.get('mode', 'unknown')
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

        # Use project name if available for filenames
        project_name = Path(results.get('project_dir', '.')).name or 'project'

        # Save text results
        if mode == "code_review":
            text_file = output_path / f"{project_name}_code_review_{timestamp}.txt"
            json_file = output_path / f"{project_name}_code_review_{timestamp}.json"
            content = self.formatter.format_code_review(results.get('review', {}))
            self.formatter.save_to_file(content, str(text_file))
            self.formatter.save_json(results, str(json_file))
        else:
            text_file = output_path / f"{project_name}_analysis_{mode}_{timestamp}.txt"
            json_file = output_path / f"{project_name}_analysis_{mode}_{timestamp}.json"
            content = self.formatter.format_results(results.get('results', []))
            self.formatter.save_to_file(content, str(text_file))
            self.formatter.save_json(results, str(json_file))


def main():
    """Main entry point"""
    import argparse

    def load_dotenv_if_present():
        """Load a simple .env file from cwd and script dir into os.environ."""
        for base in (Path.cwd(), Path(__file__).resolve().parent):
            dotenv = base / '.env'
            if dotenv.exists():
                try:
                    with open(dotenv, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith('#'):
                                continue
                            if '=' not in line:
                                continue
                            k, v = line.split('=', 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k:
                                os.environ.setdefault(k, v)
                                logger.info(f"Loaded env var from {dotenv}: {k}=***")
                except Exception as e:
                    logger.warning(f"Failed to read {dotenv}: {e}")

    # Minimal mock to run pipeline without external API calls
    class MockModelProcessor:
        def __init__(self, *args, **kwargs):
            self.model_list = ["mock-model"]

        def process_with_models_sequential(self, project_data: str):
            result = {
                "model": "mock-model",
                "response": "Mock analysis: project structure appears valid.",
                "status": "success",
                "response_length": 46
            }
            return {
                "results": [result],
                "model_results": [result],
                "mutation_testing": {"mutation_summary": "mock", "mutation_findings": "none"},
                "genetic_improvement": {"generation_summary": "mock", "best_solution": "none"}
            }

        async def process_with_models_parallel(self, project_data: str):
            return self.process_with_models_sequential(project_data)

        def generate_code_review(self, project_data: str, results, *args, **kwargs):
            return {
                "review": "Mock code review: no obvious issues found.",
                "summary": "Mock summary",
                "recommendations": "No action required",
                "mutation_testing": {},
                "genetic_improvement": {},
                "status": "success"
            }

    parser = argparse.ArgumentParser(description='Project Analyzer using Claude AI Models')
    parser.add_argument('project_dir', nargs='?', default='.', help='Path to project directory to analyze (default: current directory)')
    parser.add_argument('--mode', choices=['sequential', 'parallel', 'review'], default='sequential',
                       help='Analysis mode')
    parser.add_argument('--output', default='.', help='Output directory for results')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    parser.add_argument('--dry-run', action='store_true', help='Run without external API calls (mock)')

    args = parser.parse_args()

    # Load .env files early so environment variables are available to ModelProcessor
    load_dotenv_if_present()

    try:
        # Initialize analyzer
        analyzer = ProjectAnalyzer(args.config)

        # Replace real model processor with mock when requested
        if args.dry_run:
            logger.info("[*] Dry run enabled - using MockModelProcessor (no external API calls)")
            analyzer.model_processor = MockModelProcessor()

        # Run analysis based on mode
        if args.mode == 'sequential':
            logger.info("[*] Running in SEQUENTIAL mode")
            results = analyzer.analyze_project_sequential(args.project_dir)
        elif args.mode == 'parallel':
            logger.info("[*] Running in PARALLEL mode")
            results = asyncio.run(analyzer.analyze_project_parallel(args.project_dir))
        elif args.mode == 'review':
            logger.info("[*] Running in CODE REVIEW mode")
            results = analyzer.code_review(args.project_dir)

        # Save results
        analyzer.save_results(results, args.output)
        logger.info("[OK] Analysis complete!")

    except Exception as e:
        logger.error(f"[ERROR] Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
