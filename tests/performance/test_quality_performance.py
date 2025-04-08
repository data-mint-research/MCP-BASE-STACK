"""
Performance benchmarks for quality modules.

This module contains performance benchmarks for quality checks, fix operations,
reporting, and performance regression detection.
"""

import os
import time
import json
import tempfile
import shutil
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from core.quality import QualityCheckResult, QualityCheckSeverity
from tests.utils.fixtures import temp_test_dir, mock_quality_results
from tests.utils.mocks import MockFileSystem, MockConfig, MockKnowledgeGraph
from tests.utils.helpers import create_test_file, create_test_directory_structure


class PerformanceMetrics:
    """Class for collecting and analyzing performance metrics."""
    
    def __init__(self, name: str, baseline_path: Optional[str] = None):
        """
        Initialize the performance metrics collector.
        
        Args:
            name: The name of the benchmark.
            baseline_path: Optional path to a baseline metrics file.
        """
        self.name = name
        self.metrics = {}
        self.baseline = {}
        
        if baseline_path and os.path.exists(baseline_path):
            with open(baseline_path, "r") as f:
                self.baseline = json.load(f)
    
    def start_timer(self, operation: str) -> None:
        """
        Start a timer for an operation.
        
        Args:
            operation: The name of the operation.
        """
        if operation not in self.metrics:
            self.metrics[operation] = {}
        
        self.metrics[operation]["start_time"] = time.time()
    
    def stop_timer(self, operation: str) -> float:
        """
        Stop a timer for an operation and return the elapsed time.
        
        Args:
            operation: The name of the operation.
            
        Returns:
            The elapsed time in seconds.
        """
        if operation not in self.metrics or "start_time" not in self.metrics[operation]:
            raise ValueError(f"Timer for operation '{operation}' was not started")
        
        elapsed = time.time() - self.metrics[operation]["start_time"]
        self.metrics[operation]["elapsed"] = elapsed
        return elapsed
    
    def record_metric(self, operation: str, metric: str, value: Any) -> None:
        """
        Record a metric for an operation.
        
        Args:
            operation: The name of the operation.
            metric: The name of the metric.
            value: The value of the metric.
        """
        if operation not in self.metrics:
            self.metrics[operation] = {}
        
        self.metrics[operation][metric] = value
    
    def get_metric(self, operation: str, metric: str) -> Any:
        """
        Get a metric for an operation.
        
        Args:
            operation: The name of the operation.
            metric: The name of the metric.
            
        Returns:
            The value of the metric.
        """
        if operation not in self.metrics or metric not in self.metrics[operation]:
            raise ValueError(f"Metric '{metric}' for operation '{operation}' not found")
        
        return self.metrics[operation][metric]
    
    def compare_with_baseline(self, operation: str, metric: str, threshold: float = 0.1) -> Dict[str, Any]:
        """
        Compare a metric with its baseline value.
        
        Args:
            operation: The name of the operation.
            metric: The name of the metric.
            threshold: The threshold for regression detection.
            
        Returns:
            A dictionary with comparison results.
        """
        if operation not in self.metrics or metric not in self.metrics[operation]:
            raise ValueError(f"Metric '{metric}' for operation '{operation}' not found")
        
        current = self.metrics[operation][metric]
        
        if operation not in self.baseline or metric not in self.baseline[operation]:
            return {
                "current": current,
                "baseline": None,
                "difference": None,
                "regression": False
            }
        
        baseline = self.baseline[operation][metric]
        difference = current - baseline
        regression = difference > baseline * threshold
        
        return {
            "current": current,
            "baseline": baseline,
            "difference": difference,
            "regression": regression
        }
    
    def save_metrics(self, output_path: str) -> None:
        """
        Save the metrics to a file.
        
        Args:
            output_path: The path to save the metrics to.
        """
        with open(output_path, "w") as f:
            json.dump(self.metrics, f, indent=2)
    
    def generate_report(self, output_path: str) -> None:
        """
        Generate a performance report.
        
        Args:
            output_path: The path to save the report to.
        """
        report = {
            "name": self.name,
            "timestamp": time.time(),
            "metrics": self.metrics,
            "comparisons": {}
        }
        
        for operation in self.metrics:
            report["comparisons"][operation] = {}
            
            for metric in self.metrics[operation]:
                if metric != "start_time":
                    try:
                        report["comparisons"][operation][metric] = self.compare_with_baseline(operation, metric)
                    except ValueError:
                        pass
        
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)


@pytest.mark.performance
class TestQualityCheckPerformance:
    """Performance benchmarks for quality checks."""
    
    @pytest.fixture
    def performance_metrics(self):
        """Create a performance metrics collector."""
        return PerformanceMetrics("quality_check_performance")
    
    @pytest.fixture
    def large_test_project(self, temp_test_dir):
        """Create a large test project structure."""
        # Create a large test project structure
        structure = {}
        
        # Create 10 directories with 10 files each
        for i in range(10):
            dir_name = f"dir_{i}"
            structure[dir_name] = {}
            
            for j in range(10):
                file_name = f"file_{j}.py"
                structure[dir_name][file_name] = f"""
# Test file {i}_{j}

def function_{i}_{j}():
    \"\"\"Test function {i}_{j}.\"\"\"
    return {i} * {j}

class TestClass_{i}_{j}:
    \"\"\"Test class {i}_{j}.\"\"\"
    
    def __init__(self):
        \"\"\"Initialize the test class.\"\"\"
        self.value = {i} * {j}
    
    def test_method(self):
        \"\"\"Test method.\"\"\"
        return self.value
"""
        
        create_test_directory_structure(temp_test_dir, structure)
        
        return temp_test_dir
    
    def test_quality_check_performance(self, large_test_project, performance_metrics):
        """Benchmark the performance of quality checks."""
        # Create a mock enforcer
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class:
            # Create a mock enforcer instance
            mock_enforcer = MagicMock()
            
            # Mock the run_all_checks method to simulate realistic behavior
            def mock_run_checks(paths):
                # Simulate processing time based on the number of files
                num_files = sum(1 for _ in Path(large_test_project).glob("**/*.py"))
                time.sleep(0.001 * num_files)  # 1ms per file
                return mock_quality_results()
            
            mock_enforcer.run_all_checks.side_effect = mock_run_checks
            mock_enforcer_class.return_value = mock_enforcer
            
            # Create an enforcer instance
            from core.quality import QualityEnforcer
            enforcer = QualityEnforcer()
            
            # Benchmark the quality check performance
            performance_metrics.start_timer("run_all_checks")
            results = enforcer.run_all_checks([large_test_project])
            elapsed = performance_metrics.stop_timer("run_all_checks")
            
            # Record additional metrics
            performance_metrics.record_metric("run_all_checks", "num_results", len(results))
            performance_metrics.record_metric("run_all_checks", "num_files", sum(1 for _ in Path(large_test_project).glob("**/*.py")))
            
            # Verify the results
            assert results is not None
            assert elapsed > 0
            
            # Generate a performance report
            report_dir = os.path.join(large_test_project, "reports")
            os.makedirs(report_dir, exist_ok=True)
            performance_metrics.generate_report(os.path.join(report_dir, "quality_check_performance.json"))


@pytest.mark.performance
class TestFixOperationsPerformance:
    """Performance benchmarks for fix operations."""
    
    @pytest.fixture
    def performance_metrics(self):
        """Create a performance metrics collector."""
        return PerformanceMetrics("fix_operations_performance")
    
    def test_fix_operations_performance(self, temp_test_dir, performance_metrics):
        """Benchmark the performance of fix operations."""
        # Create a mock enforcer
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class:
            # Create a mock enforcer instance
            mock_enforcer = MagicMock()
            
            # Create a large set of quality results
            results = []
            for i in range(100):
                result = QualityCheckResult(
                    check_id=f"check_{i % 5}",
                    severity=QualityCheckSeverity.WARNING,
                    message=f"Issue {i}",
                    file_path=f"file_{i % 10}.py",
                    line_number=i * 10,
                    fix_available=True,
                    fix_command=f"fix_{i % 5} file_{i % 10}.py"
                )
                results.append(result)
            
            # Mock the fix_issues method to simulate realistic behavior
            def mock_fix_issues(results):
                # Simulate processing time based on the number of issues
                time.sleep(0.005 * len(results))  # 5ms per issue
                return []
            
            mock_enforcer.fix_issues.side_effect = mock_fix_issues
            mock_enforcer_class.return_value = mock_enforcer
            
            # Create an enforcer instance
            from core.quality import QualityEnforcer
            enforcer = QualityEnforcer()
            
            # Benchmark the fix operations performance
            performance_metrics.start_timer("fix_issues")
            unfixed = enforcer.fix_issues(results)
            elapsed = performance_metrics.stop_timer("fix_issues")
            
            # Record additional metrics
            performance_metrics.record_metric("fix_issues", "num_issues", len(results))
            performance_metrics.record_metric("fix_issues", "num_unfixed", len(unfixed))
            
            # Verify the results
            assert unfixed is not None
            assert elapsed > 0
            
            # Generate a performance report
            report_dir = os.path.join(temp_test_dir, "reports")
            os.makedirs(report_dir, exist_ok=True)
            performance_metrics.generate_report(os.path.join(report_dir, "fix_operations_performance.json"))


@pytest.mark.performance
class TestReportingPerformance:
    """Performance benchmarks for reporting."""
    
    @pytest.fixture
    def performance_metrics(self):
        """Create a performance metrics collector."""
        return PerformanceMetrics("reporting_performance")
    
    def test_reporting_performance(self, temp_test_dir, performance_metrics):
        """Benchmark the performance of reporting."""
        # Create a mock enforcer
        with patch('core.quality.QualityEnforcer') as mock_enforcer_class:
            # Create a mock enforcer instance
            mock_enforcer = MagicMock()
            
            # Create a large set of quality results
            results = []
            for i in range(100):
                result = QualityCheckResult(
                    check_id=f"check_{i % 5}",
                    severity=QualityCheckSeverity.WARNING,
                    message=f"Issue {i}",
                    file_path=f"file_{i % 10}.py",
                    line_number=i * 10,
                    fix_available=True,
                    fix_command=f"fix_{i % 5} file_{i % 10}.py"
                )
                results.append(result)
            
            # Mock the update_knowledge_graph method to simulate realistic behavior
            def mock_update_kg(results):
                # Simulate processing time based on the number of issues
                time.sleep(0.002 * len(results))  # 2ms per issue
            
            mock_enforcer.update_knowledge_graph.side_effect = mock_update_kg
            mock_enforcer_class.return_value = mock_enforcer
            
            # Create an enforcer instance
            from core.quality import QualityEnforcer
            enforcer = QualityEnforcer()
            
            # Benchmark the reporting performance
            performance_metrics.start_timer("update_knowledge_graph")
            enforcer.update_knowledge_graph(results)
            elapsed = performance_metrics.stop_timer("update_knowledge_graph")
            
            # Record additional metrics
            performance_metrics.record_metric("update_knowledge_graph", "num_issues", len(results))
            
            # Verify the results
            assert elapsed > 0
            
            # Generate a performance report
            report_dir = os.path.join(temp_test_dir, "reports")
            os.makedirs(report_dir, exist_ok=True)
            performance_metrics.generate_report(os.path.join(report_dir, "reporting_performance.json"))


@pytest.mark.performance
class TestPerformanceRegression:
    """Tests for performance regression detection."""
    
    @pytest.fixture
    def baseline_metrics(self, temp_test_dir):
        """Create baseline performance metrics."""
        # Create a baseline metrics file
        baseline = {
            "run_all_checks": {
                "elapsed": 0.5,
                "num_results": 100,
                "num_files": 100
            },
            "fix_issues": {
                "elapsed": 0.5,
                "num_issues": 100,
                "num_unfixed": 0
            },
            "update_knowledge_graph": {
                "elapsed": 0.2,
                "num_issues": 100
            }
        }
        
        baseline_dir = os.path.join(temp_test_dir, "baselines")
        os.makedirs(baseline_dir, exist_ok=True)
        baseline_path = os.path.join(baseline_dir, "performance_baseline.json")
        
        with open(baseline_path, "w") as f:
            json.dump(baseline, f, indent=2)
        
        return baseline_path
    
    def test_performance_regression_detection(self, temp_test_dir, baseline_metrics):
        """Test the performance regression detection."""
        # Create a performance metrics collector with the baseline
        metrics = PerformanceMetrics("regression_test", baseline_metrics)
        
        # Record some metrics
        metrics.record_metric("run_all_checks", "elapsed", 0.55)  # 10% slower
        metrics.record_metric("run_all_checks", "num_results", 100)
        metrics.record_metric("run_all_checks", "num_files", 100)
        
        metrics.record_metric("fix_issues", "elapsed", 0.6)  # 20% slower
        metrics.record_metric("fix_issues", "num_issues", 100)
        metrics.record_metric("fix_issues", "num_unfixed", 0)
        
        metrics.record_metric("update_knowledge_graph", "elapsed", 0.19)  # 5% faster
        metrics.record_metric("update_knowledge_graph", "num_issues", 100)
        
        # Compare with baseline
        run_checks_comparison = metrics.compare_with_baseline("run_all_checks", "elapsed")
        fix_issues_comparison = metrics.compare_with_baseline("fix_issues", "elapsed")
        update_kg_comparison = metrics.compare_with_baseline("update_knowledge_graph", "elapsed")
        
        # Verify the comparisons
        assert run_checks_comparison["regression"] is True  # 10% slower is a regression
        assert fix_issues_comparison["regression"] is True  # 20% slower is a regression
        assert update_kg_comparison["regression"] is False  # 5% faster is not a regression
        
        # Generate a performance report
        report_dir = os.path.join(temp_test_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)
        metrics.generate_report(os.path.join(report_dir, "regression_test.json"))