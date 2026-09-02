import asyncio
import unittest
from unittest.mock import AsyncMock, Mock

from ModelProcessor import ModelProcessor
from QualityEngine import QualityEngine


class QualityEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = QualityEngine()
        self.code = """
def is_ready(value):
    if value > 0 and value < 10:
        return True
    return False
"""

    def test_mutation_testing_generates_valid_mutants(self):
        result = self.engine.mutation_testing(self.code)
        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(result["total_mutants"], 3)
        self.assertEqual(result["total_mutants"], len(result["mutants"]))
        self.assertEqual(result["total_mutants"], result["valid_mutants"])

    def test_genetic_algorithm_is_deterministic_and_actionable(self):
        result = self.engine.genetic_improvement(self.code)
        again = self.engine.genetic_improvement(self.code)
        self.assertEqual(result["best_solution"], again["best_solution"])
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["recommendations"])
        self.assertEqual(len(result["generations"]), 3)


class ModelProcessorQualityIntegrationTests(unittest.TestCase):
    def make_processor(self):
        processor = ModelProcessor.__new__(ModelProcessor)
        processor.quality_engine = QualityEngine()
        processor.model_list = ["test-model"]
        return processor

    def test_sequential_result_contains_quality_sections(self):
        processor = self.make_processor()
        processor.sync_client = Mock()
        processor.sync_client.messages.create.return_value = Mock(
            content=[Mock(text="Add tests for errors.")]
        )
        result = processor.process_with_models_sequential("if value > 0: return True")
        self.assertIn("mutation_testing", result)
        self.assertIn("genetic_improvement", result)

    def test_parallel_result_contains_quality_sections(self):
        processor = self.make_processor()
        processor.async_client = Mock()
        processor._process_single_model_async = AsyncMock(return_value={
            "model": "test-model", "response": "test errors", "status": "success", "response_length": 11
        })
        result = asyncio.run(processor.process_with_models_parallel("if value > 0: return True"))
        self.assertIn("mutation_testing", result)
        self.assertIn("genetic_improvement", result)


if __name__ == "__main__":
    unittest.main()
