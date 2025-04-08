#!/usr/bin/env python3
"""
MCP Migration - Architecture Design Script

This script takes the analysis report as input and designs the MCP architecture.
It defines the components, interfaces, and data flows for the MCP architecture
based on the MCP Host-Client-Server model.

Usage:
    python design_mcp_architecture.py [--analysis-report PATH] [--target-structure PATH] [--output PATH]

Arguments:
    --analysis-report PATH     Path to the analysis report JSON file (default: data/migration/mcp/analysis_report.json)
    --target-structure PATH    Path to the target structure YAML file (default: scripts/migration/mcp/structure.yaml)
    --output PATH              Path to output the architecture design (default: data/migration/mcp/architecture_design.json)
    --verbose                  Enable verbose logging
    --help                     Show this help message and exit
"""

import os
import sys
import json
import yaml
import logging
import argparse
from typing import Dict, List, Any, Tuple, Set, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mcp_architecture_design.log")
    ]
)
logger = logging.getLogger("mcp_architecture_design")


@dataclass
class Interface:
    """Represents an interface between components."""
    name: str
    source_component: str
    target_component: str
    description: str
    methods: List[Dict[str, Any]] = field(default_factory=list)
    protocol: str = "JSON-RPC"
    version: str = "2.0"


@dataclass
class DataFlow:
    """Represents a data flow between components."""
    name: str
    source_component: str
    target_component: str
    description: str
    data_type: str
    direction: str  # "one-way" or "bidirectional"
    transport: str  # "synchronous" or "asynchronous"


@dataclass
class Component:
    """Represents a component in the MCP architecture."""
    name: str
    type: str  # "host", "client", "server", "tool", "resource", etc.
    description: str
    path: str
    required_files: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    subcomponents: List[str] = field(default_factory=list)
    migration_status: str = "pending"  # "pending", "in-progress", "complete"
    implementation_priority: int = 0  # 0-5, where 0 is highest priority


@dataclass
class ArchitectureDesign:
    """Represents the MCP architecture design."""
    components: List[Component] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    data_flows: List[DataFlow] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_report_path: str = ""
    target_structure_path: str = ""


class ArchitectureDesigner:
    """Designs the MCP architecture based on the analysis report."""

    def __init__(self, analysis_report_path: str, target_structure_path: str, verbose: bool = False):
        """
        Initialize the ArchitectureDesigner.

        Args:
            analysis_report_path: Path to the analysis report JSON file
            target_structure_path: Path to the target structure YAML file
            verbose: Whether to enable verbose logging
        """
        self.analysis_report_path = analysis_report_path
        self.target_structure_path = target_structure_path
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.info(f"Initializing ArchitectureDesigner with analysis report: {self.analysis_report_path}")
        logger.info(f"Target structure path: {self.target_structure_path}")
        
        # Validate paths
        self._validate_paths()
        
        # Load analysis report
        self.analysis_report = self._load_analysis_report()
        
        # Load target structure
        self.target_structure = self._load_target_structure()
        
        # Initialize architecture design
        self.design = ArchitectureDesign(
            analysis_report_path=self.analysis_report_path,
            target_structure_path=self.target_structure_path
        )
        
        # Component registry to keep track of all components
        self.component_registry: Dict[str, Component] = {}
        
        # Interface registry to keep track of all interfaces
        self.interface_registry: Dict[str, Interface] = {}

    def _validate_paths(self) -> None:
        """Validate that the specified paths exist."""
        if not os.path.exists(self.analysis_report_path):
            raise FileNotFoundError(f"Analysis report file does not exist: {self.analysis_report_path}")
        
        if not os.path.exists(self.target_structure_path):
            raise FileNotFoundError(f"Target structure file does not exist: {self.target_structure_path}")

    def _load_analysis_report(self) -> Dict[str, Any]:
        """
        Load the analysis report from the JSON file.
        
        Returns:
            Dict[str, Any]: The analysis report as a dictionary
        """
        try:
            with open(self.analysis_report_path, 'r') as f:
                report = json.load(f)
                logger.debug(f"Loaded analysis report with {len(report.get('components', []))} components")
                return report
        except Exception as e:
            logger.error(f"Error loading analysis report: {str(e)}")
            raise

    def _load_target_structure(self) -> Dict[str, Any]:
        """
        Load the target structure from the YAML file.
        
        Returns:
            Dict[str, Any]: The target structure as a dictionary
        """
        try:
            with open(self.target_structure_path, 'r') as f:
                structure = yaml.safe_load(f)
                logger.debug(f"Loaded target structure: {structure}")
                return structure
        except Exception as e:
            logger.error(f"Error loading target structure: {str(e)}")
            raise

    def design_architecture(self) -> ArchitectureDesign:
        """
        Design the MCP architecture based on the analysis report.
        
        Returns:
            ArchitectureDesign: The architecture design
        """
        logger.info("Starting architecture design...")
        
        # Define the core MCP components (Host, Client, Server)
        self._define_core_components()
        
        # Define interfaces between core components
        self._define_core_interfaces()
        
        # Define data flows between core components
        self._define_core_data_flows()
        
        # Process tools and resources
        self._process_tools_and_resources()
        
        # Set implementation priorities
        self._set_implementation_priorities()
        
        # Add components to the design
        self.design.components = list(self.component_registry.values())
        
        # Add interfaces to the design
        self.design.interfaces = list(self.interface_registry.values())
        
        logger.info("Architecture design completed")
        return self.design

    def _define_core_components(self) -> None:
        """Define the core MCP components (Host, Client, Server)."""
        logger.info("Defining core MCP components...")
        
        # Define Host component
        host_component = Component(
            name="MCPHost",
            type="host",
            description="Coordinates multiple clients, manages consent, and context",
            path="services/mcp-server/src/host",
            required_files=[
                "services/mcp-server/src/host/__init__.py",
                "services/mcp-server/src/host/host.py",
                "services/mcp-server/src/host/consent_manager.py",
                "services/mcp-server/src/host/context_manager.py",
                "services/mcp-server/src/host/server_registry.py",
                "services/mcp-server/src/host/client_registry.py"
            ],
            dependencies=[]
        )
        self.component_registry["MCPHost"] = host_component
        
        # Define Client component
        client_component = Component(
            name="MCPClient",
            type="client",
            description="One per server, routes JSON-RPC, handles subscriptions",
            path="services/mcp-server/src/client",
            required_files=[
                "services/mcp-server/src/client/__init__.py",
                "services/mcp-server/src/client/client.py",
                "services/mcp-server/src/client/subscription_manager.py",
                "services/mcp-server/src/client/request_handler.py",
                "services/mcp-server/src/client/response_handler.py"
            ],
            dependencies=["MCPHost"]
        )
        self.component_registry["MCPClient"] = client_component
        
        # Define Server component
        server_component = Component(
            name="MCPServer",
            type="server",
            description="Stateless capability provider",
            path="services/mcp-server/src/server",
            required_files=[
                "services/mcp-server/src/server/__init__.py",
                "services/mcp-server/src/server/server.py",
                "services/mcp-server/src/server/capability_manager.py"
            ],
            dependencies=["MCPHost"]
        )
        self.component_registry["MCPServer"] = server_component
        
        # Define DI Container component
        di_component = Component(
            name="DependencyInjection",
            type="infrastructure",
            description="Dependency injection container for MCP components",
            path="services/mcp-server/src/di",
            required_files=[
                "services/mcp-server/src/di/__init__.py",
                "services/mcp-server/src/di/containers.py",
                "services/mcp-server/src/di/providers.py"
            ],
            dependencies=["MCPHost", "MCPClient", "MCPServer"]
        )
        self.component_registry["DependencyInjection"] = di_component
        
        logger.debug(f"Defined {len(self.component_registry)} core components")

    def _define_core_interfaces(self) -> None:
        """Define the interfaces between core MCP components."""
        logger.info("Defining core MCP interfaces...")
        
        # Host-Client Interface
        host_client_interface = Interface(
            name="HostClientInterface",
            source_component="MCPHost",
            target_component="MCPClient",
            description="Interface for communication between Host and Client",
            methods=[
                {
                    "name": "register_client",
                    "description": "Register a client with the host",
                    "parameters": ["client_id", "client_info"],
                    "return_type": "registration_result"
                },
                {
                    "name": "unregister_client",
                    "description": "Unregister a client from the host",
                    "parameters": ["client_id"],
                    "return_type": "unregistration_result"
                },
                {
                    "name": "route_request",
                    "description": "Route a request from client to server",
                    "parameters": ["client_id", "server_id", "request"],
                    "return_type": "response"
                }
            ]
        )
        self.interface_registry["HostClientInterface"] = host_client_interface
        
        # Host-Server Interface
        host_server_interface = Interface(
            name="HostServerInterface",
            source_component="MCPHost",
            target_component="MCPServer",
            description="Interface for communication between Host and Server",
            methods=[
                {
                    "name": "register_server",
                    "description": "Register a server with the host",
                    "parameters": ["server_id", "server_info"],
                    "return_type": "registration_result"
                },
                {
                    "name": "unregister_server",
                    "description": "Unregister a server from the host",
                    "parameters": ["server_id"],
                    "return_type": "unregistration_result"
                },
                {
                    "name": "handle_request",
                    "description": "Handle a request from a client",
                    "parameters": ["client_id", "request"],
                    "return_type": "response"
                }
            ]
        )
        self.interface_registry["HostServerInterface"] = host_server_interface
        
        # Client-Server Interface (via Host)
        client_server_interface = Interface(
            name="ClientServerInterface",
            source_component="MCPClient",
            target_component="MCPServer",
            description="Interface for communication between Client and Server (via Host)",
            methods=[
                {
                    "name": "execute_tool",
                    "description": "Execute a tool on the server",
                    "parameters": ["tool_name", "arguments"],
                    "return_type": "tool_result"
                },
                {
                    "name": "access_resource",
                    "description": "Access a resource from the server",
                    "parameters": ["resource_uri"],
                    "return_type": "resource_data"
                },
                {
                    "name": "subscribe_to_resource",
                    "description": "Subscribe to updates for a resource",
                    "parameters": ["resource_uri", "callback_id"],
                    "return_type": "subscription_result"
                }
            ]
        )
        self.interface_registry["ClientServerInterface"] = client_server_interface
        
        # Update component interfaces
        self.component_registry["MCPHost"].interfaces = ["HostClientInterface", "HostServerInterface"]
        self.component_registry["MCPClient"].interfaces = ["HostClientInterface", "ClientServerInterface"]
        self.component_registry["MCPServer"].interfaces = ["HostServerInterface", "ClientServerInterface"]
        
        logger.debug(f"Defined {len(self.interface_registry)} core interfaces")

    def _define_core_data_flows(self) -> None:
        """Define the data flows between core MCP components."""
        logger.info("Defining core MCP data flows...")
        
        # Host to Client data flow
        host_to_client_flow = DataFlow(
            name="HostToClientFlow",
            source_component="MCPHost",
            target_component="MCPClient",
            description="Data flow from Host to Client for responses and notifications",
            data_type="JSON-RPC messages",
            direction="bidirectional",
            transport="synchronous"
        )
        
        # Client to Host data flow
        client_to_host_flow = DataFlow(
            name="ClientToHostFlow",
            source_component="MCPClient",
            target_component="MCPHost",
            description="Data flow from Client to Host for requests",
            data_type="JSON-RPC messages",
            direction="bidirectional",
            transport="synchronous"
        )
        
        # Host to Server data flow
        host_to_server_flow = DataFlow(
            name="HostToServerFlow",
            source_component="MCPHost",
            target_component="MCPServer",
            description="Data flow from Host to Server for requests",
            data_type="JSON-RPC messages",
            direction="bidirectional",
            transport="synchronous"
        )
        
        # Server to Host data flow
        server_to_host_flow = DataFlow(
            name="ServerToHostFlow",
            source_component="MCPServer",
            target_component="MCPHost",
            description="Data flow from Server to Host for responses and notifications",
            data_type="JSON-RPC messages",
            direction="bidirectional",
            transport="synchronous"
        )
        
        # Resource subscription flow
        resource_subscription_flow = DataFlow(
            name="ResourceSubscriptionFlow",
            source_component="MCPServer",
            target_component="MCPClient",
            description="Data flow for resource subscription updates",
            data_type="Resource updates",
            direction="one-way",
            transport="asynchronous"
        )
        
        # Add data flows to the design
        self.design.data_flows = [
            host_to_client_flow,
            client_to_host_flow,
            host_to_server_flow,
            server_to_host_flow,
            resource_subscription_flow
        ]
        
        logger.debug(f"Defined {len(self.design.data_flows)} core data flows")

    def _process_tools_and_resources(self) -> None:
        """Process tools and resources from the target structure."""
        logger.info("Processing tools and resources...")
        
        # Get the structure definition from the loaded YAML
        structure_def = self.target_structure.get("structure", {})
        
        # Process server tools
        if "services" in structure_def and "mcp-server" in structure_def["services"]:
            server_def = structure_def["services"]["mcp-server"]
            if "components" in server_def and "server" in server_def["components"]:
                server_components = server_def["components"]["server"].get("components", {})
                
                # Process tools
                if "tools" in server_components:
                    self._process_tools(server_components["tools"])
                
                # Process resources
                if "resources" in server_components:
                    self._process_resources(server_components["resources"])
        
        logger.debug(f"Processed tools and resources, total components: {len(self.component_registry)}")

    def _process_tools(self, tools_def: Dict[str, Any]) -> None:
        """
        Process tool components from the target structure.
        
        Args:
            tools_def: Tool components definition from the target structure
        """
        logger.debug("Processing tool components...")
        
        # Create Tools Registry component
        tools_registry = Component(
            name="ToolsRegistry",
            type="registry",
            description="Registry for MCP tools",
            path="services/mcp-server/src/server/tools",
            required_files=[
                "services/mcp-server/src/server/tools/__init__.py",
                "services/mcp-server/src/server/tools/registry.py"
            ],
            dependencies=["MCPServer"]
        )
        self.component_registry["ToolsRegistry"] = tools_registry
        
        # Add Tools Registry as a subcomponent of Server
        server_component = self.component_registry["MCPServer"]
        server_component.subcomponents.append("ToolsRegistry")
        
        # Process tool components
        for tool_name, tool_def in tools_def.get("components", {}).items():
            component_name = f"{tool_name.capitalize()}Tool"
            tool_path = f"services/mcp-server/src/server/tools/{tool_name}"
            
            tool_component = Component(
                name=component_name,
                type="tool",
                description=tool_def.get("description", f"{tool_name} tool implementation"),
                path=tool_path,
                required_files=tool_def.get("required_files", []),
                dependencies=["ToolsRegistry"]
            )
            self.component_registry[component_name] = tool_component
            
            # Add tool as a subcomponent of Tools Registry
            tools_registry.subcomponents.append(component_name)
            
            # Create interface for the tool
            tool_interface = Interface(
                name=f"{component_name}Interface",
                source_component="MCPServer",
                target_component=component_name,
                description=f"Interface for {tool_name} tool operations",
                methods=[
                    {
                        "name": "execute",
                        "description": f"Execute the {tool_name} tool",
                        "parameters": ["arguments"],
                        "return_type": "tool_result"
                    }
                ]
            )
            self.interface_registry[f"{component_name}Interface"] = tool_interface
            
            # Add interface to the tool component
            tool_component.interfaces.append(f"{component_name}Interface")

    def _process_resources(self, resources_def: Dict[str, Any]) -> None:
        """
        Process resource components from the target structure.
        
        Args:
            resources_def: Resource components definition from the target structure
        """
        logger.debug("Processing resource components...")
        
        # Create Resources Registry component
        resources_registry = Component(
            name="ResourcesRegistry",
            type="registry",
            description="Registry for MCP resources",
            path="services/mcp-server/src/server/resources",
            required_files=[
                "services/mcp-server/src/server/resources/__init__.py",
                "services/mcp-server/src/server/resources/registry.py"
            ],
            dependencies=["MCPServer"]
        )
        self.component_registry["ResourcesRegistry"] = resources_registry
        
        # Add Resources Registry as a subcomponent of Server
        server_component = self.component_registry["MCPServer"]
        server_component.subcomponents.append("ResourcesRegistry")
        
        # Process resource components
        for resource_name, resource_def in resources_def.get("components", {}).items():
            component_name = f"{resource_name.capitalize()}Resource"
            resource_path = f"services/mcp-server/src/server/resources/{resource_name}"
            
            resource_component = Component(
                name=component_name,
                type="resource",
                description=resource_def.get("description", f"{resource_name} resource implementation"),
                path=resource_path,
                required_files=resource_def.get("required_files", []),
                dependencies=["ResourcesRegistry"]
            )
            self.component_registry[component_name] = resource_component
            
            # Add resource as a subcomponent of Resources Registry
            resources_registry.subcomponents.append(component_name)
            
            # Create interface for the resource
            resource_interface = Interface(
                name=f"{component_name}Interface",
                source_component="MCPServer",
                target_component=component_name,
                description=f"Interface for {resource_name} resource operations",
                methods=[
                    {
                        "name": "list",
                        "description": f"List {resource_name} resources",
                        "parameters": ["path"],
                        "return_type": "resource_list"
                    },
                    {
                        "name": "read",
                        "description": f"Read a {resource_name} resource",
                        "parameters": ["uri"],
                        "return_type": "resource_data"
                    },
                    {
                        "name": "subscribe",
                        "description": f"Subscribe to a {resource_name} resource",
                        "parameters": ["uri", "callback_id"],
                        "return_type": "subscription_result"
                    }
                ]
            )
            self.interface_registry[f"{component_name}Interface"] = resource_interface
            
            # Add interface to the resource component
            resource_component.interfaces.append(f"{component_name}Interface")

    def _set_implementation_priorities(self) -> None:
        """Set implementation priorities for components based on dependencies."""
        logger.info("Setting implementation priorities...")
        
        # First, set priorities for core components
        self.component_registry["MCPHost"].implementation_priority = 0
        self.component_registry["MCPClient"].implementation_priority = 1
        self.component_registry["MCPServer"].implementation_priority = 1
        self.component_registry["DependencyInjection"].implementation_priority = 2
        
        # Set priorities for registries
        if "ToolsRegistry" in self.component_registry:
            self.component_registry["ToolsRegistry"].implementation_priority = 2
        
        if "ResourcesRegistry" in self.component_registry:
            self.component_registry["ResourcesRegistry"].implementation_priority = 2
        
        # Set priorities for tools and resources based on dependencies
        for component_name, component in self.component_registry.items():
            if component.type in ["tool", "resource"]:
                # Tools and resources have lower priority than their registries
                component.implementation_priority = 3
        
        # Adjust priorities based on migration status from analysis report
        for component in self.analysis_report.get("components", []):
            component_name = component.get("name")
            migration_status = component.get("migration_status")
            
            # Find matching component in our registry
            for reg_name, reg_component in self.component_registry.items():
                if reg_component.path.endswith(component_name):
                    # Update migration status
                    reg_component.migration_status = migration_status
                    
                    # Adjust priority based on status
                    if migration_status == "complete":
                        # Completed components have lowest priority (already done)
                        reg_component.implementation_priority = 5
                    elif migration_status == "partial":
                        # Partially completed components have medium priority
                        reg_component.implementation_priority = 3
                    
                    logger.debug(f"Updated component {reg_name} with status {migration_status} and priority {reg_component.implementation_priority}")

    def save_design(self, output_path: str) -> None:
        """
        Save the architecture design to a JSON file.
        
        Args:
            output_path: Path to save the design to
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Convert design to dictionary
            design_dict = {
                "components": [asdict(c) for c in self.design.components],
                "interfaces": [asdict(i) for i in self.design.interfaces],
                "data_flows": [asdict(d) for d in self.design.data_flows],
                "timestamp": self.design.timestamp,
                "analysis_report_path": self.design.analysis_report_path,
                "target_structure_path": self.design.target_structure_path
            }
            
            # Save to JSON file
            with open(output_path, 'w') as f:
                json.dump(design_dict, f, indent=2)
            
            logger.info(f"Architecture design saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving architecture design: {str(e)}")
            raise


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Design MCP architecture based on analysis report")
    
    parser.add_argument(
        "--analysis-report",
        type=str,
        default="data/migration/mcp/analysis_report.json",
        help="Path to the analysis report JSON file (default: data/migration/mcp/analysis_report.json)"
    )
    
    parser.add_argument(
        "--target-structure",
        type=str,
        default="scripts/migration/mcp/structure.yaml",
        help="Path to the target structure YAML file (default: scripts/migration/mcp/structure.yaml)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="data/migration/mcp/architecture_design.json",
        help="Path to output the architecture design (default: data/migration/mcp/architecture_design.json)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main function.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments
        args = parse_arguments()
        
        # Create designer
        designer = ArchitectureDesigner(
            analysis_report_path=args.analysis_report,
            target_structure_path=args.target_structure,
            verbose=args.verbose
        )
        
        # Design architecture
        design = designer.design_architecture()
        
        # Save design
        designer.save_design(args.output)
        
        # Print summary
        print("\nArchitecture Design Summary:")
        print(f"Total components: {len(design.components)}")
        print(f"Total interfaces: {len(design.interfaces)}")
        print(f"Total data flows: {len(design.data_flows)}")
        print(f"Design saved to: {args.output}")
        
        # Print implementation order
        print("\nImplementation Order:")
        sorted_components = sorted(design.components, key=lambda c: c.implementation_priority)
        for i, component in enumerate(sorted_components):
            print(f"{i+1}. {component.name} (Priority: {component.implementation_priority}, Type: {component.type})")
        
        return 0
    except Exception as e:
        logger.error(f"Error during architecture design: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())