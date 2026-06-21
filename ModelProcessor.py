import asyncio
import logging
from typing import List, Dict, Any

from anthropic import AsyncAnthropic, Anthropic


class ModelProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url")
        self.model_list = config.get("models", [])

        # Инициализация клиентов
        self.async_client = AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.sync_client = Anthropic(
            api_key=self.api_key,
            base_url=self.base_url
        )

        self.logger = logging.getLogger(__name__)

    async def process_with_models_parallel(self, project_data: str) -> List[Dict[str, Any]]:
        """Обработка через несколько моделей параллельно с одним API ключом"""
        if not self.model_list:
            raise ValueError("Не указаны модели для обработки")

        results = []

        # Создаем системный промпт один раз
        system_prompt = (
            "Ты — эксперт в области разработки на Scala, Chisel, FIRRTL, Python, Tcl и проектирования цифровой аппаратуры "
            "на Verilog/VHDL для Intel Quartus Prime. Твоя задача — проанализировать предоставленный "
            "проект генератора, найти ошибки и сделать его полностью запускаемым."
        )

        user_query = (
            "Все уже сделано так, как ты говоришь, продолжи генерировать до успешного исполнения проекта.\n\n"
            f"Проект: {project_data}"
        )

        # Создаем задачи для параллельного выполнения
        tasks = [
            self._process_single_model(model_name, system_prompt, user_query)
            for model_name in self.model_list
        ]

        # Выполняем все задачи параллельно
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Обрабатываем результаты
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "model": self.model_list[i],
                        "response": None,
                        "status": "error",
                        "error": str(result),
                        "error_type": type(result).__name__,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                else:
                    processed_results.append(result)

            return processed_results

        except Exception as e:
            self.logger.error(f"Ошибка при параллельной обработке: {str(e)}")
            raise

    async def _process_single_model(self, model_name: str, system_prompt: str, user_query: str) -> Dict[str, Any]:
        """Обработка одной модели"""
        try:
            # Создаем сообщение для модели
            message = await self.async_client.messages.create(
                model=model_name,
                max_tokens=4096,
                temperature=0.2,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_query
                    }
                ]
            )

            # Сохраняем результат
            response_text = message.content[0].text if message.content else ""

            result = {
                "model": model_name,
                "response": response_text,
                "status": "success",
                "response_length": len(response_text),
                "timestamp": asyncio.get_event_loop().time()
            }

            return result

        except Exception as e:
            # Если произошла ошибка, сохраняем информацию об ошибке
            result = {
                "model": model_name,
                "response": None,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": asyncio.get_event_loop().time()
            }
            return result

    def _process_with_models_sequentially(self, project_data: str) -> List[Dict[str, Any]]:
        """Обработка через несколько моделей последовательно с одним API ключом (оригинальная версия)"""
        results = []
        # Создаем системный промпт один раз
        system_prompt = (
            "Ты — эксперт в области разработки на Scala, Chisel, FIRRTL, Python, Tcl и проектирования цифровой аппаратуры "
            "на Verilog/VHDL для Intel Quartus Prime. Твоя задача — проанализировать предоставленный "
            "проект генератора, найти ошибки и сделать его полностью запускаемым."
        )

        user_query = (
            "Все уже сделано так, как ты говоришь, продолжи генерировать до успешного исполнения проекта.\n\n"
            f"Проект: {project_data}"
        )

        # Обрабатываем каждый запрос через разные модели
        for model_name in self.model_list:
            try:
                # Создаем сообщение для модели
                message = self.client.messages.create(
                    model=model_name,
                    max_tokens=4096,
                    temperature=0.2,
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": user_query
                        }
                    ]
                )

                # Сохраняем результат
                result = {
                    "model": model_name,
                    "response": message.content[0].text,
                    "status": "success",
                    "response_length": len(message.content[0].text) if message.content else 0
                }
                results.append(result)

            except Exception as e:
                # Если произошла ошибка, сохраняем информацию об ошибке
                result = {
                    "model": model_name,
                    "response": None,
                    "status": "error",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
                results.append(result)

        return results

    def generate_code_review(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Генерация code review на основе результатов всех моделей"""
        review_prompt = (
            "Проанализируй результаты обработки проекта разными моделями и создай comprehensive code review.\n\n"
            "Результаты:\n"
        )

        for result in results:
            review_prompt += f"Модель: {result['model']}\n"
            review_prompt += f"Статус: {result['status']}\n"
            if result['status'] == 'success' and result['response']:
                review_prompt += f"Ответ: {result['response'][:200]}...\n"  # Ограничиваем длину
            elif result['status'] == 'error':
                review_prompt += f"Ошибка: {result['error']}\n"
            review_prompt += "\n"

        # Создаем запрос для code review
        try:
            review_message = self.client.messages.create(
                model="claude-3-5-sonnet",  # Используем более мощную модель для code review
                max_tokens=2048,
                temperature=0.3,
                system="Ты — эксперт по code review. Проанализируй результаты и предоставь структурированную обратную связь.",
                messages=[
                    {
                        "role": "user",
                        "content": review_prompt
                    }
                ]
            )

            return {
                "review": review_message.content[0].text,
                "summary": self.generate_summary(results),
                "recommendations": self.generate_recommendations(results)
            }

        except Exception as e:
            return {
                "review": f"Ошибка при генерации code review: {str(e)}",
                "summary": "Не удалось сгенерировать сводку",
                "recommendations": "Не удалось сгенерировать рекомендации"
            }

    def generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """Генерация сводки по результатам"""
        success_count = sum(1 for r in results if r['status'] == 'success')
        error_count = len(results) - success_count

        summary = f"Обработано {len(results)} моделей: {success_count} успешных, {error_count} с ошибками\n\n"

        for result in results:
            if result['status'] == 'success':
                summary += f"✅ {result['model']}: Успешно\n"
            else:
                summary += f"❌ {result['model']}: Ошибка - {result['error'][:100]}...\n"

        return summary

    def generate_recommendations(self, results: List[Dict[str, Any]]) -> str:
        """Генерация рекомендаций на основе результатов"""
        recommendations = []

        # Проверяем наличие ошибок
        error_results = [r for r in results if r['status'] == 'error']
        if error_results:
            recommendations.append("⚠️ Обратите внимание на ошибки в результатах моделей")

        # Проверяем一致性
        success_results = [r for r in results if r['status'] == 'success']
        if len(success_results) > 1:
            # Можно добавить логику для сравнения ответов
            recommendations.append("📊 Проверьте согласованность ответов от разных моделей")

        return "\n".join(recommendations) if recommendations else "✅ Все результаты положительные"


# Пример использования
async def main():
    # Инициализация
    processor = ModelProcessor(client, ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"])

    # Параллельная обработка
    project_data = "Ваш проект здесь"
    results = await processor.process_with_models_parallel(project_data)

    # Генерация code review
    review = processor.generate_code_review(results)

    print("Результаты:")
    for result in results:
        print(f"Модель: {result['model']}, Статус: {result['status']}")

    print("\nCode Review:")
    print(review['review'])


# Если используете синхронный код
def process_project_sync(project_data: str, client, model_list: List[str]) -> Dict[str, Any]:
    """Синхронная версия для использования в синхронном коде"""
    processor = ModelProcessor(client, model_list)

    # Параллельная обработка
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        results = loop.run_until_complete(processor.process_with_models_parallel(project_data))

        # Генерация code review
        review = processor.generate_code_review(results)

        return {
            "results": results,
            "review": review
        }
    finally:
        loop.close()


# Использование:
# async_result = await processor.process_with_models_parallel(project_data)
# review_result = processor.generate_code_review(async_result)

# Для синхронного вызова:
# sync_result = process_project_sync(project_data, client, model_list)


client_1 = anthropic.Anthropic(
    api_key="sk-LgqiRR4lfipwfWA6vrs4xJvZOiEzYpsW",
    base_url="https://api.proxyapi.ru/anthropic",
)

message_1 = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=20000,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Проанализируй проект https://github.com/andrejstrogonov/processor/tree/quartus-generator и предложи изменения для исправления ошибок и сделать его запускаемым. Опиши пошагово, что нужно изменить, чтобы проект заработал."
                }
            ]
        }
    ]
)

print(message.content[0].text)