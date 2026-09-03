import asyncio
import logging
from typing import List, Dict, Any
from pathlib import Path
import os

from anthropic import AsyncAnthropic, Anthropic

from QualityEngine import QualityEngine


class ModelProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}

        # If api_key not provided in config, attempt to load from .env files
        if not self.config.get('api_key'):
            for base in (Path.cwd(), Path(__file__).resolve().parent):
                dotenv = base / '.env'
                if dotenv.exists():
                    try:
                        with open(dotenv, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if not line or line.startswith('#') or '=' not in line:
                                    continue
                                k, v = line.split('=', 1)
                                k = k.strip(); v = v.strip().strip('"').strip("'")
                                if k and v and k not in os.environ:
                                    os.environ[k] = v
                    except Exception as e:
                        logging.getLogger(__name__).warning(f"Failed to read .env {dotenv}: {e}")

        self.api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = self.config.get("base_url")
        self.model_list = self.config.get("models", [])
        self.max_tokens = self.config.get("max_tokens", 4096)
        self.temperature = self.config.get("temperature", 0.2)

        if not self.api_key:
            raise ValueError("API key not provided in config or environment (.env)")
        if not self.model_list:
            raise ValueError("Model list is empty")

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.async_client = AsyncAnthropic(**client_kwargs)
        self.sync_client = Anthropic(**client_kwargs)
        self.logger = logging.getLogger(__name__)
        self.quality_engine = QualityEngine()

    @staticmethod
    def _build_unified_prompt(project_data: str) -> Dict[str, str]:
        pass

    def _extract_message_text(self, message) -> str:
        """Normalize various SDK response formats into plain text."""
        if not message:
            return ""
        try:
            # Common pattern: message.content -> list
            content = getattr(message, 'content', None)
            if content:
                first = content[0]
                if isinstance(first, dict):
                    # Some SDKs return {'text': '...'}
                    return first.get('text') or first.get('content') or first.get('message') or str(first)
                else:
                    if hasattr(first, 'text'):
                        return getattr(first, 'text') or ''
                    if hasattr(first, 'content'):
                        return getattr(first, 'content') or ''
            # Some SDKs return message.text directly
            if hasattr(message, 'text'):
                return getattr(message, 'text') or ''
            # dict-like message
            if isinstance(message, dict):
                return message.get('text') or message.get('output') or message.get('response') or str(message)
            # fallback to str
            return str(message)
        except Exception:
            try:
                return str(message)
            except Exception:
                return ""

    @staticmethod
    def _build_unified_prompt(project_data: str) -> Dict[str, str]:
        """Построение единого промпта (объединение system + user в один контекст)"""
        system_prompt = (
            "You are an expert in Python development, software architecture, and code analysis. "
            "Your task is to analyze the provided project code, identify errors and issues, "
            "and provide recommendations for improvement."
        )

        user_prompt = (
            "Please analyze the following project code, identify all errors and issues, "
            "and provide recommendations for fixes and improvements.\n\n"
            f"PROJECT CODE:\n{project_data}"
        )

        return {
            "system": system_prompt,
            "user": user_prompt
        }

    async def process_with_models_parallel(self, project_data: str) -> Dict[str, Any]:
        """Обработка через несколько моделей параллельно (async)"""
        if not self.model_list:
            raise ValueError("No models specified")

        prompts = self._build_unified_prompt(project_data)

        tasks = [
            self._process_single_model_async(model_name, prompts)
            for model_name in self.model_list
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "model": self.model_list[i],
                        "response": None,
                        "status": "error",
                        "error": str(result),
                        "error_type": type(result).__name__
                    })
                else:
                    processed_results.append(result)

            mutation_testing = self.run_mutation_testing(project_data, processed_results)
            genetic_improvement = self.run_genetic_algorithm(project_data, processed_results)

            return {
                "results": processed_results,
                "model_results": processed_results,
                "mutation_testing": mutation_testing,
                "genetic_improvement": genetic_improvement
            }

        except Exception as e:
            self.logger.error(f"Error in parallel processing: {str(e)}")
            raise

    async def _process_single_model_async(self, model_name: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Обработка одной модели в async режиме with robust SDK compatibility and response normalization"""
        try:
            user_message = {"role": "user", "content": prompts.get("user", "")}
            system_text = prompts.get("system")

            # Try call signatures in preferred order for compatibility with proxy and SDKs
            # 1) top-level system param (proxy expects this)
            try:
                message = await self.async_client.messages.create(
                    model=model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_text,
                    messages=[user_message],
                )
            except TypeError:
                # 2) system as a message (some SDKs accept this)
                try:
                    message = await self.async_client.messages.create(
                        model=model_name,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        messages=([{"role": "system", "content": system_text}] if system_text else []) + [user_message],
                    )
                except TypeError:
                    # 3) without temperature/system fields
                    try:
                        message = await self.async_client.messages.create(
                            model=model_name,
                            max_tokens=self.max_tokens,
                            messages=([{"role": "system", "content": system_text}] if system_text else []) + [user_message],
                        )
                    except TypeError:
                        # Last resort: try completions endpoint if available
                        if hasattr(self.async_client, 'completions') and hasattr(self.async_client.completions, 'create'):
                            full_prompt = (system_text or '') + '\n' + (prompts.get('user',''))
                            full_prompt = full_prompt.strip()
                            message = await self.async_client.completions.create(model=model_name, prompt=full_prompt, max_tokens=self.max_tokens)
                        else:
                            raise

            response_text = self._extract_message_text(message)

            return {
                "model": model_name,
                "response": response_text,
                "status": "success",
                "response_length": len(response_text)
            }

        except Exception as e:
            return {
                "model": model_name,
                "response": None,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def process_with_models_sequential(self, project_data: str) -> Dict[str, Any]:
        """Обработка через несколько моделей последовательно (sync) with SDK compatibility"""
        results = []
        prompts = self._build_unified_prompt(project_data)

        for model_name in self.model_list:
            try:
                messages = []
                if prompts.get("system"):
                    messages.append({"role": "system", "content": prompts["system"]})
                messages.append({"role": "user", "content": prompts["user"]})

                user_message = {"role": "user", "content": prompts.get("user", "")}
                system_text = prompts.get("system")

                try:
                    message = self.sync_client.messages.create(
                        model=model_name,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system=system_text,
                        messages=[user_message],
                    )
                except TypeError:
                    try:
                        message = self.sync_client.messages.create(
                            model=model_name,
                            max_tokens=self.max_tokens,
                            temperature=self.temperature,
                            messages=([{"role": "system", "content": system_text}] if system_text else []) + [user_message],
                        )
                    except TypeError:
                        try:
                            message = self.sync_client.messages.create(
                                model=model_name,
                                max_tokens=self.max_tokens,
                                messages=([{"role": "system", "content": system_text}] if system_text else []) + [user_message],
                            )
                        except TypeError:
                            if hasattr(self.sync_client, 'completions') and hasattr(self.sync_client.completions, 'create'):
                                full_prompt = (system_text or '') + '\n' + (prompts.get('user',''))
                                full_prompt = full_prompt.strip()
                                message = self.sync_client.completions.create(model=model_name, prompt=full_prompt, max_tokens=self.max_tokens)
                            else:
                                raise

                response_text = self._extract_message_text(message)

                result = {
                    "model": model_name,
                    "response": response_text,
                    "status": "success",
                    "response_length": len(response_text)
                }
                results.append(result)

            except Exception as e:
                result = {
                    "model": model_name,
                    "response": None,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                results.append(result)

        mutation_testing = self.run_mutation_testing(project_data, results)
        genetic_improvement = self.run_genetic_algorithm(project_data, results)

        return {
            "results": results,
            "model_results": results,
            "mutation_testing": mutation_testing,
            "genetic_improvement": genetic_improvement
        }

    def generate_code_review(
        self,
        project_data: str,
        results: List[Dict[str, Any]],
        mutation_testing: Dict[str, Any] = None,
        genetic_improvement: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Генерация code review на основе результатов всех моделей"""
        mutation_testing = mutation_testing or self.run_mutation_testing(project_data, results)
        genetic_improvement = genetic_improvement or self.run_genetic_algorithm(project_data, results)
        review_prompt = (
            "You are an expert code reviewer. Analyze the project and the following model outputs "
            "to provide a comprehensive code review.\n\n"
            "PROJECT CODE:\n"
            f"{project_data[:3000]}\n\n"  # Ограничиваем для контекста
            "MODEL ANALYSIS RESULTS:\n"
        )

        for result in results:
            review_prompt += f"\n--- Model: {result['model']} ---\n"
            review_prompt += f"Status: {result['status']}\n"
            if result['status'] == 'success' and result['response']:
                review_prompt += f"Analysis: {result['response'][:500]}\n"
            elif result['status'] == 'error':
                review_prompt += f"Error: {result['error']}\n"

        if mutation_testing:
            review_prompt += "\nMUTATION TESTING SUMMARY:\n"
            review_prompt += mutation_testing.get("mutation_summary", "No mutation summary available")
            review_prompt += "\nMUTATION TESTING DETAILS:\n"
            review_prompt += mutation_testing.get("mutation_findings", "No mutation findings available")

        if genetic_improvement:
            review_prompt += "\nGENETIC IMPROVEMENT SUMMARY:\n"
            review_prompt += genetic_improvement.get("generation_summary", "No genetic improvement summary available")
            review_prompt += "\nGENETIC IMPROVEMENT RESULT:\n"
            review_prompt += genetic_improvement.get("best_solution", "No genetic improvement result available")

        try:
            # Используем первую модель для code review
            review_model = self.model_list[0] if self.model_list else "claude-3-sonnet"
            
            user_message = {"role": "user", "content": review_prompt}
            system_text = "You are a senior code reviewer. Provide detailed, actionable feedback."

            try:
                try:
                    review_message = self.sync_client.messages.create(
                        model=review_model,
                        max_tokens=2048,
                        temperature=0.3,
                        system=system_text,
                        messages=[user_message],
                    )
                except TypeError:
                    review_message = self.sync_client.messages.create(
                        model=review_model,
                        max_tokens=2048,
                        temperature=0.3,
                        messages=[{"role": "system", "content": system_text}, user_message],
                    )
            except TypeError:
                if hasattr(self.sync_client, 'completions') and hasattr(self.sync_client.completions, 'create'):
                    review_message = self.sync_client.completions.create(model=review_model, prompt=review_prompt, max_tokens=2048)
                else:
                    raise

            return {
                "review": self._extract_message_text(review_message),
                "summary": self._generate_summary(results),
                "recommendations": self._generate_recommendations(results, genetic_improvement),
                "mutation_testing": mutation_testing,
                "genetic_improvement": genetic_improvement,
                "status": "success"
            }

        except Exception as e:
            return {
                "review": f"Error generating code review: {str(e)}",
                "summary": "Review generation failed",
                "recommendations": self._generate_recommendations(results, genetic_improvement),
                "mutation_testing": mutation_testing,
                "genetic_improvement": genetic_improvement,
                "status": "error",
                "error": str(e)
            }

    def run_mutation_testing(self, project_data: str, results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run deterministic local mutation analysis."""
        # Use local QualityEngine deterministic mutation testing
        return self.quality_engine.mutation_testing(project_data)
        prompt = (
            "You are an expert in software quality and mutation testing. "
            "Analyze the project and suggest a small set of targeted code mutations that would "
            "reveal fragile logic, hidden bugs, or missing error handling. For each mutation, explain "
            "why it is useful and how it would impact the code. Then provide a brief recommendation "
            "for hardening the code against these issues.\n\n"
            "PROJECT CODE:\n"
            f"{project_data[:3000]}\n\n"
        )

        if results:
            prompt += "MODEL ANALYSIS RESULTS:\n"
            for result in results:
                prompt += f"- {result['model']} ({result['status']}): {result.get('response', '')[:200]}\n"

        try:
            mutation_message = self.sync_client.messages.create(
                model=self.model_list[0] if self.model_list else "claude-3-sonnet",
                max_tokens=1600,
                temperature=0.25,
                system="You are a mutation testing expert. Provide concise, actionable analysis.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            mutation_response = mutation_message.content[0].text if mutation_message.content else ""
            return {
                "mutation_summary": "Mutation testing analysis completed.",
                "mutation_findings": mutation_response,
                "status": "success"
            }
        except Exception as e:
            return {
                "mutation_summary": "Mutation testing failed.",
                "mutation_findings": str(e),
                "status": "error",
                "error": str(e)
            }

    def run_genetic_algorithm(self, project_data: str, results: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evolve local, actionable recommendations from project signals."""
        # Use local QualityEngine genetic improvements
        return self.quality_engine.genetic_improvement(project_data, results)
        prompt = (
            "You are an expert in genetic algorithms and software optimization. "
            "Using the project code as input, simulate a standard genetic algorithm workflow: "
            "generate an initial population of improved code variants, evaluate their fitness based on "
            "readability, maintainability, performance, and correctness, then apply selection, crossover, "
            "and mutation to produce a better final code suggestion. Present the best candidate and "
            "explain why it is superior.\n\n"
            "PROJECT CODE:\n"
            f"{project_data[:3000]}\n\n"
        )

        if results:
            prompt += "MODEL ANALYSIS RESULTS:\n"
            for result in results:
                prompt += f"- {result['model']} ({result['status']}): {result.get('response', '')[:200]}\n"

        try:
            genetic_message = self.sync_client.messages.create(
                model=self.model_list[0] if self.model_list else "claude-3-sonnet",
                max_tokens=1800,
                temperature=0.25,
                system="You are a genetic algorithm expert for code improvement.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            genetic_response = genetic_message.content[0].text if genetic_message.content else ""
            return {
                "generation_summary": "Genetic improvement simulation completed.",
                "best_solution": genetic_response,
                "status": "success"
            }
        except Exception as e:
            return {
                "generation_summary": "Genetic improvement failed.",
                "best_solution": str(e),
                "status": "error",
                "error": str(e)
            }

    def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """Генерация сводки по результатам"""
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = len(results) - success_count

        summary = f"Processed {len(results)} models: {success_count} successful, {error_count} errors\n\n"

        for result in results:
            status_icon = "[OK]" if result['status'] == 'success' else "[ERROR]"
            summary += f"{status_icon} {result['model']}: "
            if result['status'] == 'success':
                summary += f"OK ({result.get('response_length', 0)} chars)\n"
            else:
                summary += f"{result['error'][:60]}\n"

        return summary

    def _generate_recommendations(
        self, results: List[Dict[str, Any]], genetic_improvement: Dict[str, Any] = None
    ) -> str:
        """Генерация рекомендаций на основе результатов"""
        recommendations = []

        error_results = [r for r in results if r['status'] == 'error']
        if error_results:
            recommendations.append("[!] Check error results from models")

        success_results = [r for r in results if r['status'] == 'success']
        if len(success_results) > 1:
            recommendations.append("[i] Compare responses from different models")

        if genetic_improvement:
            for recommendation in genetic_improvement.get("recommendations", [])[:3]:
                recommendations.append(f"[GA] {recommendation}")

        if not recommendations:
            recommendations.append("[OK] All results are positive")

        return "\n".join(recommendations)