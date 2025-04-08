#!/usr/bin/env python3
"""
Record the code quality tooling in the knowledge graph.

This script records the code quality configuration files and scripts
as a migration decision in the knowledge graph, documenting the
rationale and purpose.
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"

try:
    import networkx as nx
    from rdflib import Graph, Namespace, Literal, URIRef
    from rdflib.namespace import RDF, RDFS
except ImportError as e:
    logger.error(f"Could not import required libraries: {e}")
    logger.error("Make sure networkx and rdflib are installed.")
    sys.exit(1)


def load_knowledge_graph():
    """Load the knowledge graph from files."""
    try:
        nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph = Graph()
        rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
        return nx_graph, rdf_graph
    except Exception as e:
        logger.error(f"Error loading knowledge graph: {e}")
        logger.error("Make sure the knowledge graph files exist and are valid.")
        sys.exit(1)


def save_knowledge_graph(nx_graph, rdf_graph):
    """Save the knowledge graph to files."""
    try:
        nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
        logger.info("Knowledge graph saved successfully.")
    except Exception as e:
        logger.error(f"Error saving knowledge graph: {e}")
        sys.exit(1)


def record_config_file(nx_graph, rdf_graph, file_id, file_name, file_path, file_description, file_language):
    """Record a configuration file in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the file node already exists
    if file_id in nx_graph:
        logger.info(f"File {file_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[file_id]["name"] = file_name
        nx_graph.nodes[file_id]["path"] = file_path
        nx_graph.nodes[file_id]["description"] = file_description
        nx_graph.nodes[file_id]["language"] = file_language
        nx_graph.nodes[file_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding file {file_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            file_id,
            type="file",
            name=file_name,
            path=file_path,
            description=file_description,
            language=file_language,
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    file_uri = ns[file_id]
    rdf_graph.add((file_uri, RDF.type, ns.File))
    rdf_graph.add((file_uri, ns.name, Literal(file_name)))
    rdf_graph.add((file_uri, ns.path, Literal(file_path)))
    rdf_graph.add((file_uri, ns.description, Literal(file_description)))
    rdf_graph.add((file_uri, ns.language, Literal(file_language)))
    rdf_graph.add((file_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to code_quality component if it exists
    if "code_quality" in nx_graph:
        if not nx_graph.has_edge("code_quality", file_id):
            logger.info(f"Connecting {file_id} to code_quality component...")
            nx_graph.add_edge("code_quality", file_id, relation="contains")
            rdf_graph.add((ns["code_quality"], ns.contains, file_uri))
    else:
        logger.warning("code_quality component node not found in the knowledge graph.")
    
    return True


def record_script_file(nx_graph, rdf_graph, script_id, script_name, script_path, script_description):
    """Record a script file in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the script node already exists
    if script_id in nx_graph:
        logger.info(f"Script {script_id} already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes[script_id]["name"] = script_name
        nx_graph.nodes[script_id]["path"] = script_path
        nx_graph.nodes[script_id]["description"] = script_description
        nx_graph.nodes[script_id]["language"] = "shell"
        nx_graph.nodes[script_id]["last_modified"] = datetime.now().timestamp()
    else:
        logger.info(f"Adding script {script_id} to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            script_id,
            type="file",
            name=script_name,
            path=script_path,
            description=script_description,
            language="shell",
            last_modified=datetime.now().timestamp()
        )
    
    # Update RDF graph
    script_uri = ns[script_id]
    rdf_graph.add((script_uri, RDF.type, ns.File))
    rdf_graph.add((script_uri, ns.name, Literal(script_name)))
    rdf_graph.add((script_uri, ns.path, Literal(script_path)))
    rdf_graph.add((script_uri, ns.description, Literal(script_description)))
    rdf_graph.add((script_uri, ns.language, Literal("shell")))
    rdf_graph.add((script_uri, ns.last_modified, Literal(datetime.now().timestamp())))
    
    # Connect to code_quality component if it exists
    if "code_quality" in nx_graph:
        if not nx_graph.has_edge("code_quality", script_id):
            logger.info(f"Connecting {script_id} to code_quality component...")
            nx_graph.add_edge("code_quality", script_id, relation="contains")
            rdf_graph.add((ns["code_quality"], ns.contains, script_uri))
    else:
        logger.warning("code_quality component node not found in the knowledge graph.")
    
    return True


def add_code_quality_component(nx_graph, rdf_graph):
    """Add or update the code quality component in the knowledge graph."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Check if the component already exists
    if "code_quality" in nx_graph:
        logger.info("Code quality component already exists in the knowledge graph. Updating...")
        # Update existing node
        nx_graph.nodes["code_quality"]["status"] = "implemented"
    else:
        logger.info("Adding code quality component to the knowledge graph...")
        # Add new node
        nx_graph.add_node(
            "code_quality",
            type="component",
            name="Code Quality",
            description="Code quality standards and tools",
            status="implemented"
        )
    
    # Update RDF graph
    component_uri = ns["code_quality"]
    rdf_graph.add((component_uri, RDF.type, ns.Component))
    rdf_graph.add((component_uri, ns.name, Literal("Code Quality")))
    rdf_graph.add((component_uri, ns.description, Literal("Code quality standards and tools")))
    rdf_graph.add((component_uri, ns.status, Literal("implemented")))
    
    # Connect to project_root if not already connected
    if not nx_graph.has_edge("project_root", "code_quality"):
        logger.info("Connecting code_quality component to project_root...")
        nx_graph.add_edge("project_root", "code_quality", relation="contains")
        rdf_graph.add((ns["project_root"], ns.contains, component_uri))
    
    return True


def record_migration_decision(nx_graph, rdf_graph):
    """Record the creation of code quality tooling as a migration decision."""
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Generate a unique ID for the decision
    decision_id = f"decision_code_quality_tooling_{int(datetime.now().timestamp())}"
    
    # Add the decision node
    nx_graph.add_node(
        decision_id,
        type="decision",
        name="Implementation of Code Quality Tooling",
        description="Implementation of code quality configuration files and scripts",
        rationale="To enforce code quality standards and automate quality checks for the MCP-BASE-STACK project",
        timestamp=datetime.now().isoformat()
    )
    
    # Update RDF graph
    decision_uri = ns[decision_id]
    rdf_graph.add((decision_uri, RDF.type, ns.Decision))
    rdf_graph.add((decision_uri, ns.name, Literal("Implementation of Code Quality Tooling")))
    rdf_graph.add((decision_uri, ns.description, Literal("Implementation of code quality configuration files and scripts")))
    rdf_graph.add((decision_uri, ns.rationale, Literal("To enforce code quality standards and automate quality checks for the MCP-BASE-STACK project")))
    rdf_graph.add((decision_uri, ns.timestamp, Literal(datetime.now().isoformat())))
    
    # Connect to code_quality component
    if "code_quality" in nx_graph:
        nx_graph.add_edge("code_quality", decision_id, relation="has_decision")
        rdf_graph.add((ns["code_quality"], ns.has_decision, decision_uri))
    
    return True


def main():
    """Record the code quality tooling in the knowledge graph."""
    try:
        # Load the knowledge graph
        nx_graph, rdf_graph = load_knowledge_graph()
        
        # Add or update the code quality component
        add_code_quality_component(nx_graph, rdf_graph)
        
        # Record each configuration file
        config_files = [
            {
                "id": "pyproject_toml",
                "name": "pyproject.toml",
                "path": "pyproject.toml",
                "description": "Configuration for Black and isort Python formatters",
                "language": "toml"
            },
            {
                "id": "flake8_config",
                "name": ".flake8",
                "path": ".flake8",
                "description": "Configuration for flake8 Python linter",
                "language": "ini"
            },
            {
                "id": "mypy_config",
                "name": "mypy.ini",
                "path": "mypy.ini",
                "description": "Configuration for mypy Python type checker",
                "language": "ini"
            },
            {
                "id": "pylint_config",
                "name": ".pylintrc",
                "path": ".pylintrc",
                "description": "Configuration for pylint Python linter",
                "language": "ini"
            },
            {
                "id": "shellcheck_config",
                "name": ".shellcheckrc",
                "path": ".shellcheckrc",
                "description": "Configuration for shellcheck shell script linter",
                "language": "ini"
            },
            {
                "id": "pre_commit_config",
                "name": ".pre-commit-config.yaml",
                "path": ".pre-commit-config.yaml",
                "description": "Configuration for pre-commit hooks",
                "language": "yaml"
            }
        ]
        
        for config in config_files:
            record_config_file(
                nx_graph, 
                rdf_graph, 
                config["id"], 
                config["name"], 
                config["path"], 
                config["description"],
                config["language"]
            )
        
        # Record each script file
        script_files = [
            {
                "id": "check_code_quality_script",
                "name": "check_code_quality.sh",
                "path": "scripts/utils/quality/check_code_quality.sh",
                "description": "Script to check code quality using various tools"
            },
            {
                "id": "fix_code_quality_script",
                "name": "fix_code_quality.sh",
                "path": "scripts/utils/quality/fix_code_quality.sh",
                "description": "Script to automatically fix code quality issues"
            },
            {
                "id": "install_pre_commit_hooks_script",
                "name": "install_pre_commit_hooks.sh",
                "path": "scripts/utils/installation/install_pre_commit_hooks.sh",
                "description": "Script to install pre-commit hooks for code quality checks"
            },
            {
                "id": "analyze_code_script",
                "name": "analyze_code.py",
                "path": "scripts/utils/analysis/analyze_code.py",
                "description": "Script to analyze code structure and patterns"
            },
            {
                "id": "check_kg_nodes_script",
                "name": "check_kg_nodes.py",
                "path": "scripts/utils/analysis/check_kg_nodes.py",
                "description": "Script to check knowledge graph nodes"
            },
            {
                "id": "traverse_project_script",
                "name": "traverse_project.py",
                "path": "scripts/utils/analysis/traverse_project.py",
                "description": "Script to traverse the project structure"
            },
            {
                "id": "validate_manifest_script",
                "name": "validate-manifest.py",
                "path": "scripts/utils/validation/validate-manifest.py",
                "description": "Script to validate the project manifest"
            },
            {
                "id": "verify_stack_health_script",
                "name": "verify_stack_health.sh",
                "path": "scripts/utils/validation/verify_stack_health.sh",
                "description": "Script to verify the health of the stack"
            }
        ]
        
        for script in script_files:
            record_script_file(
                nx_graph, 
                rdf_graph, 
                script["id"], 
                script["name"], 
                script["path"], 
                script["description"]
            )
        
        # Record the migration decision
        record_migration_decision(nx_graph, rdf_graph)
        
        # Save the knowledge graph
        save_knowledge_graph(nx_graph, rdf_graph)
        
        logger.info("Code quality tooling successfully recorded in the knowledge graph")
        return True
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()