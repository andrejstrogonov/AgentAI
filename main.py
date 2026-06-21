import os
import anthropic

# 1. ТОЧНЫЙ ПУТЬ К ВАШЕМУ ПРОЕКТУ
# Используем сырую строку (буква r перед кавычками), чтобы Windows-слэши не ломались
PROJECT_DIR = r"C:\Users\strog\IdeaProjects\processor"
OUTPUT_FILE = os.path.join(PROJECT_DIR, "project_context.txt")

# Расширения файлов, которые нужно проанализировать
VALID_EXTENSIONS = {
    '.py', '.v', '.sv', '.vhd', '.vhdl', '.tcl',
    '.md', '.json', '.yaml', '.yml', '.ini', '.cfg'
}

# Папки, которые нужно пропустить, чтобы не забивать лимиты нейросети мусором
IGNORE_DIRS = {
    '.git', '.idea', '__pycache__', 'venv', '.venv',
    'db', 'incremental_db', 'simulation', 'greybox_tmp'
}

MODEL_LIST = [
    {"name": "claude-sonnet-4-6", "model": "claude-sonnet-4-6"},
    {"name": "mistral-large-latest", "model": "mistral-large-latest"},
    # Добавьте любые другие модели
]
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
    print(f"Сканирование всей директории проекта: {PROJECT_DIR}")

    if not os.path.exists(PROJECT_DIR):
        raise FileNotFoundError(f"Указанный путь не существует: {PROJECT_DIR}. Проверьте правильность пути!")

    context_chunks = []

    # 1. Заголовок и метаданные
    context_chunks.append("=== АНАЛИЗ ПРОЕКТА QUARTUS GENERATOR ===\n\n")
    context_chunks.append("ОКРУЖЕНИЕ И КОНТЕКСТ:\n")
    context_chunks.append("- Инструмент: Intel Quartus Prime\n\n")

    # 2. Добавление дерева структуры
    context_chunks.append("=== СТРУКТУРА ПРОЕКТА ===\n")
    context_chunks.append(f"[{os.path.basename(PROJECT_DIR)}/]\n")
    context_chunks.append(generate_tree(PROJECT_DIR))
    context_chunks.append("\n" + "=" * 40 + "\n\n")

    # 3. Добавление содержимого файлов
    context_chunks.append("=== СОДЕРЖИМОЕ ФАЙЛОВ ===\n\n")

    for root, dirs, files in os.walk(PROJECT_DIR):
        # Исключаем ненужные папки из обхода на лету
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in sorted(files):
            ext = os.path.splitext(file)[1].lower()
            if ext not in VALID_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, PROJECT_DIR)

            if full_path == OUTPUT_FILE:
                continue

            context_chunks.append(f"--- НАЧАЛО ФАЙЛА: {rel_path} ---\n")
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    context_chunks.append(f.read())
            except Exception as e:
                context_chunks.append(f"[Ошибка чтения файла: {str(e)}]\n")
            context_chunks.append(f"\n--- КОНЕЦ ФАЙЛА: {rel_path} ---\n\n")

    full_context = "".join(context_chunks)

    # Дублируем контекст в файл на диске для надежности
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(full_context)

    print(f"Успешно! Снапшот проекта сохранен локально в: {OUTPUT_FILE}")
    return full_context

def process_with_models(project_data, client):
    """Обрабатывает проект через несколько моделей и собирает результаты."""
    results = []

    for model_config in MODEL_LIST:
        model_name = model_config["name"]
        model_id = model_config["model"]

        print(f"\n=== ЗАПУСК МОДЕЛИ: {model_name} ===")

        system_prompt = (
            "Ты — эксперт в области разработки на Scala, Chisel, FIRRTL, Python, Tcl и проектирования цифровой аппаратуры "
            "на Verilog/VHDL для Intel Quartus Prime. Твоя задача — проанализировать предоставленный "
            "проект генератора, найти ошибки и сделать его полностью запускаемым."
        )

        user_query = (
            "Все уже сделано так, как ты говоришь, продолжи генерировать до успешного исполнения проекта.\n\n"
            f"{project_data}"
        )

        try:
            message = client.messages.create(
                model=model_id,
                max_tokens=4000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_query
                    }
                ]
            )

            result_text = message.content[0].text
            results.append({
                "model": model_name,
                "response": result_text
            })
            print(f"[✓] Модель {model_name} завершена.")

        except Exception as e:
            results.append({
                "model": model_name,
                "error": str(e)
            })
            print(f"[✗] Ошибка при работе с моделью {model_name}: {e}")

    return results



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
    print(f"Сканирование всей директории проекта: {PROJECT_DIR}")

    if not os.path.exists(PROJECT_DIR):
        raise FileNotFoundError(f"Указанный путь не существует: {PROJECT_DIR}. Проверьте правильность пути!")

    context_chunks = []

    # 1. Заголовок и метаданные
    context_chunks.append("=== АНАЛИЗ ПРОЕКТА QUARTUS GENERATOR ===\n\n")
    context_chunks.append("ОКРУЖЕНИЕ И КОНТЕКСТ:\n")
    context_chunks.append("- Инструмент: Intel Quartus Prime\n\n")

    # 2. Добавление дерева структуры
    context_chunks.append("=== СТРУКТУРА ПРОЕКТА ===\n")
    context_chunks.append(f"[{os.path.basename(PROJECT_DIR)}/]\n")
    context_chunks.append(generate_tree(PROJECT_DIR))
    context_chunks.append("\n" + "=" * 40 + "\n\n")

    # 3. Добавление содержимого файлов
    context_chunks.append("=== СОДЕРЖИМОЕ ФАЙЛОВ ===\n\n")

    for root, dirs, files in os.walk(PROJECT_DIR):
        # Исключаем ненужные папки из обхода на лету
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in sorted(files):
            ext = os.path.splitext(file)[1].lower()
            if ext not in VALID_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, PROJECT_DIR)

            if full_path == OUTPUT_FILE:
                continue

            context_chunks.append(f"--- НАЧАЛО ФАЙЛА: {rel_path} ---\n")
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    context_chunks.append(f.read())
            except Exception as e:
                context_chunks.append(f"[Ошибка чтения файла: {str(e)}]\n")
            context_chunks.append(f"\n--- КОНЕЦ ФАЙЛА: {rel_path} ---\n\n")

    full_context = "".join(context_chunks)

    # Дублируем контекст в файл на диске для надежности
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(full_context)

    print(f"Успешно! Снапшот проекта сохранен локально в: {OUTPUT_FILE}")
    return full_context


def main():
    # Шаг 1: Собираем всю структуру и код папки
    project_data = collect_context()

    client = anthropic.Anthropic(
        api_key="sk-LgqiRR4lfipwfWA6vrs4xJvZOiEzYpsW",
        base_url="https://api.proxyapi.ru/anthropic",
    )

    # Шаг 3: Запускаем обработку через несколько моделей
    print("Запуск анализа проекта через несколько нейросетей...")
    results = process_with_models(project_data, client)

    # Шаг 4: Выводим результаты
    print("\n" + "=" * 60)
    print("=== РЕЗУЛЬТАТЫ АНАЛИЗА ПРОЕКТА ===")
    print("=" * 60)

    for i, res in enumerate(results, 1):
        print(f"\n[{i}] Модель: {res['model']}")
        if 'error' in res:
            print("❌ ОШИБКА:", res['error'])
        else:
            print("✅ ОТВЕТ:")
            print(res['response'])
        print("-" * 60)

    # Шаг 2: Формируем итоговый промпт для нейросети
    system_prompt = (
        "Ты — эксперт в области разработки на Scala, Chisel, FIRRTL, Python, Tcl и проектирования цифровой аппаратуры "
        "на Verilog/VHDL для Intel Quartus Prime. Твоя задача — проанализировать предоставленный "
        "проект генератора, найти ошибки и сделать его полностью запускаемым."
    )

    user_query = (
        "Все уже сделано так, как ты говоришь, продолжи генерировать до успешного исполнения проекта.\n\n"
        f"{project_data}"
    )

    # Шаг 3: Отправляем собранные данные в API
    print("Отправка данных проекта в Anthropic API... Пожалуйста, подождите.")



    # Используем claude-sonnet-4-6, так как лимиты контекста выше, а модель умнее
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,  # Увеличили лимит, чтобы уместить развернутый ответ с кодом
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_query
            }
        ]
    )

    print("\n=== АНАЛИЗ И ИСПРАВЛЕНИЯ ОТ НЕЙРОСЕТИ ===\n")
    print(message.content[0].text)


if __name__ == "__main__":
    main()