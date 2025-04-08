import networkx as nx
import os
import sys
import json
import glob
from datetime import datetime
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS

# Configuration
KG_DATA_DIR = "core/kg/data"
PROJECT_NAME = "MCP-BASE-STACK"
QUALITY_REPORTS_DIR = "data/reports"
FILE_STRUCTURE_REPORT = "data/reports/file-structure-report.json"

def update_knowledge_graph():
    """Update the Knowledge Graph based on current implementation status"""
    # Load existing graphs
    try:
        nx_graph = nx.read_graphml(f"{KG_DATA_DIR}/knowledge_graph.graphml")
        rdf_graph = Graph()
        rdf_graph.parse(f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    except Exception as e:
        print(f"Error loading graphs: {e}")
        print("Please run setup_knowledge_graph.py first")
        sys.exit(1)
    
    # Namespace for RDF
    ns = Namespace(f"http://{PROJECT_NAME.lower()}.org/")
    
    # Update quality metrics in the knowledge graph
    update_quality_metrics(nx_graph, rdf_graph, ns)
    
    # Update file structure metrics in the knowledge graph
    update_file_structure_metrics(nx_graph, rdf_graph, ns)
    
    # Update implementation status based on file existence
    component_checks = [
        # Component ID, File to check, Status attribute
        ("nvidia_gpu", "nvidia-smi-output.txt", "verified"),
        ("docker", "docker-version.txt", "installed"),
        ("nvidia_container", "nvidia-container-output.txt", "configured"),
        ("librechat", "services/librechat/docker-compose.yml", "cloned"),
        ("librechat", "services/librechat/config/librechat.yaml", "configured"),
        ("librechat", "librechat-status.txt", "deployed"),
        ("llm_server", "data/logs/llm-server-status.txt", "deployed"),
        ("mistral", "mistral-model.txt", "loaded"),
        ("deepseek", "deepseek-model.txt", "loaded"),
        ("mcp_server", "services/mcp-server/src/app.py", "implemented"),
        ("documentation", "docs/README.md", "created"),
        ("tests", "tests/README.md", "created")
    ]
    
    # Update status based on file checks
    for component_id, check_file, status in component_checks:
        if os.path.exists(check_file):
            if component_id in nx_graph:
                nx_graph.nodes[component_id]['status'] = status
                
                # Update RDF
                rdf_graph.add((ns[component_id], ns.status, Literal(status)))
                
                print(f"Updated {component_id} status to '{status}'")
            else:
                # Add new component if it doesn't exist
                nx_graph.add_node(component_id, status=status, type="component")
                
                # Update RDF
                rdf_graph.add((ns[component_id], RDF.type, ns.Component))
                rdf_graph.add((ns[component_id], ns.status, Literal(status)))
                
                print(f"Added new component {component_id} with status '{status}'")
    # Automatically detect and track docs and tests directories
    update_directory_structure(nx_graph, rdf_graph, ns)
    
    # Save updated graphs
    nx.write_graphml(nx_graph, f"{KG_DATA_DIR}/knowledge_graph.graphml")
    rdf_graph.serialize(destination=f"{KG_DATA_DIR}/knowledge_graph.ttl", format="turtle")
    
    print("Knowledge Graph updated successfully.")

def update_file_structure_metrics(nx_graph, rdf_graph, ns):
    """Update file structure metrics in the knowledge graph based on latest file structure report"""
    print("Updating file structure metrics in knowledge graph...")
    
    if not os.path.exists(FILE_STRUCTURE_REPORT):
        print(f"File structure report not found at {FILE_STRUCTURE_REPORT}. Skipping file structure metrics update.")
        return
    
    try:
        # Load the file structure report
        with open(FILE_STRUCTURE_REPORT, 'r') as f:
            report_data = json.load(f)
        
        # Extract metrics
        total_files = report_data.get("total_files", 0)
        naming_compliance = report_data.get("naming_issues", {}).get("compliance_percentage", 0)
        directory_compliance = report_data.get("directory_issues", {}).get("compliance_percentage", 0)
        overall_compliance = report_data.get("overall_compliance_percentage", 0)
        
        # Update or create file structure metrics node
        node_id = "file_structure_metrics"
        if node_id in nx_graph:
            # Update existing node
            nx_graph.nodes[node_id]["last_modified"] = datetime.now().timestamp()
            nx_graph.nodes[node_id]["total_files"] = total_files
            nx_graph.nodes[node_id]["naming_compliance"] = naming_compliance
            nx_graph.nodes[node_id]["directory_compliance"] = directory_compliance
            nx_graph.nodes[node_id]["overall_compliance"] = overall_compliance
            nx_graph.nodes[node_id]["status"] = "updated"
            
            # Update RDF
            rdf_graph.add((ns[node_id], ns.last_modified, Literal(datetime.now().timestamp())))
            rdf_graph.add((ns[node_id], ns.total_files, Literal(total_files)))
            rdf_graph.add((ns[node_id], ns.naming_compliance, Literal(naming_compliance)))
            rdf_graph.add((ns[node_id], ns.directory_compliance, Literal(directory_compliance)))
            rdf_graph.add((ns[node_id], ns.overall_compliance, Literal(overall_compliance)))
            rdf_graph.add((ns[node_id], ns.status, Literal("updated")))
            
            print(f"Updated file structure metrics: {total_files} files, {naming_compliance}% naming compliance, {directory_compliance}% directory compliance")
        else:
            # Add new node
            nx_graph.add_node(
                node_id,
                name="File Structure Metrics",
                type="metrics",
                component_type="file_structure",
                description="File structure standardization metrics",
                last_modified=datetime.now().timestamp(),
                total_files=total_files,
                naming_compliance=naming_compliance,
                directory_compliance=directory_compliance,
                overall_compliance=overall_compliance,
                status="created"
            )
            
            # Update RDF
            rdf_graph.add((ns[node_id], RDF.type, ns.Metrics))
            rdf_graph.add((ns[node_id], ns.name, Literal("File Structure Metrics")))
            rdf_graph.add((ns[node_id], ns.component_type, Literal("file_structure")))
            rdf_graph.add((ns[node_id], ns.description, Literal("File structure standardization metrics")))
            rdf_graph.add((ns[node_id], ns.last_modified, Literal(datetime.now().timestamp())))
            rdf_graph.add((ns[node_id], ns.total_files, Literal(total_files)))
            rdf_graph.add((ns[node_id], ns.naming_compliance, Literal(naming_compliance)))
            rdf_graph.add((ns[node_id], ns.directory_compliance, Literal(directory_compliance)))
            rdf_graph.add((ns[node_id], ns.overall_compliance, Literal(overall_compliance)))
            rdf_graph.add((ns[node_id], ns.status, Literal("created")))
            
            # Create relationship with quality_metrics
            if "quality_metrics" in nx_graph:
                nx_graph.add_edge("quality_metrics", node_id, relationship="TRACKS")
                rdf_graph.add((ns["quality_metrics"], ns.TRACKS, ns[node_id]))
            
            print(f"Added new file structure metrics: {total_files} files, {naming_compliance}% naming compliance, {directory_compliance}% directory compliance")
    
    except Exception as e:
        print(f"Error updating file structure metrics: {e}")

def update_quality_metrics(nx_graph, rdf_graph, ns):
    """Update quality metrics in the knowledge graph based on latest quality reports"""
    print("Updating quality metrics in knowledge graph...")
    
    # Find the latest quality report
    report_files = glob.glob(f"{QUALITY_REPORTS_DIR}/code_quality_report_*.json")
    if not report_files:
        print("No quality reports found. Skipping quality metrics update.")
        return
    
    # Sort by modification time to get the latest report
    latest_report = max(report_files, key=os.path.getmtime)
    print(f"Using latest quality report: {latest_report}")
    
    try:
        # Load the quality report
        with open(latest_report, 'r') as f:
            report_data = json.load(f)
        
        # Update system-wide quality metrics node
        if "quality_metrics" in nx_graph:
            # Update timestamp
            nx_graph.nodes["quality_metrics"]["last_modified"] = datetime.now().timestamp()
            rdf_graph.add((ns["quality_metrics"], ns.last_modified, Literal(datetime.now().timestamp())))
            
            # Update status
            nx_graph.nodes["quality_metrics"]["status"] = "updated"
            rdf_graph.add((ns["quality_metrics"], ns.status, Literal("updated")))
            
            print("Updated quality_metrics node")
        
        # Process results from the report
        if "results" in report_data:
            # Group results by component
            results_by_component = {}
            
            for result in report_data["results"]:
                file_path = result.get("file_path", "")
                if file_path:
                    # Determine component from file path
                    component = file_path.split("/")[0] if "/" in file_path else "root"
                    
                    if component not in results_by_component:
                        results_by_component[component] = []
                    
                    results_by_component[component].append(result)
            
            # Update component quality metrics
            update_component_quality_metrics(nx_graph, rdf_graph, ns, "core", results_by_component.get("core", []))
            update_component_quality_metrics(nx_graph, rdf_graph, ns, "docs", results_by_component.get("docs", []))
            update_component_quality_metrics(nx_graph, rdf_graph, ns, "tests", results_by_component.get("tests", []))
        
        # Process summary metrics if available
        if "summary" in report_data:
            summary = report_data["summary"]
            print(f"Quality summary: {summary['total_checks']} checks, {summary['passed']} passed, {summary['failed']} failed")
    
    except Exception as e:
        print(f"Error updating quality metrics: {e}")

def update_component_quality_metrics(nx_graph, rdf_graph, ns, component_name, results):
    """Update quality metrics for a specific component"""
    quality_node_id = f"{component_name}_quality"
    
    if quality_node_id in nx_graph:
        # Count issues by severity
        severity_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
        
        for result in results:
            severity = result.get("severity", "info")
            severity_counts[severity] += 1
        
        # Update metrics in the graph
        nx_graph.nodes[quality_node_id]["issues_count"] = len(results)
        rdf_graph.add((ns[quality_node_id], ns.issues_count, Literal(len(results))))
        
        for severity, count in severity_counts.items():
            nx_graph.nodes[quality_node_id][f"{severity}_count"] = count
            rdf_graph.add((ns[quality_node_id], ns[f"{severity}_count"], Literal(count)))
        
        # Update last modified timestamp
        nx_graph.nodes[quality_node_id]["last_modified"] = datetime.now().timestamp()
        rdf_graph.add((ns[quality_node_id], ns.last_modified, Literal(datetime.now().timestamp())))
        
        print(f"Updated quality metrics for {component_name}: {len(results)} issues")
    print("Knowledge Graph updated successfully.")

def update_directory_structure(nx_graph, rdf_graph, ns):
    """Update the Knowledge Graph with directory structure information"""
    # Check for docs directory
    if os.path.exists("docs"):
        update_directory_info(nx_graph, rdf_graph, ns, "docs", "docs")
        
        # Process docs subdirectories
        for subdir in ["knowledge-graph", "tutorials", "troubleshooting", "conventions"]:
            if os.path.exists(f"docs/{subdir}"):
                update_directory_info(nx_graph, rdf_graph, ns, f"docs/{subdir}", f"docs_{subdir}")
                
                # Create relationship between docs and subdirectory
                if "docs" in nx_graph and f"docs_{subdir}" in nx_graph:
                    nx_graph.add_edge("docs", f"docs_{subdir}", relationship="contains")
                    rdf_graph.add((ns["docs"], ns.contains, ns[f"docs_{subdir}"]))
                
                # Count files in subdirectory
                file_count = len([f for f in os.listdir(f"docs/{subdir}") if f.endswith('.md')])
                if f"docs_{subdir}" in nx_graph:
                    nx_graph.nodes[f"docs_{subdir}"]["file_count"] = file_count
                    rdf_graph.add((ns[f"docs_{subdir}"], ns.file_count, Literal(file_count)))
    
    # Check for tests directory
    if os.path.exists("tests"):
        update_directory_info(nx_graph, rdf_graph, ns, "tests", "tests")
        
        # Process tests subdirectories
        test_subdirs = ["unit", "integration", "agent_tests", "e2e", "performance", "regression", "data"]
        for subdir in test_subdirs:
            if os.path.exists(f"tests/{subdir}"):
                update_directory_info(nx_graph, rdf_graph, ns, f"tests/{subdir}", f"tests_{subdir}")
                
                # Create relationship between tests and subdirectory
                if "tests" in nx_graph and f"tests_{subdir}" in nx_graph:
                    nx_graph.add_edge("tests", f"tests_{subdir}", relationship="contains")
                    rdf_graph.add((ns["tests"], ns.contains, ns[f"tests_{subdir}"]))
                
                # Count files in subdirectory recursively
                file_count = count_files_recursive(f"tests/{subdir}")
                if f"tests_{subdir}" in nx_graph:
                    nx_graph.nodes[f"tests_{subdir}"]["file_count"] = file_count
                    rdf_graph.add((ns[f"tests_{subdir}"], ns.file_count, Literal(file_count)))

def update_directory_info(nx_graph, rdf_graph, ns, path, node_id):
    """Add or update directory information in the graph"""
    if node_id in nx_graph:
        # Update existing node
        nx_graph.nodes[node_id]["path"] = path
        nx_graph.nodes[node_id]["last_modified"] = os.path.getmtime(path)
        
        # Update RDF
        rdf_graph.add((ns[node_id], ns.path, Literal(path)))
        rdf_graph.add((ns[node_id], ns.last_modified, Literal(os.path.getmtime(path))))
        
        print(f"Updated directory info for {node_id}")
    else:
        # Add new node
        nx_graph.add_node(
            node_id, 
            type="directory", 
            path=path, 
            last_modified=os.path.getmtime(path)
        )
        
        # Update RDF
        rdf_graph.add((ns[node_id], RDF.type, ns.Directory))
        rdf_graph.add((ns[node_id], ns.path, Literal(path)))
        rdf_graph.add((ns[node_id], ns.last_modified, Literal(os.path.getmtime(path))))
        
        print(f"Added new directory {node_id}")

def count_files_recursive(directory):
    """Count files recursively in a directory"""
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def register_feature(nx_graph, rdf_graph, ns, feature_id, name, description, owner, status="planned"):
    """Register a new feature in the Knowledge Graph"""
    if feature_id in nx_graph:
        # Update existing feature
        nx_graph.nodes[feature_id]["name"] = name
        nx_graph.nodes[feature_id]["description"] = description
        nx_graph.nodes[feature_id]["owner"] = owner
        nx_graph.nodes[feature_id]["status"] = status
        
        # Update RDF
        rdf_graph.add((ns[feature_id], ns.name, Literal(name)))
        rdf_graph.add((ns[feature_id], ns.description, Literal(description)))
        rdf_graph.add((ns[feature_id], ns.owner, Literal(owner)))
        rdf_graph.add((ns[feature_id], ns.status, Literal(status)))
        
        print(f"Updated feature {feature_id}")
    else:
        # Add new feature
        nx_graph.add_node(
            feature_id, 
            type="feature", 
            name=name, 
            description=description, 
            owner=owner, 
            status=status
        )
        
        # Update RDF
        rdf_graph.add((ns[feature_id], RDF.type, ns.Feature))
        rdf_graph.add((ns[feature_id], ns.name, Literal(name)))
        rdf_graph.add((ns[feature_id], ns.description, Literal(description)))
        rdf_graph.add((ns[feature_id], ns.owner, Literal(owner)))
        rdf_graph.add((ns[feature_id], ns.status, Literal(status)))
        
        print(f"Added new feature {feature_id}")
def update_component_status(nx_graph, rdf_graph, ns, component_id, status):
    """
    Update the status of a component in the knowledge graph.
    
    Args:
        nx_graph: NetworkX graph
        rdf_graph: RDF graph
        ns: Namespace
        component_id: Component ID
        status: New status
    """
    if component_id in nx_graph:
        # Update existing component
        nx_graph.nodes[component_id]['status'] = status
        
        # Update RDF
        rdf_graph.add((ns[component_id], ns.status, Literal(status)))
        
        print(f"Updated {component_id} status to '{status}'")
    else:
        # Add new component if it doesn't exist
        nx_graph.add_node(component_id, status=status, type="component")
        
        # Update RDF
        rdf_graph.add((ns[component_id], RDF.type, ns.Component))
        rdf_graph.add((ns[component_id], ns.status, Literal(status)))
        
        print(f"Added new component {component_id} with status '{status}'")

if __name__ == "__main__":
    update_knowledge_graph()
    update_knowledge_graph()