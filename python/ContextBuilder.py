import logging
import os
import json
from pathlib import Path


class ContextBuilder:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.valid_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss', '.json',
            '.yaml', '.yml', '.md', '.txt', '.xml', '.sql', '.java', '.cpp', '.c',
            '.h', '.hpp', '.go', '.rs', '.rb', '.php', '.sh', '.bash', '.pl', '.pm'
        }
        self.ignore_dirs = {
            '__pycache__', '.git', 'node_modules', '.svn', '.hg', '.idea',
            '.vscode', 'venv', '.venv', 'env', '.env', '__pycache__', '.pytest_cache',
            'dist', 'build', '.tox', '.coverage', '.mypy_cache', '.DS_Store', '.qodo'
        }
        self.max_file_size = 1024 * 1024

    def build_project_context(self, project_dir):
        """Построение контекста проекта"""
        project_path = Path(project_dir)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Директория не существует: {project_dir}")
        
        context_chunks = {
            'metadata': {},
            'tree_structure': '',
            'file_contents': {},
            'dependencies': {},
            'cicd_configs': {},
            'readme': '',
            'license': '',
            'stats': {}
        }

        try:
            self.add_metadata(context_chunks, project_path)
            self.add_tree_structure(context_chunks, project_path)
            self.add_file_contents(context_chunks, project_path)
            self.add_dependencies(context_chunks, project_path)
            self.add_cicd_configs(context_chunks, project_path)
            self.add_readme_and_license(context_chunks, project_path)
            self.add_statistics(context_chunks, project_path)
        except Exception as e:
            self.logger.error(f"Ошибка при построении контекста проекта: {e}")
            raise

        return context_chunks

    def add_metadata(self, context_chunks, project_path):
        """Добавление метаданных проекта"""
        context_chunks['metadata'] = {
            'project_name': project_path.name,
            'project_path': str(project_path.resolve()),
            'project_type': self._detect_project_type(project_path)
        }

    def _detect_project_type(self, project_path):
        """Определение типа проекта"""
        if (project_path / 'package.json').exists():
            return 'Node.js'
        if (project_path / 'requirements.txt').exists():
            return 'Python'
        if (project_path / 'go.mod').exists():
            return 'Go'
        if (project_path / 'pom.xml').exists():
            return 'Java Maven'
        if (project_path / 'Cargo.toml').exists():
            return 'Rust'
        return 'Unknown'

    def add_tree_structure(self, context_chunks, project_path):
        """Добавление дерева структуры проекта"""
        context_chunks['tree_structure'] = self._generate_tree(project_path)

    def _generate_tree(self, current_dir, indent=""):
        """Рекурсивное построение дерева директорий"""
        tree = ""
        try:
            items = sorted(current_dir.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            self.logger.warning(f"Нет доступа к директории: {current_dir}")
            return tree

        items_list = [i for i in items if i.name not in self.ignore_dirs]
        for idx, item in enumerate(items_list):
            is_last = (idx == len(items_list) - 1)
            connector = '└── ' if is_last else '├── '
            child_indent = indent + ("    " if is_last else "│   ")

            if item.is_dir():
                tree += f"{indent}{connector}[{item.name}/]\n"
                tree += self._generate_tree(item, child_indent)
            else:
                tree += f"{indent}{connector}{item.name}\n"

        return tree

    def add_file_contents(self, context_chunks, project_path):
        """Чтение и сохранение содержимого файлов"""
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]

            for file_name in sorted(files):
                file_path = Path(root) / file_name
                if file_path.suffix.lower() not in self.valid_extensions:
                    continue
                
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        self.logger.warning(f"Файл пропущен (>1MB): {file_path}")
                        continue
                except:
                    continue

                rel_path = str(file_path.relative_to(project_path))
                try:
                    content = file_path.read_text(encoding='utf-8', errors='replace')
                    context_chunks['file_contents'][rel_path] = content
                except Exception as e:
                    self.logger.warning(f"Ошибка чтения {file_path}: {e}")
                    context_chunks['file_contents'][rel_path] = f"[Error: {e}]"

    def add_dependencies(self, context_chunks, project_path):
        """Сбор зависимостей из стандартных файлов"""
        deps = {}
        
        if (project_path / 'requirements.txt').exists():
            try:
                lines = (project_path / 'requirements.txt').read_text().splitlines()
                deps['requirements.txt'] = [l.strip() for l in lines if l.strip() and not l.startswith('#')]
            except Exception as e:
                self.logger.warning(f"Ошибка парсинга requirements.txt: {e}")
        
        if (project_path / 'package.json').exists():
            try:
                data = json.loads((project_path / 'package.json').read_text())
                deps['package.json'] = {
                    'dependencies': list(data.get('dependencies', {}).keys()),
                    'devDependencies': list(data.get('devDependencies', {}).keys()),
                }
            except Exception as e:
                self.logger.warning(f"Ошибка парсинга package.json: {e}")
        
        context_chunks['dependencies'] = deps

    def add_cicd_configs(self, context_chunks, project_path):
        """Поиск CI/CD конфигурационных файлов"""
        cicd = {}
        candidates = [
            '.github/workflows', '.gitlab-ci.yml', 'Jenkinsfile',
            '.travis.yml', 'Dockerfile', 'Makefile',
        ]
        for candidate in candidates:
            target = project_path / candidate
            if target.exists():
                cicd[candidate] = str(target.relative_to(project_path))
        context_chunks['cicd_configs'] = cicd

    def add_readme_and_license(self, context_chunks, project_path):
        """Чтение README и LICENSE файлов"""
        for name in ('README.md', 'README.rst', 'README.txt', 'readme.md'):
            p = project_path / name
            if p.exists():
                try:
                    context_chunks['readme'] = p.read_text(encoding='utf-8', errors='replace')
                except:
                    pass
                break

        for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING'):
            p = project_path / name
            if p.exists():
                try:
                    context_chunks['license'] = p.read_text(encoding='utf-8', errors='replace')
                except:
                    pass
                break

    def add_statistics(self, context_chunks, project_path):
        """Сбор статистики по проекту"""
        stats = {}
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            for f in files:
                ext = Path(f).suffix.lower()
                stats[ext] = stats.get(ext, 0) + 1
        context_chunks['stats'] = stats

    def build_prompt_context(self, project_dir: str) -> str:
        """Возвращает контекст проекта в виде единой строки для промпта"""
        chunks = self.build_project_context(project_dir)
        parts = [
            "=== PROJECT ANALYSIS ===\n",
            f"Project: {chunks['metadata'].get('project_name', 'Unknown')}\n",
            f"Type: {chunks['metadata'].get('project_type', 'Unknown')}\n\n",
            "=== PROJECT STRUCTURE ===\n",
            chunks['tree_structure'],
            "\n=== FILE CONTENTS ===\n",
        ]
        for rel_path, content in chunks['file_contents'].items():
            parts.append(f"\n--- START: {rel_path} ---\n")
            parts.append(content[:5000])  # Ограничиваем длину файла в контексте
            parts.append(f"\n--- END: {rel_path} ---\n")

        if chunks['readme']:
            parts.append(f"\n=== README ===\n{chunks['readme'][:2000]}\n")

        return "".join(parts)
