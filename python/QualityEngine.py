"""Deterministic mutation testing and genetic recommendation helpers."""

import ast
import io
import random
import re
import tokenize
from typing import Any, Dict, List


class QualityEngine:
    """Run lightweight local quality analysis without an external model."""

    MUTATION_OPERATORS = (
        ("comparison", "==", "!="),
        ("comparison", ">", ">="),
        ("comparison", "<", "<="),
        ("boolean", " and ", " or "),
        ("arithmetic", " + ", " - "),
    )

    def mutation_testing(self, project_data: str) -> Dict[str, Any]:
        """Generate syntax-valid mutants and report likely test gaps.

        This is intentionally static: without a project test runner, a mutant cannot
        be honestly classified as killed. The report exposes that distinction.
        """
        source = project_data or ""
        source_lines = source.splitlines()
        mutants: List[Dict[str, Any]] = []
        token_replacements = {"==": ("comparison", "!="), ">": ("comparison", ">="),
                              "<": ("comparison", "<="), "and": ("boolean", "or"),
                              "+": ("arithmetic", "-"), "-": ("arithmetic", "+")}
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            mutation_points = [
                (token.start[0], token.start[1], token.end[1], token.string, *token_replacements[token.string])
                for token in tokens if token.string in token_replacements
            ]
        except (tokenize.TokenError, IndentationError):
            mutation_points = []

        for line_number, start, end, original, operator, replacement in mutation_points:
                line = source_lines[line_number - 1]
                mutated_line = line[:start] + replacement + line[end:]
                candidate_lines = list(source_lines)
                candidate_lines[line_number - 1] = mutated_line
                candidate = "\n".join(candidate_lines)
                try:
                    ast.parse(candidate)
                    syntax_valid = True
                except SyntaxError:
                    syntax_valid = False
                mutants.append({
                    "id": f"M{len(mutants) + 1}",
                    "line": line_number,
                    "operator": operator,
                    "change": f"{original.strip()} -> {replacement.strip()}",
                    "syntax_valid": syntax_valid,
                    "status": "untested",
                })

        valid_mutants = [mutant for mutant in mutants if mutant["syntax_valid"]]
        return {
            "mutation_summary": (
                f"Generated {len(mutants)} mutants; {len(valid_mutants)} are syntax-valid. "
                "Execution status is untested because no test command was supplied."
            ),
            "mutation_findings": (
                "Add targeted tests for lines: "
                + ", ".join(str(item["line"]) for item in valid_mutants[:10])
                if valid_mutants
                else "No supported mutation points found."
            ),
            "mutants": mutants,
            "total_mutants": len(mutants),
            "valid_mutants": len(valid_mutants),
            "status": "success",
        }

    def genetic_improvement(
        self, project_data: str, results: List[Dict[str, Any]] = None, seed: int = 7
    ) -> Dict[str, Any]:
        """Evolve actionable recommendations from model output and local signals."""
        random_generator = random.Random(seed)
        candidates = self._recommendation_candidates(project_data, results or [])
        population = list(dict.fromkeys(candidates))
        if not population:
            population = ["Add focused tests around error handling and boundary conditions."]

        generations = []
        for _ in range(3):
            ranked = sorted(population, key=self._fitness, reverse=True)
            generations.append({"size": len(population), "best_fitness": self._fitness(ranked[0])})
            parents = ranked[: max(1, min(3, len(ranked)))]
            children = []
            while len(children) < min(8, max(2, len(population))):
                first = random_generator.choice(parents)
                second = random_generator.choice(parents)
                children.append(self._crossover(first, second))
            population = list(dict.fromkeys(parents + children))

        best = max(population, key=self._fitness)
        return {
            "generation_summary": f"Evolved {len(generations)} generations; best fitness {self._fitness(best):.2f}.",
            "best_solution": best,
            "recommendations": sorted(dict.fromkeys(population), key=self._fitness, reverse=True)[:5],
            "generations": generations,
            "fitness": self._fitness(best),
            "status": "success",
        }

    @staticmethod
    def _recommendation_candidates(project_data: str, results: List[Dict[str, Any]]) -> List[str]:
        text = "\n".join(str(item.get("response") or "") for item in results)
        candidates = [
            line.strip(" -*") for line in text.splitlines()
            if len(line.strip(" -*")) >= 25 and re.search(r"test|fix|error|exception|bug|recommend", line, re.I)
        ]
        if "try:" in project_data or "except" in project_data:
            candidates.append("Add tests for exception paths and verify error messages remain actionable.")
        if "async def" in project_data or "asyncio" in project_data:
            candidates.append("Test async cancellation, timeout, and failure propagation explicitly.")
        if "if " in project_data:
            candidates.append("Cover both branches of each conditional with boundary-value tests.")
        return candidates

    @staticmethod
    def _fitness(candidate: str) -> float:
        score = 0.0
        score += min(len(candidate), 140) / 140
        score += 0.35 if re.search(r"test|tests", candidate, re.I) else 0
        score += 0.25 if re.search(r"error|exception|boundary|async", candidate, re.I) else 0
        return round(score, 4)

    @staticmethod
    def _crossover(first: str, second: str) -> str:
        first_words = first.rstrip(".").split()
        second_words = second.rstrip(".").split()
        midpoint = max(1, len(first_words) // 2)
        child = " ".join(first_words[:midpoint] + second_words[midpoint:])
        return child.rstrip(".") + "."
