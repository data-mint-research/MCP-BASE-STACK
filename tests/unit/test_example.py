"""
Example unit test for MCP-BASE-STACK.

This file serves as an example of how to write unit tests for the project.
"""

import unittest
from typing import List, Dict, Any


class ExampleTest(unittest.TestCase):
    """Example test case demonstrating unit testing patterns."""

    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.sample_data = {
            "name": "example",
            "values": [1, 2, 3, 4, 5],
            "metadata": {
                "version": "1.0.0",
                "description": "Sample test data"
            }
        }

    def tearDown(self) -> None:
        """Clean up test fixtures after each test method."""
        self.sample_data = None

    def test_data_structure(self) -> None:
        """Test that the sample data has the expected structure."""
        self.assertIsInstance(self.sample_data, dict)
        self.assertIn("name", self.sample_data)
        self.assertIn("values", self.sample_data)
        self.assertIn("metadata", self.sample_data)
        
        self.assertIsInstance(self.sample_data["name"], str)
        self.assertIsInstance(self.sample_data["values"], list)
        self.assertIsInstance(self.sample_data["metadata"], dict)

    def test_data_values(self) -> None:
        """Test that the sample data contains expected values."""
        self.assertEqual(self.sample_data["name"], "example")
        self.assertEqual(len(self.sample_data["values"]), 5)
        self.assertEqual(sum(self.sample_data["values"]), 15)
        self.assertEqual(self.sample_data["metadata"]["version"], "1.0.0")


def calculate_sum(numbers: List[int]) -> int:
    """
    Calculate the sum of a list of numbers.
    
    Args:
        numbers: A list of integers to sum
        
    Returns:
        The sum of all numbers in the list
    """
    return sum(numbers)


class CalculationTest(unittest.TestCase):
    """Test case for calculation functions."""
    
    def test_calculate_sum(self) -> None:
        """Test the calculate_sum function."""
        self.assertEqual(calculate_sum([1, 2, 3]), 6)
        self.assertEqual(calculate_sum([]), 0)
        self.assertEqual(calculate_sum([-1, 1]), 0)
        self.assertEqual(calculate_sum([10, 20, 30, 40]), 100)


if __name__ == "__main__":
    unittest.main()