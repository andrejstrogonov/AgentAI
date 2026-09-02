"""PyQt desktop panel for configuring and running an AI-CICD pipeline."""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from QualityEngine import QualityEngine

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
                             QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget)


class PipelineWorker(QThread):
    completed = pyqtSignal(dict)
    failed = pyqtSignal(str)
    log = pyqtSignal(str)

    def __init__(self, code, settings):
        super().__init__()
        self.code = code
        self.settings = settings

    def run(self):
        try:
            engine = QualityEngine()
            result = {"started_at": datetime.now().isoformat(timespec="seconds"), "stages": {}}
            if self.settings["static"]:
                self.log.emit("[static] Проверка синтаксиса и mutation testing")
                result["stages"]["static"] = engine.mutation_testing(self.code)
            if self.settings["review"]:
                self.log.emit("[review] Генерация рекомендаций")
                result["stages"]["review"] = engine.genetic_improvement(self.code)
            if self.settings["tests"]:
                self.log.emit("[tests] Запуск тестовой команды")
                command = self.settings["test_command"]
                completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120,
                                           cwd=self.settings["project_dir"] or None)
                result["stages"]["tests"] = {"returncode": completed.returncode,
                                               "stdout": completed.stdout[-4000:],
                                               "stderr": completed.stderr[-4000:]}
            if self.settings["build"]:
                self.log.emit("[build] Сборка проекта")
                completed = subprocess.run(self.settings["build_command"], shell=True,
                                           capture_output=True, text=True, timeout=120,
                                           cwd=self.settings["project_dir"] or None)
                result["stages"]["build"] = {"returncode": completed.returncode,
                                               "stdout": completed.stdout[-4000:],
                                               "stderr": completed.stderr[-4000:]}
            self.completed.emit(result)
        except Exception as error:
            self.failed.emit(str(error))


class ReviewDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgentAI | AI-CICD Pipeline")
        self.resize(1100, 760)
        self.worker = None

        self.source = QTextEdit()
        self.source.setPlaceholderText("Вставьте Python-код или выберите файл проекта")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.artifacts = QTextEdit()
        self.artifacts.setReadOnly(True)

        pipeline = QWidget()
        pipeline_form = QFormLayout()
        self.project_path = QLineEdit()
        self.project_path.setPlaceholderText("Необязательно: каталог проекта")
        choose_project = QPushButton("Выбрать")
        choose_project.clicked.connect(self.choose_project)
        path_row = QHBoxLayout()
        path_row.addWidget(self.project_path)
        path_row.addWidget(choose_project)
        pipeline_form.addRow("Проект", path_row)
        self.ai_mode = QComboBox()
        self.ai_mode.addItems(["Local quality engine", "Sequential models", "Parallel async models"])
        pipeline_form.addRow("AI-режим", self.ai_mode)
        self.static_check = QCheckBox("Статический анализ и мутационное тестирование")
        self.static_check.setChecked(True)
        self.tests_check = QCheckBox("Тесты")
        self.build_check = QCheckBox("Сборка проекта")
        self.build_check.setChecked(True)
        self.review_check = QCheckBox("Code review и рекомендации")
        self.review_check.setChecked(True)
        pipeline_form.addRow("Этапы", self.static_check)
        pipeline_form.addRow("", self.tests_check)
        pipeline_form.addRow("", self.build_check)
        pipeline_form.addRow("", self.review_check)
        self.test_command = QLineEdit("python -m unittest discover -s tests")
        pipeline_form.addRow("Команда тестов", self.test_command)
        self.build_command = QLineEdit("python -m compileall -q .")
        pipeline_form.addRow("Команда сборки", self.build_command)
        run = QPushButton("Запустить pipeline")
        stop = QPushButton("Остановить")
        save = QPushButton("Сохранить конфиг")
        run.clicked.connect(self.run_pipeline)
        stop.clicked.connect(self.stop_pipeline)
        save.clicked.connect(self.save_config)
        actions = QHBoxLayout()
        actions.addWidget(run)
        actions.addWidget(stop)
        actions.addWidget(save)
        pipeline_form.addRow("Управление", actions)
        pipeline.setLayout(pipeline_form)

        source_tab = QWidget()
        source_layout = QVBoxLayout()
        browse = QPushButton("Открыть .py")
        browse.clicked.connect(self.open_file)
        source_layout.addWidget(browse)
        source_layout.addWidget(self.source)
        source_tab.setLayout(source_layout)

        artifacts_tab = QWidget()
        artifacts_layout = QVBoxLayout()
        artifacts_layout.addWidget(QLabel("Артефакты и логи последнего запуска"))
        artifacts_layout.addWidget(self.artifacts)
        artifacts_tab.setLayout(artifacts_layout)

        tabs = QTabWidget()
        tabs.addTab(pipeline, "Pipeline")
        tabs.addTab(source_tab, "Source")
        tabs.addTab(artifacts_tab, "Artifacts")
        layout = QVBoxLayout()
        layout.addWidget(tabs, 3)
        layout.addWidget(QLabel("Pipeline log"))
        layout.addWidget(self.log_output, 2)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите Python-файл", "", "Python (*.py)")
        if filename:
            self.source.setPlainText(Path(filename).read_text(encoding="utf-8"))
            self.project_path.setText(str(Path(filename).parent))

    def choose_project(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите каталог проекта")
        if directory:
            self.project_path.setText(directory)

    def run_pipeline(self):
        if self.worker and self.worker.isRunning():
            return
        settings = {"static": self.static_check.isChecked(), "tests": self.tests_check.isChecked(),
                "build": self.build_check.isChecked(), "review": self.review_check.isChecked(),
                    "test_command": self.test_command.text(), "build_command": self.build_command.text(),
                    "project_dir": self.project_path.text()}
        self.log_output.clear()
        self.log_output.append("Pipeline started")
        self.worker = PipelineWorker(self.source.toPlainText(), settings)
        self.worker.log.connect(self.log_output.append)
        self.worker.completed.connect(self.pipeline_completed)
        self.worker.failed.connect(self.pipeline_failed)
        self.worker.start()

    def stop_pipeline(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.log_output.append("Pipeline stopped")

    def pipeline_completed(self, result):
        output_dir = Path(self.project_path.text() or ".") / ".agentai-artifacts"
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact = output_dir / "pipeline-result.json"
        artifact.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        self.artifacts.setPlainText(json.dumps(result, indent=2, ensure_ascii=False) + f"\n\nSaved: {artifact}")
        self.log_output.append(f"Pipeline completed; artifact: {artifact}")

    def pipeline_failed(self, message):
        self.log_output.append(f"Pipeline failed: {message}")
        QMessageBox.critical(self, "Pipeline error", message)

    def save_config(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить конфигурацию", "pipeline.json", "JSON (*.json)")
        if filename:
            config = {"project": self.project_path.text(), "ai_mode": self.ai_mode.currentText(),
                      "stages": {"static": self.static_check.isChecked(), "tests": self.tests_check.isChecked(),
                                 "build": self.build_check.isChecked(),
                                 "review": self.review_check.isChecked()},
                      "test_command": self.test_command.text(), "build_command": self.build_command.text()}
            Path(filename).write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
            self.log_output.append(f"Configuration saved: {filename}")



def main():
    app = QApplication(sys.argv)
    window = ReviewDemo()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
