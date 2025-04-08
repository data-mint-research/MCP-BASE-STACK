"""
Test reporting and visualization utilities.

This module provides utilities for test result collection, performance visualization,
coverage reporting, and test trend analysis.
"""

import os
import json
import time
import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class TestResultCollector:
    """Collector for test results."""
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize the test result collector.
        
        Args:
            output_dir: Directory to store test results.
        """
        self.output_dir = output_dir
        self.results = []
        self.start_time = None
        self.end_time = None
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def start_test_run(self) -> None:
        """Start a test run."""
        self.start_time = time.time()
        self.results = []
    
    def add_result(self, test_name: str, result: Dict[str, Any]) -> None:
        """
        Add a test result.
        
        Args:
            test_name: Name of the test.
            result: Test result data.
        """
        self.results.append({
            "test_name": test_name,
            "timestamp": time.time(),
            "result": result
        })
    
    def end_test_run(self) -> Dict[str, Any]:
        """
        End a test run and return the summary.
        
        Returns:
            A dictionary containing the test run summary.
        """
        self.end_time = time.time()
        
        summary = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r["result"].get("status") == "passed"),
            "failed": sum(1 for r in self.results if r["result"].get("status") == "failed"),
            "skipped": sum(1 for r in self.results if r["result"].get("status") == "skipped"),
            "results": self.results
        }
        
        return summary
    
    def save_results(self, filename: str = None) -> str:
        """
        Save the test results to a file.
        
        Args:
            filename: Optional filename to save results to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved file.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        file_path = os.path.join(self.output_dir, filename)
        
        summary = self.end_test_run()
        
        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        return file_path


class PerformanceVisualizer:
    """Visualizer for performance data."""
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize the performance visualizer.
        
        Args:
            output_dir: Directory to store visualizations.
        """
        self.output_dir = output_dir
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def visualize_test_durations(
        self,
        test_durations: Dict[str, float],
        title: str = "Test Durations",
        filename: str = None
    ) -> str:
        """
        Visualize test durations as a bar chart.
        
        Args:
            test_durations: Dictionary mapping test names to durations.
            title: Title for the chart.
            filename: Optional filename to save the visualization to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved visualization.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_durations_{timestamp}.png"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Sort tests by duration
        sorted_tests = sorted(test_durations.items(), key=lambda x: x[1], reverse=True)
        test_names = [t[0] for t in sorted_tests]
        durations = [t[1] for t in sorted_tests]
        
        # Create the bar chart
        plt.figure(figsize=(12, 8))
        plt.barh(test_names, durations)
        plt.xlabel("Duration (seconds)")
        plt.ylabel("Test Name")
        plt.title(title)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(file_path)
        plt.close()
        
        return file_path
    
    def visualize_performance_comparison(
        self,
        current: Dict[str, float],
        baseline: Dict[str, float],
        title: str = "Performance Comparison",
        filename: str = None
    ) -> str:
        """
        Visualize performance comparison between current and baseline.
        
        Args:
            current: Dictionary mapping metric names to current values.
            baseline: Dictionary mapping metric names to baseline values.
            title: Title for the chart.
            filename: Optional filename to save the visualization to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved visualization.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_comparison_{timestamp}.png"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Get metrics that are in both current and baseline
        metrics = sorted(set(current.keys()) & set(baseline.keys()))
        
        if not metrics:
            raise ValueError("No common metrics found between current and baseline")
        
        # Get values for each metric
        current_values = [current[m] for m in metrics]
        baseline_values = [baseline[m] for m in metrics]
        
        # Calculate percentage change
        percent_change = [(c - b) / b * 100 if b != 0 else 0 for c, b in zip(current_values, baseline_values)]
        
        # Create the bar chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot absolute values
        x = np.arange(len(metrics))
        width = 0.35
        ax1.bar(x - width/2, baseline_values, width, label="Baseline")
        ax1.bar(x + width/2, current_values, width, label="Current")
        ax1.set_ylabel("Value")
        ax1.set_title("Absolute Values")
        ax1.set_xticks(x)
        ax1.set_xticklabels(metrics)
        ax1.legend()
        
        # Plot percentage change
        colors = ["green" if p <= 0 else "red" for p in percent_change]
        ax2.bar(metrics, percent_change, color=colors)
        ax2.set_ylabel("Percentage Change (%)")
        ax2.set_title("Percentage Change from Baseline")
        ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        
        plt.suptitle(title)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(file_path)
        plt.close()
        
        return file_path
    
    def visualize_performance_trend(
        self,
        metrics: Dict[str, List[Tuple[datetime.datetime, float]]],
        title: str = "Performance Trend",
        filename: str = None
    ) -> str:
        """
        Visualize performance trend over time.
        
        Args:
            metrics: Dictionary mapping metric names to lists of (timestamp, value) tuples.
            title: Title for the chart.
            filename: Optional filename to save the visualization to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved visualization.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_trend_{timestamp}.png"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Create the line chart
        plt.figure(figsize=(12, 8))
        
        for metric_name, data_points in metrics.items():
            timestamps = [d[0] for d in data_points]
            values = [d[1] for d in data_points]
            plt.plot(timestamps, values, marker="o", label=metric_name)
        
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.title(title)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(file_path)
        plt.close()
        
        return file_path


class CoverageReporter:
    """Reporter for test coverage."""
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize the coverage reporter.
        
        Args:
            output_dir: Directory to store coverage reports.
        """
        self.output_dir = output_dir
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_coverage_report(
        self,
        coverage_data: Dict[str, Any],
        title: str = "Test Coverage Report",
        filename: str = None
    ) -> str:
        """
        Generate a coverage report.
        
        Args:
            coverage_data: Coverage data.
            title: Title for the report.
            filename: Optional filename to save the report to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved report.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coverage_report_{timestamp}.json"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Add metadata to the coverage data
        report_data = {
            "title": title,
            "timestamp": datetime.datetime.now().isoformat(),
            "coverage": coverage_data
        }
        
        # Save the report
        with open(file_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        return file_path
    
    def visualize_coverage(
        self,
        coverage_data: Dict[str, float],
        title: str = "Test Coverage",
        filename: str = None
    ) -> str:
        """
        Visualize test coverage as a bar chart.
        
        Args:
            coverage_data: Dictionary mapping module names to coverage percentages.
            title: Title for the chart.
            filename: Optional filename to save the visualization to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved visualization.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coverage_visualization_{timestamp}.png"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Sort modules by coverage
        sorted_modules = sorted(coverage_data.items(), key=lambda x: x[1])
        module_names = [m[0] for m in sorted_modules]
        coverage_values = [m[1] for m in sorted_modules]
        
        # Create the bar chart
        plt.figure(figsize=(12, 8))
        bars = plt.barh(module_names, coverage_values)
        
        # Color the bars based on coverage
        for i, bar in enumerate(bars):
            if coverage_values[i] < 50:
                bar.set_color("red")
            elif coverage_values[i] < 80:
                bar.set_color("orange")
            else:
                bar.set_color("green")
        
        plt.xlabel("Coverage (%)")
        plt.ylabel("Module")
        plt.title(title)
        plt.xlim(0, 100)
        plt.tight_layout()
        
        # Save the chart
        plt.savefig(file_path)
        plt.close()
        
        return file_path


class TestTrendAnalyzer:
    """Analyzer for test trends."""
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize the test trend analyzer.
        
        Args:
            output_dir: Directory to store trend analysis.
        """
        self.output_dir = output_dir
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def analyze_test_trends(
        self,
        test_results: List[Dict[str, Any]],
        title: str = "Test Trend Analysis",
        filename: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze trends in test results.
        
        Args:
            test_results: List of test result summaries.
            title: Title for the analysis.
            filename: Optional filename to save the analysis to.
                If None, a default filename is generated.
                
        Returns:
            A tuple containing the path to the saved analysis and the analysis data.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_trend_analysis_{timestamp}.json"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Extract data for analysis
        timestamps = [r["start_time"] for r in test_results]
        dates = [datetime.datetime.fromtimestamp(t).date() for t in timestamps]
        total_tests = [r["total_tests"] for r in test_results]
        passed_tests = [r["passed"] for r in test_results]
        failed_tests = [r["failed"] for r in test_results]
        skipped_tests = [r["skipped"] for r in test_results]
        durations = [r["duration"] for r in test_results]
        
        # Calculate pass rates
        pass_rates = [p / t * 100 if t > 0 else 0 for p, t in zip(passed_tests, total_tests)]
        
        # Calculate trends
        total_trend = self._calculate_trend(total_tests)
        pass_rate_trend = self._calculate_trend(pass_rates)
        duration_trend = self._calculate_trend(durations)
        
        # Create analysis data
        analysis = {
            "title": title,
            "timestamp": datetime.datetime.now().isoformat(),
            "data": {
                "dates": [d.isoformat() for d in dates],
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "skipped_tests": skipped_tests,
                "pass_rates": pass_rates,
                "durations": durations
            },
            "trends": {
                "total_tests": total_trend,
                "pass_rate": pass_rate_trend,
                "duration": duration_trend
            }
        }
        
        # Save the analysis
        with open(file_path, "w") as f:
            json.dump(analysis, f, indent=2)
        
        return file_path, analysis
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate trend statistics for a list of values.
        
        Args:
            values: List of values.
            
        Returns:
            A dictionary containing trend statistics.
        """
        if not values:
            return {
                "mean": 0,
                "min": 0,
                "max": 0,
                "trend": 0,
                "trend_percentage": 0
            }
        
        # Calculate basic statistics
        mean = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        
        # Calculate trend (slope of linear regression)
        if len(values) < 2:
            trend = 0
            trend_percentage = 0
        else:
            x = list(range(len(values)))
            x_mean = sum(x) / len(x)
            y_mean = mean
            
            numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(len(values)))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(len(values)))
            
            trend = numerator / denominator if denominator != 0 else 0
            trend_percentage = (trend / y_mean) * 100 if y_mean != 0 else 0
        
        return {
            "mean": mean,
            "min": min_val,
            "max": max_val,
            "trend": trend,
            "trend_percentage": trend_percentage
        }
    
    def visualize_test_trends(
        self,
        analysis: Dict[str, Any],
        title: str = "Test Trends",
        filename: str = None
    ) -> str:
        """
        Visualize test trends.
        
        Args:
            analysis: Analysis data from analyze_test_trends.
            title: Title for the visualization.
            filename: Optional filename to save the visualization to.
                If None, a default filename is generated.
                
        Returns:
            The path to the saved visualization.
        """
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_trends_{timestamp}.png"
        
        file_path = os.path.join(self.output_dir, filename)
        
        # Extract data
        dates = [datetime.date.fromisoformat(d) for d in analysis["data"]["dates"]]
        total_tests = analysis["data"]["total_tests"]
        passed_tests = analysis["data"]["passed_tests"]
        failed_tests = analysis["data"]["failed_tests"]
        skipped_tests = analysis["data"]["skipped_tests"]
        pass_rates = analysis["data"]["pass_rates"]
        durations = analysis["data"]["durations"]
        
        # Create the visualization
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
        
        # Plot test counts
        ax1.plot(dates, total_tests, marker="o", label="Total")
        ax1.plot(dates, passed_tests, marker="o", label="Passed")
        ax1.plot(dates, failed_tests, marker="o", label="Failed")
        ax1.plot(dates, skipped_tests, marker="o", label="Skipped")
        ax1.set_ylabel("Count")
        ax1.set_title("Test Counts")
        ax1.legend()
        ax1.grid(True)
        
        # Plot pass rates
        ax2.plot(dates, pass_rates, marker="o", color="green")
        ax2.set_ylabel("Pass Rate (%)")
        ax2.set_title("Test Pass Rate")
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        
        # Plot durations
        ax3.plot(dates, durations, marker="o", color="blue")
        ax3.set_ylabel("Duration (seconds)")
        ax3.set_title("Test Duration")
        ax3.grid(True)
        
        plt.suptitle(title)
        plt.tight_layout()
        
        # Save the visualization
        plt.savefig(file_path)
        plt.close()
        
        return file_path