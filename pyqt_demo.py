"""Minimal PyQt demonstration for local review quality analysis."""

import sys
from pathlib import Path

from QualityEngine import QualityEngine

try:
    from PyQt6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget
except ImportError:
    from PyQt5.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget


class ReviewDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = QualityEngine()
        self.setWindowTitle("AgentAI Quality Review")
        self.resize(900, 650)

        self.source = QTextEdit()
        self.source.setPlaceholderText("Вставьте Python-код или выберите .py файл")
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        browse = QPushButton("Открыть .py")
        analyze = QPushButton("Запустить review")
        browse.clicked.connect(self.open_file)
        analyze.clicked.connect(self.run_review)

        buttons = QHBoxLayout()
        buttons.addWidget(browse)
        buttons.addWidget(analyze)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Исходный код"))
        layout.addWidget(self.source, 3)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Результат"))
        layout.addWidget(self.output, 2)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите Python-файл", "", "Python (*.py)")
        if filename:
            self.source.setPlainText(Path(filename).read_text(encoding="utf-8"))

    def run_review(self):
        code = self.source.toPlainText()
        mutation = self.engine.mutation_testing(code)
        genetic = self.engine.genetic_improvement(code)
        recommendations = "\n".join(f"- {item}" for item in genetic["recommendations"])
        self.output.setPlainText(
            f"{mutation['mutation_summary']}\n{mutation['mutation_findings']}\n\n"
            f"{genetic['generation_summary']}\n{genetic['best_solution']}\n\n"
            f"Рекомендации:\n{recommendations}"
        )


def main():
    app = QApplication(sys.argv)
    window = ReviewDemo()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
