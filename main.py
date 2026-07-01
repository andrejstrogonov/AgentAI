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
from TannerAnalyzer import TannerProjectAnalyzer, analyze_tanner_project
from EDAToolchain import OpenSourceEDAToolchain, get_tool_status
from TannerPatcher import TannerProjectPatcher, analyze_and_patch


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
        """Load configuration from config.json"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Load API key from environment variable
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            
            config['api_key'] = api_key
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def analyze_project_sequential(self, project_dir: str) -> Dict[str, Any]:
        """Analyze project using sequential model processing"""
        logger.info(f"[*] Analyzing project sequentially: {project_dir}")
        
        # Build project context
        logger.info("[*] Building project context...")
        project_context = self.context_builder.build_prompt_context(project_dir)
        
        # Process with models sequentially
        logger.info("[*] Processing with models sequentially...")
        results = self.model_processor.process_with_models_sequential(project_context)
        
        # Display results
        self.formatter.display_results(results)
        
        return {
            "mode": "sequential",
            "results": results,
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
        
        # Display results
        self.formatter.display_results(results)
        
        return {
            "mode": "parallel",
            "results": results,
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
        
        # Generate code review
        logger.info("[*] Generating code review...")
        review = self.model_processor.generate_code_review(project_context, analysis_results)
        
        # Display review
        self.formatter.display_code_review(review)
        
        return {
            "mode": "code_review",
            "review": review,
            "project_dir": project_dir
        }

    def analyze_tanner_project(self, project_dir: str) -> Dict[str, Any]:
        """Analyze Tanner EDA project (topology, DRC, LVS)"""
        logger.info(f"[*] Analyzing Tanner EDA project: {project_dir}")
        
        # Run Tanner analysis
        logger.info("[*] Scanning Tanner files...")
        analyzer = TannerProjectAnalyzer()
        tanner_analysis = analyzer.scan_project(project_dir)
        
        # Display results
        self.formatter.display_results([{
            'model': 'Tanner EDA Analyzer',
            'status': 'success',
            'response': analyzer.generate_report(tanner_analysis),
            'response_length': len(analyzer.generate_report(tanner_analysis))
        }])
        
        return {
            "mode": "tanner_analysis",
            "tanner_data": tanner_analysis,
            "report": analyzer.generate_report(tanner_analysis),
            "project_dir": project_dir
        }

    def patch_tanner_project(self, project_dir: str) -> Dict[str, Any]:
        """Analyze and patch Tanner project"""
        logger.info(f"[*] Patching Tanner project: {project_dir}")
        
        result = analyze_and_patch(project_dir)
        
        # Display report
        self.formatter.save_to_file(result['report'], f"{project_dir}/patch_report.txt")
        
        return {
            "mode": "tanner_patch",
            "analysis": result['analysis'],
            "patch_script": result['patch_script'],
            "report": result['report'],
            "project_dir": project_dir
        }

    def verify_with_opensource_tools(self, project_dir: str) -> Dict[str, Any]:
        """Verify project using open-source EDA tools"""
        logger.info(f"[*] Verifying with open-source tools: {project_dir}")
        
        # Check available tools
        toolchain = OpenSourceEDAToolchain()
        tool_status = toolchain.get_status()
        
        logger.info(f"[*] Available tools: {tool_status['installed_tools']}")
        
        # Run verification
        verification_results = toolchain.full_verification_flow(project_dir)
        
        return {
            "mode": "opensource_verification",
            "tool_status": tool_status,
            "verification": verification_results,
            "project_dir": project_dir
        }

    def save_results(self, results: Dict[str, Any], output_dir: str = ".") -> None:
        """Save analysis results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        mode = results.get('mode', 'unknown')
        
        # Save based on analysis type
        if mode == "code_review":
            text_file = output_path / f"code_review_{mode}.txt"
            json_file = output_path / f"code_review_{mode}.json"
            content = self.formatter.format_code_review(results.get('review', {}))
            self.formatter.save_to_file(content, str(text_file))
            self.formatter.save_json(results, str(json_file))
        
        elif mode == "tanner_analysis":
            text_file = output_path / f"tanner_analysis.txt"
            json_file = output_path / f"tanner_analysis.json"
            self.formatter.save_to_file(results.get('report', ''), str(text_file))
            self.formatter.save_json(results.get('tanner_data', {}), str(json_file))
        
        elif mode == "tanner_patch":
            text_file = output_path / f"tanner_patch_report.txt"
            json_file = output_path / f"tanner_patch_analysis.json"
            self.formatter.save_to_file(results.get('report', ''), str(text_file))
            self.formatter.save_json(results.get('analysis', {}), str(json_file))
            logger.info(f"[+] Patch script: {results.get('patch_script', '')}")
        
        elif mode == "opensource_verification":
            text_file = output_path / f"verification_report.txt"
            json_file = output_path / f"verification_results.json"
            verification_text = json.dumps(results.get('verification', {}), indent=2)
            self.formatter.save_to_file(verification_text, str(text_file))
            self.formatter.save_json(results, str(json_file))
        
        else:
            text_file = output_path / f"analysis_{mode}.txt"
            json_file = output_path / f"analysis_{mode}.json"
            content = self.formatter.format_results(results.get('results', []))
            self.formatter.save_to_file(content, str(text_file))
            self.formatter.save_json(results, str(json_file))


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Project Analyzer using Claude AI Models + Tanner EDA Tools')
    parser.add_argument('project_dir', help='Path to project directory to analyze')
    parser.add_argument('--mode', 
                       choices=['sequential', 'parallel', 'review', 'tanner', 'patch', 'verify'],
                       default='sequential',
                       help='Analysis mode')
    parser.add_argument('--output', default='.', help='Output directory for results')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = ProjectAnalyzer(args.config)
        
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
        elif args.mode == 'tanner':
            logger.info("[*] Running in TANNER ANALYSIS mode")
            results = analyzer.analyze_tanner_project(args.project_dir)
        elif args.mode == 'patch':
            logger.info("[*] Running in TANNER PATCH mode")
            results = analyzer.patch_tanner_project(args.project_dir)
        elif args.mode == 'verify':
            logger.info("[*] Running in OPEN-SOURCE VERIFICATION mode")
            results = analyzer.verify_with_opensource_tools(args.project_dir)
        
        # Save results
        analyzer.save_results(results, args.output)
        logger.info("[OK] Analysis complete!")
        
    except Exception as e:
        logger.error(f"[ERROR] Analysis failed: {e}")
        raise
        
        # Save results
        analyzer.save_results(results, args.output)
        logger.info("[OK] Analysis complete!")
        
    except Exception as e:
        logger.error(f"[ERROR] Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
