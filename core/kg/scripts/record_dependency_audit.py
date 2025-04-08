#!/usr/bin/env python3
"""
Record Dependency Audit Capabilities in Knowledge Graph

This script updates the knowledge graph with information about the dependency audit
capabilities implemented in the MCP-BASE-STACK project. It records:

1. The dependency audit script and its capabilities
2. The relationship between dependency auditing and quality enforcement
3. The types of dependencies that can be audited
4. The vulnerability checking capabilities

Usage:
    python record_dependency_audit.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import networkx as nx
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# Load the knowledge graph
def load_knowledge_graph(graph_path):
    """Load the knowledge graph from the specified path."""
    g = Graph()
    try:
        g.parse(graph_path, format="turtle")
        print(f"Loaded knowledge graph from {graph_path}")
        return g
    except Exception as e:
        print(f"Error loading knowledge graph: {e}")
        sys.exit(1)

# Define namespaces
MCP = Namespace("http://mcp-stack.org/ontology#")
MCPR = Namespace("http://mcp-stack.org/resource#")

def update_knowledge_graph(g):
    """Update the knowledge graph with dependency audit information."""
    # Add dependency audit script
    dependency_audit_script = MCPR.DependencyAuditScript
    g.add((dependency_audit_script, RDF.type, MCP.MaintenanceScript))
    g.add((dependency_audit_script, RDFS.label, Literal("Dependency Audit Script")))
    g.add((dependency_audit_script, RDFS.comment, Literal(
        "A script that audits project dependencies for outdated versions, vulnerabilities, and inconsistencies."
    )))
    g.add((dependency_audit_script, MCP.scriptPath, Literal("scripts/utils/maintenance/audit_dependencies.py")))
    g.add((dependency_audit_script, MCP.implementationDate, Literal("2025-04-08", datatype=XSD.date)))
    
    # Add dependency audit capabilities
    g.add((dependency_audit_script, MCP.hasCapability, MCPR.OutdatedDependencyDetection))
    g.add((dependency_audit_script, MCP.hasCapability, MCPR.VulnerabilityDetection))
    g.add((dependency_audit_script, MCP.hasCapability, MCPR.InconsistentDependencyDetection))
    g.add((dependency_audit_script, MCP.hasCapability, MCPR.DependencyRecommendations))
    
    # Define capabilities
    g.add((MCPR.OutdatedDependencyDetection, RDF.type, MCP.Capability))
    g.add((MCPR.OutdatedDependencyDetection, RDFS.label, Literal("Outdated Dependency Detection")))
    g.add((MCPR.OutdatedDependencyDetection, RDFS.comment, Literal(
        "Detects outdated dependencies by comparing current versions with latest available versions."
    )))
    
    g.add((MCPR.VulnerabilityDetection, RDF.type, MCP.Capability))
    g.add((MCPR.VulnerabilityDetection, RDFS.label, Literal("Vulnerability Detection")))
    g.add((MCPR.VulnerabilityDetection, RDFS.comment, Literal(
        "Identifies known security vulnerabilities in project dependencies."
    )))
    
    g.add((MCPR.InconsistentDependencyDetection, RDF.type, MCP.Capability))
    g.add((MCPR.InconsistentDependencyDetection, RDFS.label, Literal("Inconsistent Dependency Detection")))
    g.add((MCPR.InconsistentDependencyDetection, RDFS.comment, Literal(
        "Detects inconsistent dependency versions across different parts of the project."
    )))
    
    g.add((MCPR.DependencyRecommendations, RDF.type, MCP.Capability))
    g.add((MCPR.DependencyRecommendations, RDFS.label, Literal("Dependency Recommendations")))
    g.add((MCPR.DependencyRecommendations, RDFS.comment, Literal(
        "Provides actionable recommendations for fixing dependency issues."
    )))
    
    # Add supported dependency types
    g.add((dependency_audit_script, MCP.supportsDependencyType, MCPR.PythonDependency))
    g.add((dependency_audit_script, MCP.supportsDependencyType, MCPR.NodeDependency))
    g.add((dependency_audit_script, MCP.supportsDependencyType, MCPR.JavaDependency))
    g.add((dependency_audit_script, MCP.supportsDependencyType, MCPR.DockerDependency))
    
    # Define dependency types
    g.add((MCPR.PythonDependency, RDF.type, MCP.DependencyType))
    g.add((MCPR.PythonDependency, RDFS.label, Literal("Python Dependency")))
    g.add((MCPR.PythonDependency, MCP.filePattern, Literal("requirements.txt")))
    g.add((MCPR.PythonDependency, MCP.filePattern, Literal("setup.py")))
    g.add((MCPR.PythonDependency, MCP.filePattern, Literal("pyproject.toml")))
    g.add((MCPR.PythonDependency, MCP.filePattern, Literal("Pipfile")))
    
    g.add((MCPR.NodeDependency, RDF.type, MCP.DependencyType))
    g.add((MCPR.NodeDependency, RDFS.label, Literal("Node.js Dependency")))
    g.add((MCPR.NodeDependency, MCP.filePattern, Literal("package.json")))
    g.add((MCPR.NodeDependency, MCP.filePattern, Literal("yarn.lock")))
    g.add((MCPR.NodeDependency, MCP.filePattern, Literal("package-lock.json")))
    
    g.add((MCPR.JavaDependency, RDF.type, MCP.DependencyType))
    g.add((MCPR.JavaDependency, RDFS.label, Literal("Java Dependency")))
    g.add((MCPR.JavaDependency, MCP.filePattern, Literal("pom.xml")))
    g.add((MCPR.JavaDependency, MCP.filePattern, Literal("build.gradle")))
    g.add((MCPR.JavaDependency, MCP.filePattern, Literal("build.gradle.kts")))
    
    g.add((MCPR.DockerDependency, RDF.type, MCP.DependencyType))
    g.add((MCPR.DockerDependency, RDFS.label, Literal("Docker Dependency")))
    g.add((MCPR.DockerDependency, MCP.filePattern, Literal("Dockerfile")))
    g.add((MCPR.DockerDependency, MCP.filePattern, Literal("docker-compose.yml")))
    g.add((MCPR.DockerDependency, MCP.filePattern, Literal("docker-compose.yaml")))
    
    # Add relationship to quality enforcement
    quality_enforcer = MCPR.QualityEnforcer
    g.add((dependency_audit_script, MCP.integratesWith, quality_enforcer))
    g.add((quality_enforcer, MCP.hasComponent, MCPR.DependencyAuditComponent))
    
    g.add((MCPR.DependencyAuditComponent, RDF.type, MCP.QualityComponent))
    g.add((MCPR.DependencyAuditComponent, RDFS.label, Literal("Dependency Audit Component")))
    g.add((MCPR.DependencyAuditComponent, RDFS.comment, Literal(
        "A quality component that audits dependencies for issues and updates the knowledge graph."
    )))
    
    # Add relationship to knowledge graph
    g.add((dependency_audit_script, MCP.updatesKnowledgeGraph, Literal(True)))
    g.add((dependency_audit_script, MCP.knowledgeGraphUpdateMethod, Literal("QualityEnforcer.update_knowledge_graph")))
    
    print("Updated knowledge graph with dependency audit information")

def main():
    """Main entry point for the script."""
    # Define paths
    kg_path = os.path.join("core", "kg", "data", "knowledge_graph.ttl")
    
    # Load the knowledge graph
    g = load_knowledge_graph(kg_path)
    
    # Update the knowledge graph
    update_knowledge_graph(g)
    
    # Save the knowledge graph
    try:
        g.serialize(destination=kg_path, format="turtle")
        print(f"Saved knowledge graph to {kg_path}")
    except Exception as e:
        print(f"Error saving knowledge graph: {e}")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())