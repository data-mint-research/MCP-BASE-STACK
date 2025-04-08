"""
Test data generators for quality module tests.

This module provides generators for configuration data, file content,
quality issues, and knowledge graph data to support testing.
"""

import os
import random
import string
from typing import Dict, List, Optional, Any, Tuple, Union
import networkx as nx

from core.quality import QualityCheckResult, QualityCheckSeverity


def generate_config_data(
    components: Optional[List[str]] = None,
    include_optional: bool = True,
    randomize: bool = False
) -> Dict[str, Any]:
    """
    Generate configuration data for testing.
    
    Args:
        components: Optional list of component names to include.
            If None, default components are used.
        include_optional: Whether to include optional configuration parameters.
        randomize: Whether to randomize the configuration values.
        
    Returns:
        A dictionary containing configuration data.
    """
    if components is None:
        components = ["code_style", "static_analysis", "documentation", "structure"]
    
    if randomize:
        enabled = random.choice([True, False])
        selected_components = random.sample(components, random.randint(0, len(components)))
        severity_threshold = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
        auto_fix = random.choice([True, False])
    else:
        enabled = True
        selected_components = components
        severity_threshold = "WARNING"
        auto_fix = True
    
    config = {
        "enabled": enabled,
        "components": selected_components,
        "severity_threshold": severity_threshold,
        "auto_fix": auto_fix
    }
    
    if include_optional and (not randomize or random.choice([True, False])):
        config["report_dir"] = "data/reports"
        config["log_level"] = "INFO" if not randomize else random.choice(["DEBUG", "INFO", "WARNING", "ERROR"])
        config["max_issues_per_file"] = 10 if not randomize else random.randint(1, 100)
    
    return config


def generate_file_content(
    file_type: str = "python",
    include_issues: bool = False,
    num_issues: int = 3,
    file_size: str = "medium"
) -> str:
    """
    Generate file content for testing.
    
    Args:
        file_type: The type of file to generate content for.
            Supported types: "python", "markdown", "yaml", "json".
        include_issues: Whether to include quality issues in the content.
        num_issues: The number of quality issues to include.
        file_size: The size of the file to generate.
            Supported sizes: "small", "medium", "large".
            
    Returns:
        A string containing the generated file content.
    """
    # Determine the size of the file
    if file_size == "small":
        num_lines = random.randint(10, 30)
    elif file_size == "medium":
        num_lines = random.randint(50, 150)
    elif file_size == "large":
        num_lines = random.randint(200, 500)
    else:
        num_lines = random.randint(50, 150)
    
    # Generate content based on file type
    if file_type == "python":
        return _generate_python_content(num_lines, include_issues, num_issues)
    elif file_type == "markdown":
        return _generate_markdown_content(num_lines, include_issues, num_issues)
    elif file_type == "yaml":
        return _generate_yaml_content(num_lines, include_issues, num_issues)
    elif file_type == "json":
        return _generate_json_content(num_lines, include_issues, num_issues)
    else:
        return _generate_python_content(num_lines, include_issues, num_issues)


def _generate_python_content(num_lines: int, include_issues: bool, num_issues: int) -> str:
    """Generate Python file content."""
    lines = [
        '"""',
        "Example Python module.",
        "",
        "This module provides example functionality for testing.",
        '"""',
        "",
        "import os",
        "import sys",
        "import random",
        "from typing import Dict, List, Optional, Any",
        "",
        ""
    ]
    
    # Generate classes and functions
    num_classes = random.randint(1, 3)
    num_functions = random.randint(2, 5)
    
    for i in range(num_classes):
        class_name = f"ExampleClass{i+1}"
        lines.append(f"class {class_name}:")
        lines.append(f'    """Example class {i+1}."""')
        lines.append("")
        lines.append("    def __init__(self):")
        lines.append(f'        """Initialize the {class_name}."""')
        lines.append(f"        self.value = {i+1}")
        lines.append("")
        
        # Add methods
        num_methods = random.randint(2, 4)
        for j in range(num_methods):
            method_name = f"method_{j+1}"
            lines.append(f"    def {method_name}(self, param: int = {j+1}):")
            lines.append(f'        """Example method {j+1}."""')
            lines.append(f"        return self.value * param")
            lines.append("")
    
    for i in range(num_functions):
        function_name = f"example_function_{i+1}"
        lines.append(f"def {function_name}(param1: int, param2: Optional[str] = None) -> int:")
        lines.append(f'    """Example function {i+1}."""')
        lines.append("    result = param1")
        lines.append("    if param2:")
        lines.append("        result += len(param2)")
        lines.append("    return result")
        lines.append("")
    
    # Add a main block
    lines.append('if __name__ == "__main__":')
    lines.append("    # Example usage")
    lines.append(f"    obj = ExampleClass1()")
    lines.append(f"    print(obj.method_1(10))")
    lines.append(f"    print(example_function_1(5, 'test'))")
    
    # Add quality issues if requested
    if include_issues:
        issue_lines = []
        
        # Missing docstring
        if num_issues > 0:
            issue_lines.append(("def function_without_docstring(x, y):", "    return x + y", ""))
        
        # Unused import
        if num_issues > 1:
            issue_lines.append(("import datetime", "", ""))
        
        # Undefined variable
        if num_issues > 2:
            issue_lines.append(("def function_with_undefined_var():", "    return undefined_var", ""))
        
        # Too complex function
        if num_issues > 3:
            complex_func = [
                "def complex_function(x):",
                "    if x > 0:",
                "        if x > 10:",
                "            if x > 100:",
                "                return 'very large'",
                "            else:",
                "                return 'large'",
                "        else:",
                "            if x > 5:",
                "                return 'medium'",
                "            else:",
                "                return 'small'",
                "    else:",
                "        if x < -10:",
                "            if x < -100:",
                "                return 'very negative'",
                "            else:",
                "                return 'negative'",
                "        else:",
                "            if x < -5:",
                "                return 'slightly negative'",
                "            else:",
                "                return 'zero-ish'",
                ""
            ]
            issue_lines.append((complex_func[0], "\n".join(complex_func[1:]), ""))
        
        # Line too long
        if num_issues > 4:
            issue_lines.append((
                "# " + "x" * 100,
                "",
                ""
            ))
        
        # Insert issues at random positions
        for issue in issue_lines[:num_issues]:
            pos = random.randint(len(lines) // 4, 3 * len(lines) // 4)
            lines.insert(pos, issue[0])
            if issue[1]:
                lines.insert(pos + 1, issue[1])
            if issue[2]:
                lines.insert(pos + 2, issue[2])
    
    # Ensure we have at least the requested number of lines
    while len(lines) < num_lines:
        lines.append("")
    
    # Trim to the requested number of lines
    lines = lines[:num_lines]
    
    return "\n".join(lines)


def _generate_markdown_content(num_lines: int, include_issues: bool, num_issues: int) -> str:
    """Generate Markdown file content."""
    lines = [
        "# Example Markdown Document",
        "",
        "This is an example Markdown document for testing purposes.",
        "",
        "## Features",
        "",
        "- Feature 1",
        "- Feature 2",
        "- Feature 3",
        "",
        "## Usage",
        "",
        "```python",
        "import example",
        "",
        "result = example.function()",
        "print(result)",
        "```",
        "",
        "## API Reference",
        ""
    ]
    
    # Generate API reference sections
    num_sections = random.randint(3, 8)
    
    for i in range(num_sections):
        section_name = f"Function {i+1}"
        lines.append(f"### {section_name}")
        lines.append("")
        lines.append(f"`example.function_{i+1}(param1, param2=None)`")
        lines.append("")
        lines.append(f"Example function {i+1}.")
        lines.append("")
        lines.append("Parameters:")
        lines.append("- `param1` (int): The first parameter")
        lines.append("- `param2` (str, optional): The second parameter")
        lines.append("")
        lines.append("Returns:")
        lines.append("- `int`: The result")
        lines.append("")
    
    # Add quality issues if requested
    if include_issues:
        issue_lines = []
        
        # Missing heading hierarchy
        if num_issues > 0:
            issue_lines.append(("#### Skipped Heading Level", "", ""))
        
        # Broken link
        if num_issues > 1:
            issue_lines.append(("[Broken Link](http://example.com/broken)", "", ""))
        
        # Inconsistent formatting
        if num_issues > 2:
            issue_lines.append(("Some text with **bold** and _italic_ mixed styles", "", ""))
        
        # Insert issues at random positions
        for issue in issue_lines[:num_issues]:
            pos = random.randint(len(lines) // 4, 3 * len(lines) // 4)
            lines.insert(pos, issue[0])
            if issue[1]:
                lines.insert(pos + 1, issue[1])
            if issue[2]:
                lines.insert(pos + 2, issue[2])
    
    # Ensure we have at least the requested number of lines
    while len(lines) < num_lines:
        lines.append("")
    
    # Trim to the requested number of lines
    lines = lines[:num_lines]
    
    return "\n".join(lines)


def _generate_yaml_content(num_lines: int, include_issues: bool, num_issues: int) -> str:
    """Generate YAML file content."""
    lines = [
        "# Example YAML configuration",
        "version: 1.0",
        "",
        "settings:",
        "  debug: false",
        "  log_level: INFO",
        "  max_retries: 3",
        "",
        "components:"
    ]
    
    # Generate component entries
    num_components = random.randint(3, 8)
    
    for i in range(num_components):
        component_name = f"component_{i+1}"
        lines.append(f"  {component_name}:")
        lines.append(f"    enabled: true")
        lines.append(f"    version: 1.{i}")
        lines.append(f"    config:")
        lines.append(f"      param1: value{i+1}")
        lines.append(f"      param2: {i*10}")
        lines.append("")
    
    # Add quality issues if requested
    if include_issues:
        issue_lines = []
        
        # Inconsistent indentation
        if num_issues > 0:
            issue_lines.append(("  inconsistent:", "   indentation: error", ""))
        
        # Invalid YAML
        if num_issues > 1:
            issue_lines.append(("invalid: - [item1, item2]", "", ""))
        
        # Duplicate key
        if num_issues > 2:
            issue_lines.append(("settings:", "  debug: true", ""))
        
        # Insert issues at random positions
        for issue in issue_lines[:num_issues]:
            pos = random.randint(len(lines) // 4, 3 * len(lines) // 4)
            lines.insert(pos, issue[0])
            if issue[1]:
                lines.insert(pos + 1, issue[1])
            if issue[2]:
                lines.insert(pos + 2, issue[2])
    
    # Ensure we have at least the requested number of lines
    while len(lines) < num_lines:
        lines.append("")
    
    # Trim to the requested number of lines
    lines = lines[:num_lines]
    
    return "\n".join(lines)


def _generate_json_content(num_lines: int, include_issues: bool, num_issues: int) -> str:
    """Generate JSON file content."""
    # Start with a basic structure
    data = {
        "version": "1.0",
        "settings": {
            "debug": False,
            "logLevel": "INFO",
            "maxRetries": 3
        },
        "components": {}
    }
    
    # Generate component entries
    num_components = random.randint(3, 8)
    
    for i in range(num_components):
        component_name = f"component_{i+1}"
        data["components"][component_name] = {
            "enabled": True,
            "version": f"1.{i}",
            "config": {
                "param1": f"value{i+1}",
                "param2": i*10
            }
        }
    
    # Convert to formatted JSON string
    import json
    content = json.dumps(data, indent=2)
    
    # Add quality issues if requested
    if include_issues and num_issues > 0:
        lines = content.split("\n")
        
        # Introduce syntax errors
        for _ in range(min(num_issues, 3)):
            pos = random.randint(1, len(lines) - 2)
            if ":" in lines[pos]:
                # Remove a comma or add an extra comma
                if random.choice([True, False]):
                    lines[pos] = lines[pos].replace(",", "")
                else:
                    lines[pos] = lines[pos].replace(":", ":,")
        
        content = "\n".join(lines)
    
    # Ensure we have at least the requested number of lines
    lines = content.split("\n")
    while len(lines) < num_lines:
        lines.append("")
    
    # Trim to the requested number of lines
    lines = lines[:num_lines]
    
    return "\n".join(lines)


def generate_quality_issues(
    num_issues: int = 10,
    severity_distribution: Optional[Dict[str, float]] = None,
    file_paths: Optional[List[str]] = None,
    check_ids: Optional[List[str]] = None
) -> List[QualityCheckResult]:
    """
    Generate quality check results for testing.
    
    Args:
        num_issues: The number of issues to generate.
        severity_distribution: Optional dictionary mapping severity levels to
            their probability distribution. If None, a default distribution is used.
        file_paths: Optional list of file paths to use. If None, random paths are generated.
        check_ids: Optional list of check IDs to use. If None, default check IDs are used.
        
    Returns:
        A list of QualityCheckResult objects.
    """
    if severity_distribution is None:
        severity_distribution = {
            "INFO": 0.2,
            "WARNING": 0.5,
            "ERROR": 0.25,
            "CRITICAL": 0.05
        }
    
    if file_paths is None:
        file_paths = [
            "core/quality/enforcer.py",
            "core/quality/components/code_style.py",
            "core/quality/components/static_analysis.py",
            "core/quality/components/documentation.py",
            "core/quality/components/structure.py",
            "tests/test_quality.py",
            "tests/test_enforcer.py"
        ]
    
    if check_ids is None:
        check_ids = [
            "black",
            "mypy",
            "pylint",
            "flake8",
            "docstring",
            "import_order",
            "directory_structure"
        ]
    
    # Generate quality issues
    results = []
    
    for _ in range(num_issues):
        # Select severity based on distribution
        severity_rand = random.random()
        cumulative = 0
        selected_severity = QualityCheckSeverity.INFO
        
        for severity_name, probability in severity_distribution.items():
            cumulative += probability
            if severity_rand <= cumulative:
                selected_severity = getattr(QualityCheckSeverity, severity_name)
                break
        
        # Generate a quality check result
        result = QualityCheckResult(
            check_id=random.choice(check_ids),
            severity=selected_severity,
            message=f"Example quality issue: {_generate_random_string(20)}",
            file_path=random.choice(file_paths),
            line_number=random.randint(1, 100) if random.random() > 0.2 else None,
            fix_available=random.random() > 0.5,
            fix_command=f"fix_{random.choice(check_ids)} {random.choice(file_paths)}" if random.random() > 0.5 else None
        )
        
        results.append(result)
    
    return results


def _generate_random_string(length: int) -> str:
    """Generate a random string of the specified length."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def generate_knowledge_graph_data(
    num_nodes: int = 20,
    num_relationships: int = 30,
    node_types: Optional[List[str]] = None,
    relationship_types: Optional[List[str]] = None
) -> nx.DiGraph:
    """
    Generate knowledge graph data for testing.
    
    Args:
        num_nodes: The number of nodes to generate.
        num_relationships: The number of relationships to generate.
        node_types: Optional list of node types. If None, default types are used.
        relationship_types: Optional list of relationship types. If None, default types are used.
        
    Returns:
        A NetworkX DiGraph representing the knowledge graph.
    """
    if node_types is None:
        node_types = [
            "File",
            "Component",
            "QualityCheck",
            "QualityMetric",
            "Feature"
        ]
    
    if relationship_types is None:
        relationship_types = [
            "CONTAINS",
            "DEPENDS_ON",
            "HAS_CHECK",
            "HAS_METRIC",
            "IMPLEMENTS"
        ]
    
    # Create a directed graph
    g = nx.DiGraph()
    
    # Generate nodes
    for i in range(num_nodes):
        node_id = f"node_{i}"
        node_type = random.choice(node_types)
        
        # Generate node properties based on type
        properties = {
            "name": f"{node_type}_{i}",
            "type": node_type
        }
        
        if node_type == "File":
            properties["path"] = f"core/quality/{_generate_random_string(8)}.py"
        elif node_type == "Component":
            properties["status"] = random.choice(["active", "deprecated", "planned"])
        elif node_type == "QualityCheck":
            properties["severity"] = random.choice(["INFO", "WARNING", "ERROR", "CRITICAL"])
            properties["message"] = f"Example quality issue: {_generate_random_string(20)}"
        elif node_type == "QualityMetric":
            properties["value"] = str(random.uniform(0, 100))
            properties["threshold"] = str(random.uniform(0, 100))
        
        # Add the node to the graph
        g.add_node(node_id, **properties)
    
    # Generate relationships
    for _ in range(num_relationships):
        source_id = f"node_{random.randint(0, num_nodes-1)}"
        target_id = f"node_{random.randint(0, num_nodes-1)}"
        
        # Avoid self-relationships
        if source_id != target_id:
            relationship_type = random.choice(relationship_types)
            
            # Add the relationship to the graph
            g.add_edge(source_id, target_id, type=relationship_type)
    
    return g