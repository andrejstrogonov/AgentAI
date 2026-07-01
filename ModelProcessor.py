import asyncio
import logging
import time
from typing import List, Dict, Any

from anthropic import AsyncAnthropic, Anthropic


class ModelProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.model_list = config.get("models", [])
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.2)

        if not self.api_key:
            raise ValueError("API key not provided in config")
        if not self.model_list:
            raise ValueError("Model list is empty")

        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.async_client = AsyncAnthropic(**client_kwargs)
        self.sync_client = Anthropic(**client_kwargs)
        self.logger = logging.getLogger(__name__)

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

    async def process_with_models_parallel(self, project_data: str) -> List[Dict[str, Any]]:
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

            return processed_results

        except Exception as e:
            self.logger.error(f"Error in parallel processing: {str(e)}")
            raise

    async def _process_single_model_async(self, model_name: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Обработка одной модели в async режиме"""
        try:
            message = await self.async_client.messages.create(
                model=model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=prompts["system"],
                messages=[
                    {
                        "role": "user",
                        "content": prompts["user"]
                    }
                ]
            )

            response_text = message.content[0].text if message.content else ""

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

    def process_with_models_sequential(self, project_data: str) -> List[Dict[str, Any]]:
        """Обработка через несколько моделей последовательно (sync)"""
        results = []
        prompts = self._build_unified_prompt(project_data)

        for model_name in self.model_list:
            try:
                message = self.sync_client.messages.create(
                    model=model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=prompts["system"],
                    messages=[
                        {
                            "role": "user",
                            "content": prompts["user"]
                        }
                    ]
                )

                result = {
                    "model": model_name,
                    "response": message.content[0].text if message.content else "",
                    "status": "success",
                    "response_length": len(message.content[0].text) if message.content else 0
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

        return results

    def generate_code_review(self, project_data: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Генерация code review на основе результатов всех моделей"""
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

        try:
            # Используем первую модель для code review
            review_model = self.model_list[0] if self.model_list else "claude-3-sonnet"
            
            review_message = self.sync_client.messages.create(
                model=review_model,
                max_tokens=2048,
                temperature=0.3,
                system="You are a senior code reviewer. Provide detailed, actionable feedback.",
                messages=[
                    {
                        "role": "user",
                        "content": review_prompt
                    }
                ]
            )

            return {
                "review": review_message.content[0].text if review_message.content else "",
                "summary": self._generate_summary(results),
                "recommendations": self._generate_recommendations(results),
                "status": "success"
            }

        except Exception as e:
            return {
                "review": f"Error generating code review: {str(e)}",
                "summary": "Review generation failed",
                "recommendations": "Unable to generate recommendations",
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

    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> str:
        """Генерация рекомендаций на основе результатов"""
        recommendations = []

        error_results = [r for r in results if r['status'] == 'error']
        if error_results:
            recommendations.append("[!] Check error results from models")

        success_results = [r for r in results if r['status'] == 'success']
        if len(success_results) > 1:
            recommendations.append("[i] Compare responses from different models")

        if not recommendations:
            recommendations.append("[OK] All results are positive")

        return "\n".join(recommendations)