from ResultFormatter import ResultFormatter
from ModelProcessor import ModelProcessor


class UIInput:
    def __init__(self):
        self.formatter = ResultFormatter()

    def get_project_analysis_prompts(self) -> dict:
        """Получить промпты для анализа проекта"""
        system_prompt = (
            "You are an expert Python developer, software architect, and code analyst. "
            "Your task is to analyze project code, identify errors and issues, "
            "and provide comprehensive recommendations for improvement."
        )

        user_prompt_template = (
            "Please analyze the following project and provide:\n"
            "1. List of all errors and issues found\n"
            "2. Code quality assessment\n"
            "3. Recommendations for improvement\n"
            "4. Priority list of fixes needed\n\n"
            "PROJECT CODE:\n{project_data}"
        )

        return {
            "system": system_prompt,
            "user_template": user_prompt_template
        }

    def get_code_review_prompts(self) -> dict:
        """Получить промпты для code review"""
        system_prompt = (
            "You are a senior code reviewer with expertise in Python development, "
            "software architecture, and best practices. "
            "Provide constructive, detailed feedback on the code."
        )

        user_prompt_template = (
            "Please provide a comprehensive code review for the following project:\n"
            "1. Code style and formatting issues\n"
            "2. Performance concerns\n"
            "3. Security vulnerabilities\n"
            "4. Architecture and design patterns\n"
            "5. Testing coverage and recommendations\n\n"
            "PROJECT CODE:\n{project_data}"
        )

        return {
            "system": system_prompt,
            "user_template": user_prompt_template
        }

    def display_analysis_results(self, results: list) -> None:
        """Отображение результатов анализа"""
        self.formatter.display_results(results)

    def display_code_review(self, review_data: dict) -> None:
        """Отображение code review"""
        self.formatter.display_code_review(review_data)

    def save_analysis_results(self, results: list, filename: str = "analysis_results.txt") -> None:
        """Сохранение результатов анализа"""
        content = self.formatter.format_results(results)
        self.formatter.save_to_file(content, filename)

    def save_code_review(self, review_data: dict, filename: str = "code_review.txt") -> None:
        """Сохранение code review"""
        content = self.formatter.format_code_review(review_data)
        self.formatter.save_to_file(content, filename)