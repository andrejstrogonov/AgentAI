import json
import logging
import os
from pathlib import Path


class ProjectAnalyzer:
    def __init__(self, project_dir, output_file, valid_extensions, ignore_dirs):
        # Инициализация параметров
        self.project_dir = Path(project_dir)
        self.output_file = output_file
        self.valid_extensions = set(valid_extensions)
        self.ignore_dirs = set(ignore_dirs)
        self.context = {}
        self.cicd_configs = {}

        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def generate_tree(self, current_dir, indent=""):
        """Рекурсивное построение дерева проекта"""
        tree = ""
        try:
            items = sorted(os.listdir(current_dir))
            for i, item in enumerate(items):
                item_path = os.path.join(current_dir, item)
                is_last = (i == len(items) - 1)

                if item in self.ignore_dirs:
                    continue

                if os.path.isdir(item_path):
                    tree += f"{indent}{'└── ' if is_last else '├── '}{item}/\n"
                    tree += self.generate_tree(item_path, indent + ("    " if is_last else "│   "))
                else:
                    tree += f"{indent}{'└── ' if is_last else '├── '}{item}\n"
        except PermissionError:
            self.logger.warning(f"Нет доступа к директории: {current_dir}")

        return tree

    def collect_context(self):
        """Сканирование проекта и сбор контекста"""
        self.context = {
            'project_structure': self._build_project_structure(),
            'file_stats': self._count_files_by_type(),
            'cicd_configs': self._find_cicd_configs(),
            'dependencies': self._collect_dependencies(),
            'readme': self._read_readme(),
            'license': self._find_license()
        }
        return self.context

    def _build_project_structure(self):
        """Построение структуры проекта"""
        structure = {}
        for root, dirs, files in os.walk(self.project_dir):
            # Пропуск игнорируемых директорий
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            # Определяем уровень вложенности
            rel_path = os.path.relpath(root, self.project_dir)
            if rel_path == '.':
                current_level = structure
            else:
                parts = rel_path.split(os.sep)
                current_level = structure
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

            # Добавляем файлы
            for file in files:
                if any(file.endswith(ext) for ext in self.valid_extensions):
                    current_level[file] = {
                        'size': os.path.getsize(os.path.join(root, file)),
                        'type': 'file'
                    }

        return structure

    def _count_files_by_type(self):
        """Подсчет файлов по типам"""
        stats = {}
        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for file in files:
                ext = os.path.splitext(file)[1]
                if ext:
                    stats[ext] = stats.get(ext, 0) + 1
        return stats

    def _find_cicd_configs(self):
        """Поиск конфигурационных файлов CI/CD"""
        cicd_files = {}

        # Поддерживаемые файлы CI/CD
        cicd_patterns = {
            '.github/workflows': '.github/workflows/',
            '.gitlab-ci.yml': '.gitlab-ci.yml',
            'Jenkinsfile': 'Jenkinsfile',
            '.travis.yml': '.travis.yml',
            '.circleci/config.yml': '.circleci/config.yml',
            'azure-pipelines.yml': 'azure-pipelines.yml',
            '.buildkite/pipeline.yml': '.buildkite/pipeline.yml',
            'Makefile': 'Makefile',
            'Dockerfile': 'Dockerfile'
        }

        for pattern, path in cicd_patterns.items():
            if pattern == '.github/workflows':
                workflows_dir = self.project_dir / '.github' / 'workflows'
                if workflows_dir.exists():
                    cicd_files['github_workflows'] = []
                    for workflow in workflows_dir.glob('*.yml'):
                        cicd_files['github_workflows'].append({
                            'name': workflow.name,
                            'path': str(workflow.relative_to(self.project_dir))
                        })
            elif (self.project_dir / path).exists():
                cicd_files[os.path.basename(path).replace('.', '_')] = str(path)
            elif (self.project_dir / pattern).exists():
                cicd_files[os.path.basename(pattern).replace('.', '_')] = str(pattern)

        return cicd_files

    def _collect_dependencies(self):
        """Сбор информации о зависимостях"""
        deps = {}

        # Пытаемся найти файлы зависимостей
        dep_files = ['package.json', 'requirements.txt', 'Gemfile', 'pom.xml', 'build.gradle', 'go.mod', 'Cargo.toml']

        for dep_file in dep_files:
            file_path = self.project_dir / dep_file
            if file_path.exists():
                try:
                    if dep_file == 'package.json':
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            deps['npm'] = {
                                'dependencies': list(data.get('dependencies', {}).keys()),
                                'dev_dependencies': list(data.get('devDependencies', {}).keys())
                            }
                    elif dep_file == 'requirements.txt':
                        with open(file_path, 'r') as f:
                            deps['pip'] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    elif dep_file == 'Gemfile':
                        with open(file_path, 'r') as f:
                            content = f.read()
                            deps['ruby'] = [line for line in content.split('\n') if
                                            'gem' in line and not line.startswith('#')]
                    elif dep_file == 'pom.xml':
                        with open(file_path, 'r') as f:
                            content = f.read()
                            deps['maven'] = 'maven'  # Простое указание типа
                    elif dep_file == 'build.gradle':
                        deps['gradle'] = 'gradle'
                    elif dep_file == 'go.mod':
                        deps['go'] = 'go'
                    elif dep_file == 'Cargo.toml':
                        deps['rust'] = 'rust'
                except Exception as e:
                    self.logger.warning(f"Ошибка при чтении {dep_file}: {e}")

        return deps

    def _read_readme(self):
        """Чтение README файла"""
        readme_files = ['README.md', 'README.rst', 'README.txt', 'readme.md']
        for readme_file in readme_files:
            file_path = self.project_dir / readme_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        return content[:500] + '...' if len(content) > 500 else content
                except Exception as e:
                    self.logger.warning(f"Ошибка чтения README: {e}")
        return None

    def _find_license(self):
        """Поиск лицензионного файла"""
        license_files = ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING']
        for license_file in license_files:
            file_path = self.project_dir / license_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        return content[:200] + '...' if len(content) > 200 else content
                except Exception as e:
                    self.logger.warning(f"Ошибка чтения лицензии: {e}")
        return None

    def run_cicd_pipeline(self, pipeline_type='auto'):
        """Запуск CI/CD pipeline (для тестирования)"""
        try:
            if pipeline_type == 'auto':
                # Определяем тип CI/CD автоматически
                if 'github_workflows' in self.context['cicd_configs']:
                    pipeline_type = 'github'
                elif 'gitlab_ci_yml' in self.context['cicd_configs']:
                    pipeline_type = 'gitlab'
                elif 'jenkinsfile' in self.context['cicd_configs']:
                    pipeline_type = 'jenkins'
                else:
                    self.logger.warning("CI/CD конфигурации не найдены")
                    return False

            # Выполнение pipeline в зависимости от типа
            if pipeline_type == 'github':
                self.logger.info("Запуск GitHub Actions pipeline")
                # Это будет виртуальный запуск для демонстрации
                return self._simulate_github_pipeline()
            elif pipeline_type == 'gitlab':
                self.logger.info("Запуск GitLab CI pipeline")
                return self._simulate_gitlab_pipeline()
            elif pipeline_type == 'jenkins':
                self.logger.info("Запуск Jenkins pipeline")
                return self._simulate_jenkins_pipeline()

        except Exception as e:
            self.logger.error(f"Ошибка запуска CI/CD pipeline: {e}")
            return False

    def _simulate_github_pipeline(self):
        """Симуляция запуска GitHub Actions pipeline"""
        # Здесь можно реализовать реальный запуск или проверку
        print("Симуляция запуска GitHub Actions pipeline...")
        print("Проверка конфигурации...")
        print("Запуск тестов...")
        print("Сбор метрик качества кода...")
        print("Генерация отчетов...")
        return True

    def _simulate_gitlab_pipeline(self):
        """Симуляция запуска GitLab CI pipeline"""
        print("Симуляция запуска GitLab CI pipeline...")
        print("Проверка конфигурации...")
        print("Запуск тестов...")
        print("Проверка безопасности...")
        print("Деплой в staging...")
        return True

    def _simulate_jenkins_pipeline(self):
        """Симуляция запуска Jenkins pipeline"""
        print("Симуляция запуска Jenkins pipeline...")
        print("Сбор данных о проекте...")
        print("Запуск unit тестов...")
        print("Запуск integration тестов...")
        print("Проверка покрытия кода...")
        return True

    def get_cicd_status(self):
        """Получение статуса CI/CD конфигураций"""
        return {
            'has_github_actions': 'github_workflows' in self.context['cicd_configs'],
            'has_gitlab_ci': 'gitlab_ci_yml' in self.context['cicd_configs'],
            'has_jenkinsfile': 'jenkinsfile' in self.context['cicd_configs'],
            'has_cicd_config': len(self.context['cicd_configs']) > 0,
            'cicd_configs': self.context['cicd_configs']
        }

    def export_context(self):
        """Экспорт контекста в файл"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.context, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Контекст сохранен в {self.output_file}")

    def analyze_and_export(self):
        """Полный анализ и экспорт"""
        self.collect_context()
        self.export_context()
        return self.context

    def get_project_summary(self):
        """Получение краткого резюме проекта с CI/CD информацией"""
        return {
            'project_name': self.project_dir.name,
            'total_files': sum(1 for _ in self.project_dir.rglob('*') if _.is_file()),
            'cicd_status': self.get_cicd_status(),
            'dependencies_count': len(self.context.get('dependencies', {})),
            'supported_languages': list(self.context.get('file_stats', {}).keys())
        }


# Пример использования:
if __name__ == "__main__":
    # Инициализация анализатора
    analyzer = ProjectAnalyzer(
        project_dir=".",
        output_file="project_context.json",
        valid_extensions=['.py', '.js', '.html', '.css', '.md'],
        ignore_dirs=['__pycache__', '.git', 'node_modules', 'venv']
    )

    # Сбор контекста
    context = analyzer.collect_context()

    # Показать CI/CD информацию
    print("CI/CD Конфигурации:")
    print(json.dumps(analyzer.get_cicd_status(), indent=2))

    # Показать краткое резюме
    print("\nКраткое резюме:")
    print(json.dumps(analyzer.get_project_summary(), indent=2))

    # Запуск CI/CD pipeline (для демонстрации)
    print("\nЗапуск CI/CD pipeline:")
    analyzer.run_cicd_pipeline()
