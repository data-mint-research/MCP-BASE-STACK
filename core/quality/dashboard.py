"""
Quality Metrics Dashboard Module

This module provides a centralized dashboard for quality metrics, trend analysis,
and improvement tracking. It integrates with the knowledge graph to provide
a single source of truth for quality metrics across the project.
"""

import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from flask import Flask, render_template, jsonify, request, send_from_directory

from core.config.settings import get_config
from core.quality.enforcer import QualityEnforcer

logger = logging.getLogger(__name__)

# Constants
REPORTS_DIR = Path("data/reports")
DASHBOARD_DIR = Path("data/dashboard")
DASHBOARD_STATIC_DIR = DASHBOARD_DIR / "static"
DASHBOARD_TEMPLATES_DIR = DASHBOARD_DIR / "templates"
KG_PATH = Path("core/kg/data/knowledge_graph.graphml")

class QualityMetricsDashboard:
    """
    Centralized dashboard for quality metrics, trend analysis, and improvement tracking.
    
    This class provides a web-based dashboard for visualizing quality metrics,
    analyzing trends over time, and tracking improvements.
    """
    
    def __init__(self):
        """Initialize the Quality Metrics Dashboard."""
        self.app = Flask(__name__, 
                         static_folder=str(DASHBOARD_STATIC_DIR),
                         template_folder=str(DASHBOARD_TEMPLATES_DIR))
        self.enforcer = QualityEnforcer()
        self._setup_routes()
        self._ensure_directories()
        
    def _ensure_directories(self) -> None:
        """Ensure that required directories exist."""
        DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
        DASHBOARD_STATIC_DIR.mkdir(parents=True, exist_ok=True)
        DASHBOARD_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        
    def _setup_routes(self) -> None:
        """Set up Flask routes for the dashboard."""
        
        @self.app.route('/')
        def index():
            """Render the main dashboard page."""
            return render_template('index.html')
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get the latest quality metrics."""
            metrics = self._get_latest_metrics()
            return jsonify(metrics)
        
        @self.app.route('/api/trends')
        def get_trends():
            """Get trend data for quality metrics."""
            days = request.args.get('days', default=30, type=int)
            trends = self._get_trend_data(days)
            return jsonify(trends)
        
        @self.app.route('/api/components')
        def get_components():
            """Get quality metrics for all components."""
            components = self._get_component_metrics()
            return jsonify(components)
        
        @self.app.route('/api/improvements')
        def get_improvements():
            """Get improvement tracking data."""
            improvements = self._get_improvement_data()
            return jsonify(improvements)
        
        @self.app.route('/api/run-checks', methods=['POST'])
        def run_checks():
            """Run quality checks and update metrics."""
            try:
                results = self.enforcer.run_all_checks()
                self.enforcer.update_knowledge_graph(results)
                return jsonify({"status": "success", "message": "Quality checks completed successfully"})
            except Exception as e:
                logger.error(f"Error running quality checks: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
    
    def _get_latest_metrics(self) -> Dict[str, Any]:
        """
        Get the latest quality metrics from reports and knowledge graph.
        
        Returns:
            Dictionary containing the latest quality metrics.
        """
        # Get the latest code quality report
        code_quality_reports = list(REPORTS_DIR.glob("code_quality_report_*.json"))
        if not code_quality_reports:
            logger.warning("No code quality reports found")
            return {}
        
        latest_report = max(code_quality_reports, key=os.path.getmtime)
        
        try:
            with open(latest_report, 'r') as f:
                quality_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading quality report: {e}")
            quality_data = {}
        
        # Get file structure metrics
        try:
            with open(REPORTS_DIR / "file_structure_metrics.json", 'r') as f:
                structure_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading file structure metrics: {e}")
            structure_data = {}
        
        # Get dependency audit data
        try:
            with open(REPORTS_DIR / "dependency-audit-report.json", 'r') as f:
                dependency_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading dependency audit report: {e}")
            dependency_data = {}
        
        # Combine metrics from different sources
        metrics = {
            "timestamp": datetime.datetime.now().isoformat(),
            "code_quality": quality_data.get("summary", {}),
            "file_structure": structure_data.get("file_structure_metrics", {}),
            "dependencies": dependency_data.get("summary", {})
        }
        
        # Add knowledge graph metrics if available
        kg_metrics = self._get_metrics_from_knowledge_graph()
        if kg_metrics:
            metrics["knowledge_graph"] = kg_metrics
        
        return metrics
    
    def _get_metrics_from_knowledge_graph(self) -> Dict[str, Any]:
        """
        Extract quality metrics from the knowledge graph.
        
        Returns:
            Dictionary containing quality metrics from the knowledge graph.
        """
        try:
            if not KG_PATH.exists():
                logger.warning(f"Knowledge graph file not found: {KG_PATH}")
                return {}
            
            # Load the knowledge graph
            graph = nx.read_graphml(KG_PATH)
            
            # Extract quality metrics nodes
            metrics = {}
            
            # Find the central quality metrics node
            if "quality_metrics" in graph:
                metrics["status"] = graph.nodes["quality_metrics"].get("status", "unknown")
                metrics["last_modified"] = graph.nodes["quality_metrics"].get("last_modified", 0)
            
            # Extract component quality metrics
            component_metrics = {}
            for node_id, attrs in graph.nodes(data=True):
                if node_id.endswith("_quality") and attrs.get("type") == "quality_metric":
                    component_name = node_id.replace("_quality", "")
                    component_metrics[component_name] = {
                        "complexity_cyclomatic": attrs.get("complexity_cyclomatic", 0),
                        "complexity_cognitive": attrs.get("complexity_cognitive", 0),
                        "type_hint_coverage": attrs.get("type_hint_coverage", 0),
                        "documentation_coverage": attrs.get("documentation_coverage", 0),
                        "test_coverage": attrs.get("test_coverage", 0),
                        "issues_count": attrs.get("issues_count", 0),
                        "info_count": attrs.get("info_count", 0),
                        "warning_count": attrs.get("warning_count", 0),
                        "error_count": attrs.get("error_count", 0),
                        "critical_count": attrs.get("critical_count", 0)
                    }
            
            if component_metrics:
                metrics["components"] = component_metrics
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error extracting metrics from knowledge graph: {e}")
            return {}
    
    def _get_trend_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get trend data for quality metrics over time.
        
        Args:
            days: Number of days to include in the trend data.
            
        Returns:
            Dictionary containing trend data for various metrics.
        """
        # Get all code quality reports within the specified time range
        code_quality_reports = list(REPORTS_DIR.glob("code_quality_report_*.json"))
        
        # Filter reports by date if needed
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        trend_data = {
            "timestamps": [],
            "code_quality": {
                "issues_count": [],
                "passed": [],
                "failed": []
            },
            "file_structure": {
                "naming_compliance": [],
                "directory_compliance": [],
                "overall_compliance": []
            }
        }
        
        # Process code quality reports
        for report_path in sorted(code_quality_reports, key=os.path.getmtime):
            try:
                with open(report_path, 'r') as f:
                    report_data = json.load(f)
                
                # Extract timestamp
                timestamp = report_data.get("timestamp", "")
                if not timestamp:
                    continue
                
                report_date = datetime.datetime.fromisoformat(timestamp)
                if report_date < cutoff_date:
                    continue
                
                # Add data to trends
                trend_data["timestamps"].append(timestamp)
                
                summary = report_data.get("summary", {})
                trend_data["code_quality"]["issues_count"].append(len(report_data.get("results", [])))
                trend_data["code_quality"]["passed"].append(summary.get("passed", 0))
                trend_data["code_quality"]["failed"].append(summary.get("failed", 0))
                
            except Exception as e:
                logger.error(f"Error processing report {report_path}: {e}")
        
        # Process file structure metrics history
        structure_history = self._get_file_structure_history(days)
        if structure_history:
            trend_data["file_structure"] = structure_history
        
        # Add improvement tracking data
        improvements = self._get_improvement_data()
        if improvements:
            trend_data["improvements"] = improvements
        
        return trend_data
    
    def _get_file_structure_history(self, days: int = 30) -> Dict[str, List[float]]:
        """
        Get historical data for file structure metrics.
        
        Args:
            days: Number of days to include in the history.
            
        Returns:
            Dictionary containing historical data for file structure metrics.
        """
        # This would typically come from a database or time-series data
        # For now, we'll use the latest file structure metrics as a placeholder
        try:
            with open(REPORTS_DIR / "file_structure_metrics.json", 'r') as f:
                structure_data = json.load(f)
            
            metrics = structure_data.get("file_structure_metrics", {})
            
            # Create a simple history with the current value repeated
            history = {
                "naming_compliance": [metrics.get("naming_compliance", 0)] * 5,
                "directory_compliance": [metrics.get("directory_compliance", 0)] * 5,
                "overall_compliance": [metrics.get("overall_compliance", 0)] * 5
            }
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting file structure history: {e}")
            return {}
    
    def _get_component_metrics(self) -> Dict[str, Any]:
        """
        Get quality metrics for all components.
        
        Returns:
            Dictionary containing quality metrics for each component.
        """
        # Extract component metrics from the knowledge graph
        kg_metrics = self._get_metrics_from_knowledge_graph()
        component_metrics = kg_metrics.get("components", {})
        
        # Add additional component data if available
        # This could include more detailed metrics from other sources
        
        return component_metrics
    
    def _get_improvement_data(self) -> Dict[str, Any]:
        """
        Get improvement tracking data.
        
        Returns:
            Dictionary containing improvement tracking data.
        """
        # Initialize improvement tracking data
        improvements = {
            "metrics": [],
            "targets": [],
            "current": [],
            "previous": [],
            "change": []
        }
        
        # Get current metrics
        current_metrics = self._get_latest_metrics()
        
        # Define key metrics to track
        key_metrics = [
            {"name": "Documentation Coverage", "key": "documentation_coverage", "target": 0.95, "source": "knowledge_graph"},
            {"name": "Type Hint Coverage", "key": "type_hint_coverage", "target": 0.90, "source": "knowledge_graph"},
            {"name": "File Structure Compliance", "key": "overall_compliance", "target": 95.0, "source": "file_structure"},
            {"name": "Code Quality Issues", "key": "issues_count", "target": 0, "source": "code_quality", "lower_is_better": True}
        ]
        
        # Get previous metrics (for now, we'll use slightly modified current metrics as a placeholder)
        # In a real implementation, this would come from historical data
        previous_metrics = {
            "code_quality": {
                "issues_count": current_metrics.get("code_quality", {}).get("issues_count", 0) + 2
            },
            "file_structure": {
                "overall_compliance": current_metrics.get("file_structure", {}).get("overall_compliance", 0) - 1.5
            },
            "knowledge_graph": {
                "components": {
                    "core": {
                        "documentation_coverage": 0.85,
                        "type_hint_coverage": 0.82
                    }
                }
            }
        }
        
        # Calculate improvements for each metric
        for metric in key_metrics:
            improvements["metrics"].append(metric["name"])
            improvements["targets"].append(metric["target"])
            
            # Get current value
            if metric["source"] == "knowledge_graph":
                current_value = current_metrics.get("knowledge_graph", {}).get("components", {}).get("core", {}).get(metric["key"], 0)
            else:
                current_value = current_metrics.get(metric["source"], {}).get(metric["key"], 0)
            
            improvements["current"].append(current_value)
            
            # Get previous value
            if metric["source"] == "knowledge_graph":
                previous_value = previous_metrics.get("knowledge_graph", {}).get("components", {}).get("core", {}).get(metric["key"], 0)
            else:
                previous_value = previous_metrics.get(metric["source"], {}).get(metric["key"], 0)
            
            improvements["previous"].append(previous_value)
            
            # Calculate change
            change = current_value - previous_value
            if metric.get("lower_is_better", False):
                change = -change
            
            improvements["change"].append(change)
        
        return improvements
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
        """
        Run the dashboard web application.
        
        Args:
            host: Host to run the server on.
            port: Port to run the server on.
            debug: Whether to run in debug mode.
        """
        self._generate_dashboard_files()
        self.app.run(host=host, port=port, debug=debug)
    
    def _generate_dashboard_files(self) -> None:
        """Generate the necessary files for the dashboard."""
        self._generate_index_template()
        self._generate_css()
        self._generate_js()
    
    def _generate_index_template(self) -> None:
        """Generate the index.html template for the dashboard."""
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quality Metrics Dashboard</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <h1>Quality Metrics Dashboard</h1>
        <div class="last-updated">Last updated: <span id="last-updated">Loading...</span></div>
        <button id="refresh-btn">Refresh Metrics</button>
    </header>
    
    <div class="dashboard-container">
        <div class="metrics-summary">
            <h2>Summary</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Documentation Coverage</h3>
                    <div class="metric-value" id="documentation-coverage">-</div>
                    <div class="metric-trend" id="documentation-trend"></div>
                </div>
                <div class="metric-card">
                    <h3>Type Hint Coverage</h3>
                    <div class="metric-value" id="type-hint-coverage">-</div>
                    <div class="metric-trend" id="type-hint-trend"></div>
                </div>
                <div class="metric-card">
                    <h3>File Structure Compliance</h3>
                    <div class="metric-value" id="file-structure-compliance">-</div>
                    <div class="metric-trend" id="file-structure-trend"></div>
                </div>
                <div class="metric-card">
                    <h3>Quality Issues</h3>
                    <div class="metric-value" id="quality-issues">-</div>
                    <div class="metric-trend" id="issues-trend"></div>
                </div>
            </div>
        </div>
        
        <div class="dashboard-section">
            <h2>Trend Analysis</h2>
            <div class="chart-container">
                <canvas id="trends-chart"></canvas>
            </div>
        </div>
        
        <div class="dashboard-section">
            <h2>Component Metrics</h2>
            <div class="component-grid" id="component-grid">
                <!-- Component cards will be added here dynamically -->
            </div>
        </div>
        
        <div class="dashboard-section">
            <h2>Improvement Tracking</h2>
            <div class="improvement-container">
                <table class="improvement-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Target</th>
                            <th>Current</th>
                            <th>Previous</th>
                            <th>Change</th>
                        </tr>
                    </thead>
                    <tbody id="improvement-table-body">
                        <!-- Improvement data will be added here dynamically -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script src="{{ url_for('static', filename='dashboard.js') }}"></script>
</body>
</html>
"""
        
        # Ensure the templates directory exists
        DASHBOARD_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write the template file
        with open(DASHBOARD_TEMPLATES_DIR / "index.html", "w") as f:
            f.write(index_html)
    
    def _generate_css(self) -> None:
        """Generate the CSS file for the dashboard."""
        css = """/* Quality Metrics Dashboard Styles */

:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --success-color: #2ecc71;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
    --light-color: #ecf0f1;
    --dark-color: #34495e;
    --text-color: #333;
    --background-color: #f8f9fa;
    --card-background: #fff;
    --border-color: #ddd;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--background-color);
    padding: 0;
    margin: 0;
}

header {
    background-color: var(--secondary-color);
    color: white;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

header h1 {
    font-size: 1.5rem;
    margin: 0;
}

.last-updated {
    font-size: 0.9rem;
    opacity: 0.8;
}

#refresh-btn {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.3s;
}

#refresh-btn:hover {
    background-color: #2980b9;
}

.dashboard-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.dashboard-section {
    margin-bottom: 2rem;
    background-color: var(--card-background);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
}

.dashboard-section h2 {
    margin-bottom: 1rem;
    color: var(--secondary-color);
    font-size: 1.3rem;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.5rem;
}

.metrics-summary {
    margin-bottom: 2rem;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
}

.metric-card {
    background-color: var(--card-background);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    text-align: center;
}

.metric-card h3 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
    color: var(--dark-color);
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.metric-trend {
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.trend-up {
    color: var(--success-color);
}

.trend-down {
    color: var(--danger-color);
}

.chart-container {
    height: 400px;
    margin-top: 1rem;
}

.component-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
}

.component-card {
    background-color: var(--card-background);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
}

.component-card h3 {
    font-size: 1.1rem;
    margin-bottom: 1rem;
    color: var(--dark-color);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.5rem;
}

.component-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
}

.component-metric {
    margin-bottom: 0.5rem;
}

.component-metric-label {
    font-size: 0.9rem;
    color: var(--dark-color);
}

.component-metric-value {
    font-size: 1.1rem;
    font-weight: bold;
    color: var(--primary-color);
}

.improvement-container {
    overflow-x: auto;
}

.improvement-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

.improvement-table th,
.improvement-table td {
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

.improvement-table th {
    background-color: var(--light-color);
    font-weight: 600;
    color: var(--dark-color);
}

.improvement-table tr:hover {
    background-color: rgba(236, 240, 241, 0.5);
}

.positive-change {
    color: var(--success-color);
}

.negative-change {
    color: var(--danger-color);
}

.progress-bar-container {
    width: 100%;
    height: 8px;
    background-color: var(--light-color);
    border-radius: 4px;
    overflow: hidden;
    margin-top: 0.25rem;
}

.progress-bar {
    height: 100%;
    background-color: var(--primary-color);
    border-radius: 4px;
}

@media (max-width: 768px) {
    header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    header h1 {
        margin-bottom: 0.5rem;
    }
    
    .last-updated {
        margin-bottom: 0.5rem;
    }
    
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    
    .component-grid {
        grid-template-columns: 1fr;
    }
}
"""
        
        # Ensure the static directory exists
        DASHBOARD_STATIC_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write the CSS file
        with open(DASHBOARD_STATIC_DIR / "styles.css", "w") as f:
            f.write(css)
    
    def _generate_js(self) -> None:
        """Generate the JavaScript file for the dashboard."""
        js = """// Quality Metrics Dashboard JavaScript

// Global variables
let trendsChart = null;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadDashboardData();
    
    // Set up refresh button
    document.getElementById('refresh-btn').addEventListener('click', function() {
        runQualityChecks();
    });
});

// Load all dashboard data
function loadDashboardData() {
    // Load metrics
    fetch('/api/metrics')
        .then(response => response.json())
        .then(data => {
            updateSummaryMetrics(data);
            updateLastUpdated(data.timestamp);
        })
        .catch(error => console.error('Error loading metrics:', error));
    
    // Load trend data
    fetch('/api/trends')
        .then(response => response.json())
        .then(data => {
            updateTrendChart(data);
        })
        .catch(error => console.error('Error loading trends:', error));
    
    // Load component metrics
    fetch('/api/components')
        .then(response => response.json())
        .then(data => {
            updateComponentMetrics(data);
        })
        .catch(error => console.error('Error loading component metrics:', error));
    
    // Load improvement data
    fetch('/api/improvements')
        .then(response => response.json())
        .then(data => {
            updateImprovementTracking(data);
        })
        .catch(error => console.error('Error loading improvement data:', error));
}

// Update summary metrics
function updateSummaryMetrics(data) {
    // Documentation coverage
    const docCoverage = data.knowledge_graph?.components?.core?.documentation_coverage || 0;
    document.getElementById('documentation-coverage').textContent = formatPercentage(docCoverage);
    
    // Type hint coverage
    const typeHintCoverage = data.knowledge_graph?.components?.core?.type_hint_coverage || 0;
    document.getElementById('type-hint-coverage').textContent = formatPercentage(typeHintCoverage);
    
    // File structure compliance
    const fileStructureCompliance = data.file_structure?.overall_compliance || 0;
    document.getElementById('file-structure-compliance').textContent = formatPercentage(fileStructureCompliance / 100);
    
    // Quality issues
    const qualityIssues = data.code_quality?.total_checks || 0;
    document.getElementById('quality-issues').textContent = qualityIssues;
}

// Update last updated timestamp
function updateLastUpdated(timestamp) {
    const date = new Date(timestamp);
    document.getElementById('last-updated').textContent = date.toLocaleString();
}

// Update trend chart
function updateTrendChart(data) {
    const ctx = document.getElementById('trends-chart').getContext('2d');
    
    // Format dates for display
    const labels = data.timestamps.map(ts => {
        const date = new Date(ts);
        return date.toLocaleDateString();
    });
    
    // Destroy existing chart if it exists
    if (trendsChart) {
        trendsChart.destroy();
    }
    
    // Create new chart
    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Quality Issues',
                    data: data.code_quality?.issues_count || [],
                    borderColor: '#e74c3c',
                    backgroundColor: 'rgba(231, 76, 60, 0.1)',
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'File Structure Compliance',
                    data: data.file_structure?.overall_compliance || [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.1,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Quality Metrics Trends'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Value'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Update component metrics
function updateComponentMetrics(data) {
    const componentGrid = document.getElementById('component-grid');
    componentGrid.innerHTML = '';
    
    // Create a card for each component
    for (const [componentName, metrics] of Object.entries(data)) {
        const card = document.createElement('div');
        card.className = 'component-card';
        
        // Create card content
        card.innerHTML = `
            <h3>${componentName}</h3>
            <div class="component-metrics">
                <div class="component-metric">
                    <div class="component-metric-label">Documentation Coverage</div>
                    <div class="component-metric-value">${formatPercentage(metrics.documentation_coverage || 0)}</div>
                </div>
                <div class="component-metric">
                    <div class="component-metric-label">Type Hint Coverage</div>
                    <div class="component-metric-value">${formatPercentage(metrics.type_hint_coverage || 0)}</div>
                </div>
                <div class="component-metric">
                    <div class="component-metric-label">Issues</div>
                    <div class="component-metric-value">${metrics.issues_count || 0}</div>
                </div>
                <div class="component-metric">
                    <div class="component-metric-label">Complexity</div>
                    <div class="component-metric-value">${metrics.complexity_cyclomatic || 0}</div>
                </div>
            </div>
        `;
        
        // Add card to grid
        componentGrid.appendChild(card);
    }
    
    // If no components, show a message
    if (Object.keys(data).length === 0) {
        componentGrid.innerHTML = '<p>No component metrics available.</p>';
    }
}

// Update improvement tracking
function updateImprovementTracking(data) {
    const tableBody = document.getElementById('improvement-table-body');
    tableBody.innerHTML = '';
    
    // Create a row for each metric
    for (let i = 0; i < data.metrics.length; i++) {
        const row = document.createElement('tr');
        
        // Calculate change class
        const changeValue = data.change[i];
        const changeClass = changeValue > 0 ? 'positive-change' : (changeValue < 0 ? 'negative-change' : '');
        
        // Create row content
        row.innerHTML = `
            <td>${data.metrics[i]}</td>
            <td>${formatValue(data.targets[i])}</td>
            <td>${formatValue(data.current[i])}</td>
            <td>${formatValue(data.previous[i])}</td>
            <td class="${changeClass}">${formatChange(changeValue)}</td>
        `;
        
        // Add row to table
        tableBody.appendChild(row);
    }
    
    // If no metrics, show a message
    if (data.metrics.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5">No improvement data available.</td></tr>';
    }
}

// Run quality checks
function runQualityChecks() {
    // Show loading state
    document.getElementById('refresh-btn').textContent = 'Running...';
    document.getElementById('refresh-btn').disabled = true;
    
    // Run checks
    fetch('/api/run-checks', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Reload dashboard data
                loadDashboardData();
                alert('Quality checks completed successfully.');
            } else {
                alert(`Error running quality checks: ${data.message}`);
            }
        })
        .catch(error => {
            console.error('Error running quality checks:', error);
            alert('Error running quality checks. See console for details.');
        })
        .finally(() => {
            // Reset button
            document.getElementById('refresh-btn').textContent = 'Refresh Metrics';
            document.getElementById('refresh-btn').disabled = false;
        });
}

// Format percentage value
function formatPercentage(value) {
    return `${(value * 100).toFixed(1)}%`;
}

// Format change value
function formatChange(value) {
    if (value === 0) return '0';
    return value > 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
}

// Format value based on type
function formatValue(value) {
    if (typeof value === 'number') {
        // If it's a percentage (between 0 and 1)
        if (value >= 0 && value <= 1) {
            return formatPercentage(value);
        }
        // If it's a percentage (between 0 and 100)
        else if (value >= 0 && value <= 100 && value.toString().includes('.')) {
            return `${value.toFixed(1)}%`;
        }
        // Otherwise, just format the number
        return value.toFixed(0);
    }
    return value;
}
"""
        
        # Ensure the static directory exists
        DASHBOARD_STATIC_DIR.mkdir(parents=True, exist_ok=True)
        
        # Write the JavaScript file
        with open(DASHBOARD_STATIC_DIR / "dashboard.js", "w") as f:
            f.write(js)
