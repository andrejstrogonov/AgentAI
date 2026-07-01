import json
from typing import List, Dict, Any
from pathlib import Path


class ResultFormatter:
    def __init__(self):
        self.separator = "=" * 70

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Форматирование результатов в строку"""
        output = []
        output.append(f"\n{self.separator}")
        output.append("ANALYSIS RESULTS")
        output.append(self.separator)

        for i, result in enumerate(results, 1):
            output.append(f"\n[{i}] Model: {result.get('model', 'Unknown')}")
            output.append(f"    Status: {result.get('status', 'Unknown')}")
            
            if result.get('status') == 'success' and result.get('response'):
                response = result['response']
                # Ограничиваем длину вывода
                if len(response) > 500:
                    output.append(f"    Response: {response[:500]}...")
                else:
                    output.append(f"    Response: {response}")
                output.append(f"    Length: {result.get('response_length', 0)} chars")
            elif result.get('status') == 'error':
                output.append(f"    Error: {result.get('error', 'Unknown error')}")
                output.append(f"    Error Type: {result.get('error_type', 'Unknown')}")

            output.append("")

        output.append(self.separator)
        return "\n".join(output)

    def display_results(self, results: List[Dict[str, Any]]) -> None:
        """Вывод результатов в консоль"""
        output = []
        output.append(f"\n{self.separator}")
        output.append("ANALYSIS RESULTS")
        output.append(self.separator)

        for i, result in enumerate(results, 1):
            output.append(f"\n[{i}] Model: {result.get('model', 'Unknown')}")
            output.append(f"    Status: {result.get('status', 'Unknown')}")
            
            if result.get('status') == 'success' and result.get('response'):
                response = result['response']
                if len(response) > 500:
                    output.append(f"    Response: {response[:500]}...")
                else:
                    output.append(f"    Response: {response}")
                output.append(f"    Length: {result.get('response_length', 0)} chars")
            elif result.get('status') == 'error':
                output.append(f"    Error: {result.get('error', 'Unknown error')}")
                output.append(f"    Error Type: {result.get('error_type', 'Unknown')}")

            output.append("")

        output.append(self.separator)
        
        # Print with safe encoding
        for line in output:
            try:
                print(line)
            except UnicodeEncodeError:
                # Skip lines with encoding issues
                safe_line = line.encode('ascii', 'ignore').decode('ascii')
                print(safe_line)

    def format_code_review(self, review_data: Dict[str, Any]) -> str:
        """Форматирование code review"""
        output = []
        output.append(f"\n{self.separator}")
        output.append("CODE REVIEW")
        output.append(self.separator)

        if review_data.get('status') == 'error':
            output.append(f"[ERROR] {review_data.get('error', 'Unknown error')}")
        else:
            output.append("\n=== REVIEW ===")
            output.append(review_data.get('review', 'No review available'))

            output.append("\n=== SUMMARY ===")
            output.append(review_data.get('summary', 'No summary available'))

            output.append("\n=== RECOMMENDATIONS ===")
            output.append(review_data.get('recommendations', 'No recommendations available'))

        output.append("")
        output.append(self.separator)
        return "\n".join(output)

    def display_code_review(self, review_data: Dict[str, Any]) -> None:
        """Вывод code review в консоль"""
        formatted = self.format_code_review(review_data)
        
        # Print with safe encoding
        for line in formatted.split('\n'):
            try:
                print(line)
            except UnicodeEncodeError:
                safe_line = line.encode('ascii', 'ignore').decode('ascii')
                print(safe_line)

    def save_to_file(self, content: str, filename: str) -> None:
        """Сохранение результатов в файл"""
        try:
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Results saved to: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save results: {e}")

    def save_json(self, data: Any, filename: str) -> None:
        """Сохранение результатов в JSON"""
        try:
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[OK] JSON saved to: {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save JSON: {e}")

    def format_summary(self, results: List[Dict[str, Any]]) -> str:
        """Форматирование сводки по результатам"""
        success_count = sum(1 for r in results if r.get('status') == 'success')
        error_count = len(results) - success_count
        
        summary = []
        summary.append(f"\n{self.separator}")
        summary.append("SUMMARY")
        summary.append(self.separator)
        summary.append(f"\nTotal models processed: {len(results)}")
        summary.append(f"Successful: {success_count}")
        summary.append(f"Failed: {error_count}")
        summary.append("")
        
        for result in results:
            status_icon = "[OK]" if result.get('status') == 'success' else "[ERROR]"
            summary.append(f"{status_icon} {result.get('model', 'Unknown')}")
        
        summary.append(self.separator)
        return "\n".join(summary)
