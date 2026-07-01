import os
import json
import anthropic

PROJECT_DIR = r"C:\Users\strog\PycharmProject\AgentAI"
OUTPUT_FILE = os.path.join(PROJECT_DIR, "project_context.txt")

VALID_EXTENSIONS = {
    '.py', '.v', '.sv', '.vhd', '.vhdl', '.tcl',
    '.md', '.json', '.yaml', '.yml', '.ini', '.cfg'
}

IGNORE_DIRS = {
    '.git', '.idea', '__pycache__', 'venv', '.venv',
    'db', 'incremental_db', 'simulation', 'greybox_tmp', '.qodo'
}


def generate_tree(current_dir, indent=""):
    """Рекурсивно строит дерево проекта для визуализации структуры."""
    tree_str = ""
    try:
        items = sorted(os.listdir(current_dir))
    except PermissionError:
        return ""

    for item in items:
        if item in IGNORE_DIRS:
            continue
        path = os.path.join(current_dir, item)
        if os.path.isdir(path):
            tree_str += f"{indent}├── [{item}/]\n"
            tree_str += generate_tree(path, indent + "│   ")
        else:
            ext = os.path.splitext(item)[1].lower()
            if ext in VALID_EXTENSIONS:
                tree_str += f"{indent}├── {item}\n"
    return tree_str


def collect_context():
    """Сканирует весь проект и сохраняет контекст в строку и файл."""
    print(f"[*] Сканирование: {PROJECT_DIR}")

    if not os.path.exists(PROJECT_DIR):
        raise FileNotFoundError(f"Путь не существует: {PROJECT_DIR}")

    context_chunks = []
    context_chunks.append("=== АНАЛИЗ ПРОЕКТА AgentAI ===\n\n")
    context_chunks.append("=== СТРУКТУРА ПРОЕКТА ===\n")
    context_chunks.append(f"[{os.path.basename(PROJECT_DIR)}/]\n")
    context_chunks.append(generate_tree(PROJECT_DIR))
    context_chunks.append("\n" + "=" * 40 + "\n\n")
    context_chunks.append("=== СОДЕРЖИМОЕ ФАЙЛОВ ===\n\n")

    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in sorted(files):
            ext = os.path.splitext(file)[1].lower()
            if ext not in VALID_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, PROJECT_DIR)

            if full_path == OUTPUT_FILE:
                continue

            context_chunks.append(f"--- НАЧАЛО: {rel_path} ---\n")
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    context_chunks.append(f.read())
            except Exception as e:
                context_chunks.append(f"[Ошибка: {str(e)}]\n")
            context_chunks.append(f"\n--- КОНЕЦ: {rel_path} ---\n\n")

    full_context = "".join(context_chunks)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(full_context)

    print(f"[OK] Контекст сохранен: {OUTPUT_FILE}")
    return full_context


def load_config():
    """Загружает конфиг с API ключом."""
    config_path = os.path.join(PROJECT_DIR, "config.json")
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"[!] Не удалось загрузить config.json: {e}")
        return {}


def main():
    """Основная функция - собирает контекст и анализирует проект через единый промпт."""
    print("[*] Запуск анализа проекта AgentAI...\n")
    
    project_data = collect_context()
    
    config = load_config()
    api_key = config.get("api_key", "")
    base_url = config.get("base_url", "https://api.proxyapi.ru/anthropic")
    
    if not api_key:
        print("[!] API ключ не найден в config.json")
        return
    
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=base_url,
    )
    
    # ЕДИНЫЙ ОБЪЕДИНЁННЫЙ ПРОМПТ (system + user в одном контексте)
    unified_prompt = f"""Ты — эксперт в разработке на Python и архитектуре проектов.

ЗАДАЧА:
1. Проанализируй структуру и код проекта AgentAI
2. Найди все ошибки и проблемы в коде
3. Определи основные проблемы:
   - Дублирование функций
   - Неправильные пути к файлам
   - Разделение логики
   - Неверная структура промптов
4. Предложи исправления для всех проблем

КОНТЕКСТ ПРОЕКТА:

{project_data}

ТРЕБОВАНИЯ К ОТВЕТУ:
- Кратко опиши найденные ошибки
- Предложи исправленный main.py
- Убедись, что все логика объединена в одну функцию main()
- system_prompt и user_query должны быть объединены в единый промпт"""

    print("[*] Отправка на анализ (claude-sonnet-4-6)...\n")
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": unified_prompt
                }
            ]
        )
        
        response_text = message.content[0].text
        print("=" * 70)
        print("[+] АНАЛИЗ И РЕКОМЕНДАЦИИ:")
        print("=" * 70)
        
        # Сохраняем результат с правильной кодировкой
        result_file = os.path.join(PROJECT_DIR, "analysis_result.txt")
        with open(result_file, "w", encoding="utf-8") as f:
            f.write("АНАЛИЗ ПРОЕКТА AGENTAI\n")
            f.write("=" * 70 + "\n")
            f.write(response_text)
        
        # Выводим только текст без проблемных символов
        lines = response_text.split('\n')
        for line in lines[:50]:  # Первые 50 строк
            try:
                print(line)
            except UnicodeEncodeError:
                print("[TEXT] (пропущена строка с проблемными символами)")
        
        print("\n[OK] Полный результат сохранен: " + result_file)
        
    except Exception as e:
        print(f"[!] Ошибка при отправке запроса: {e}")


if __name__ == "__main__":
    main()