#!/usr/bin/env python3
"""
MCP Migration - Migration Plan Creation Script

This script takes the architecture design as input and creates a detailed migration plan.
It defines phases, tasks, dependencies, timeline, and risk assessment for the MCP migration.

Usage:
    python create_migration_plan.py [--architecture-design PATH] [--analysis-report PATH] [--output PATH]

Arguments:
    --architecture-design PATH  Path to the architecture design JSON file (default: data/migration/mcp/architecture_design.json)
    --analysis-report PATH      Path to the analysis report JSON file (default: data/migration/mcp/analysis_report.json)
    --output PATH              Path to output the migration plan (default: data/migration/mcp/migration_plan.json)
    --verbose                  Enable verbose logging
    --help                     Show this help message and exit
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any, Tuple, Set, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mcp_migration_plan.log")
    ]
)
logger = logging.getLogger("mcp_migration_plan")


class RiskLevel(Enum):
    """Risk level enumeration for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(Enum):
    """Status enumeration for tasks."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class Risk:
    """Represents a risk assessment for a task."""
    level: RiskLevel
    description: str
    mitigation_strategy: str
    impact: str


@dataclass
class Task:
    """Represents a task in the migration plan."""
    id: str
    name: str
    description: str
    phase_id: str
    component_name: str
    estimated_effort_days: float
    dependencies: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.NOT_STARTED
    assignee: str = ""
    risk_assessment: Optional[Risk] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class Phase:
    """Represents a phase in the migration plan."""
    id: str
    name: str
    description: str
    order: int
    tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class Dependency:
    """Represents a dependency between tasks."""
    source_task_id: str
    target_task_id: str
    type: str  # "finish-to-start", "start-to-start", "finish-to-finish", "start-to-finish"
    description: str = ""


@dataclass
class Timeline:
    """Represents the timeline for the migration plan."""
    start_date: str
    end_date: str
    phases: Dict[str, Dict[str, str]] = field(default_factory=dict)
    tasks: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class MigrationPlan:
    """Represents the migration plan."""
    phases: List[Phase] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    dependencies: List[Dependency] = field(default_factory=list)
    timeline: Optional[Timeline] = None
    architecture_design_path: str = ""
    analysis_report_path: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MigrationPlanner:
    """Creates a migration plan based on the architecture design."""

    def __init__(self, architecture_design_path: str, analysis_report_path: str, verbose: bool = False):
        """
        Initialize the MigrationPlanner.

        Args:
            architecture_design_path: Path to the architecture design JSON file
            analysis_report_path: Path to the analysis report JSON file
            verbose: Whether to enable verbose logging
        """
        self.architecture_design_path = architecture_design_path
        self.analysis_report_path = analysis_report_path
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.info(f"Initializing MigrationPlanner with architecture design: {self.architecture_design_path}")
        logger.info(f"Analysis report path: {self.analysis_report_path}")
        
        # Validate paths
        self._validate_paths()
        
        # Load architecture design
        self.architecture_design = self._load_architecture_design()
        
        # Load analysis report
        self.analysis_report = self._load_analysis_report()
        
        # Initialize migration plan
        self.plan = MigrationPlan(
            architecture_design_path=self.architecture_design_path,
            analysis_report_path=self.analysis_report_path
        )
        
        # Task registry to keep track of all tasks
        self.task_registry: Dict[str, Task] = {}
        
        # Phase registry to keep track of all phases
        self.phase_registry: Dict[str, Phase] = {}
        
        # Dependency registry to keep track of all dependencies
        self.dependency_registry: Dict[str, Dependency] = {}

    def _validate_paths(self) -> None:
        """Validate that the specified paths exist."""
        if not os.path.exists(self.architecture_design_path):
            raise FileNotFoundError(f"Architecture design file does not exist: {self.architecture_design_path}")
        
        if not os.path.exists(self.analysis_report_path):
            raise FileNotFoundError(f"Analysis report file does not exist: {self.analysis_report_path}")

    def _load_architecture_design(self) -> Dict[str, Any]:
        """
        Load the architecture design from the JSON file.
        
        Returns:
            Dict[str, Any]: The architecture design as a dictionary
        """
        try:
            with open(self.architecture_design_path, 'r') as f:
                design = json.load(f)
                logger.debug(f"Loaded architecture design with {len(design.get('components', []))} components")
                return design
        except Exception as e:
            logger.error(f"Error loading architecture design: {str(e)}")
            raise

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

    def create_migration_plan(self) -> MigrationPlan:
        """
        Create a migration plan based on the architecture design.
        
        Returns:
            MigrationPlan: The migration plan
        """
        logger.info("Starting migration plan creation...")
        
        # Define migration phases
        self._define_migration_phases()
        
        # Define migration tasks
        self._define_migration_tasks()
        
        # Define task dependencies
        self._define_task_dependencies()
        
        # Create timeline
        self._create_timeline()
        
        # Add phases to the plan
        self.plan.phases = list(self.phase_registry.values())
        
        # Add tasks to the plan
        self.plan.tasks = list(self.task_registry.values())
        
        # Add dependencies to the plan
        self.plan.dependencies = list(self.dependency_registry.values())
        
        logger.info("Migration plan creation completed")
        return self.plan

    def _define_migration_phases(self) -> None:
        """Define the phases of the migration plan."""
        logger.info("Defining migration phases...")
        
        # Phase 1: SDK Adoption
        sdk_adoption_phase = Phase(
            id="phase_sdk_adoption",
            name="SDK Adoption",
            description="Adopt the MCP SDK and integrate it into the existing codebase",
            order=1
        )
        self.phase_registry[sdk_adoption_phase.id] = sdk_adoption_phase
        
        # Phase 2: Protocol Conformance
        protocol_conformance_phase = Phase(
            id="phase_protocol_conformance",
            name="Protocol Conformance",
            description="Ensure that all components conform to the MCP protocol",
            order=2,
            dependencies=["phase_sdk_adoption"]
        )
        self.phase_registry[protocol_conformance_phase.id] = protocol_conformance_phase
        
        # Phase 3: Host Implementation
        host_implementation_phase = Phase(
            id="phase_host_implementation",
            name="Host Implementation",
            description="Implement the MCP Host component",
            order=3,
            dependencies=["phase_protocol_conformance"]
        )
        self.phase_registry[host_implementation_phase.id] = host_implementation_phase
        
        # Phase 4: Client Implementation
        client_implementation_phase = Phase(
            id="phase_client_implementation",
            name="Client Implementation",
            description="Implement the MCP Client component",
            order=4,
            dependencies=["phase_host_implementation"]
        )
        self.phase_registry[client_implementation_phase.id] = client_implementation_phase
        
        # Phase 5: Server Implementation
        server_implementation_phase = Phase(
            id="phase_server_implementation",
            name="Server Implementation",
            description="Implement the MCP Server component",
            order=5,
            dependencies=["phase_client_implementation"]
        )
        self.phase_registry[server_implementation_phase.id] = server_implementation_phase
        
        # Phase 6: Tools and Resources Implementation
        tools_resources_phase = Phase(
            id="phase_tools_resources",
            name="Tools and Resources Implementation",
            description="Implement MCP tools and resources",
            order=6,
            dependencies=["phase_server_implementation"]
        )
        self.phase_registry[tools_resources_phase.id] = tools_resources_phase
        
        # Phase 7: Security Model
        security_model_phase = Phase(
            id="phase_security_model",
            name="Security Model",
            description="Implement the MCP security model",
            order=7,
            dependencies=["phase_host_implementation", "phase_client_implementation", "phase_server_implementation"]
        )
        self.phase_registry[security_model_phase.id] = security_model_phase
        
        # Phase 8: Testing and Validation
        testing_validation_phase = Phase(
            id="phase_testing_validation",
            name="Testing and Validation",
            description="Test and validate the MCP implementation",
            order=8,
            dependencies=["phase_tools_resources", "phase_security_model"]
        )
        self.phase_registry[testing_validation_phase.id] = testing_validation_phase
        
        # Phase 9: Documentation and Training
        documentation_training_phase = Phase(
            id="phase_documentation_training",
            name="Documentation and Training",
            description="Create documentation and training materials for the MCP implementation",
            order=9,
            dependencies=["phase_testing_validation"]
        )
        self.phase_registry[documentation_training_phase.id] = documentation_training_phase
        
        # Phase 10: Deployment
        deployment_phase = Phase(
            id="phase_deployment",
            name="Deployment",
            description="Deploy the MCP implementation to production",
            order=10,
            dependencies=["phase_documentation_training"]
        )
        self.phase_registry[deployment_phase.id] = deployment_phase
        
        logger.debug(f"Defined {len(self.phase_registry)} migration phases")

    def _define_migration_tasks(self) -> None:
        """Define the tasks for each phase of the migration plan."""
        logger.info("Defining migration tasks...")
        
        # Get components from architecture design
        components = self.architecture_design.get("components", [])
        
        # SDK Adoption Phase Tasks
        self._define_sdk_adoption_tasks()
        
        # Protocol Conformance Phase Tasks
        self._define_protocol_conformance_tasks()
        
        # Host Implementation Phase Tasks
        self._define_host_implementation_tasks(components)
        
        # Client Implementation Phase Tasks
        self._define_client_implementation_tasks(components)
        
        # Server Implementation Phase Tasks
        self._define_server_implementation_tasks(components)
        
        # Tools and Resources Implementation Phase Tasks
        self._define_tools_resources_tasks(components)
        
        # Security Model Phase Tasks
        self._define_security_model_tasks()
        
        # Testing and Validation Phase Tasks
        self._define_testing_validation_tasks()
        
        # Documentation and Training Phase Tasks
        self._define_documentation_training_tasks()
        
        # Deployment Phase Tasks
        self._define_deployment_tasks()
        
        logger.debug(f"Defined {len(self.task_registry)} migration tasks")

    def _define_sdk_adoption_tasks(self) -> None:
        """Define tasks for the SDK Adoption phase."""
        phase_id = "phase_sdk_adoption"
        
        # Task: Install MCP SDK
        task_install_sdk = Task(
            id="task_install_sdk",
            name="Install MCP SDK",
            description="Install the MCP SDK and its dependencies",
            phase_id=phase_id,
            component_name="MCP SDK",
            estimated_effort_days=1.0,
            risk_assessment=Risk(
                level=RiskLevel.LOW,
                description="SDK might have compatibility issues with existing dependencies",
                mitigation_strategy="Test SDK installation in a separate environment first",
                impact="Delay in SDK adoption"
            )
        )
        self.task_registry[task_install_sdk.id] = task_install_sdk
        self.phase_registry[phase_id].tasks.append(task_install_sdk.id)
        
        # Task: Configure SDK
        task_configure_sdk = Task(
            id="task_configure_sdk",
            name="Configure MCP SDK",
            description="Configure the MCP SDK for the project",
            phase_id=phase_id,
            component_name="MCP SDK",
            estimated_effort_days=1.5,
            dependencies=["task_install_sdk"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Configuration might require changes to existing code",
                mitigation_strategy="Create a configuration adapter layer",
                impact="Increased complexity in the codebase"
            )
        )
        self.task_registry[task_configure_sdk.id] = task_configure_sdk
        self.phase_registry[phase_id].tasks.append(task_configure_sdk.id)
        
        # Task: Create SDK Integration Tests
        task_sdk_tests = Task(
            id="task_sdk_tests",
            name="Create SDK Integration Tests",
            description="Create tests to verify SDK integration",
            phase_id=phase_id,
            component_name="MCP SDK",
            estimated_effort_days=2.0,
            dependencies=["task_configure_sdk"],
            risk_assessment=Risk(
                level=RiskLevel.LOW,
                description="Test coverage might be incomplete",
                mitigation_strategy="Use test coverage tools to ensure comprehensive testing",
                impact="Potential issues might be missed during testing"
            )
        )
        self.task_registry[task_sdk_tests.id] = task_sdk_tests
        self.phase_registry[phase_id].tasks.append(task_sdk_tests.id)

    def _define_protocol_conformance_tasks(self) -> None:
        """Define tasks for the Protocol Conformance phase."""
        phase_id = "phase_protocol_conformance"
        
        # Task: Analyze Protocol Requirements
        task_analyze_protocol = Task(
            id="task_analyze_protocol",
            name="Analyze Protocol Requirements",
            description="Analyze the MCP protocol requirements and identify gaps in the current implementation",
            phase_id=phase_id,
            component_name="MCP Protocol",
            estimated_effort_days=2.0,
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Protocol requirements might be misunderstood",
                mitigation_strategy="Consult with MCP experts and review protocol documentation thoroughly",
                impact="Incorrect implementation of protocol conformance"
            )
        )
        self.task_registry[task_analyze_protocol.id] = task_analyze_protocol
        self.phase_registry[phase_id].tasks.append(task_analyze_protocol.id)
        
        # Task: Implement JSON-RPC Handling
        task_implement_jsonrpc = Task(
            id="task_implement_jsonrpc",
            name="Implement JSON-RPC Handling",
            description="Implement JSON-RPC handling according to the MCP protocol",
            phase_id=phase_id,
            component_name="MCP Protocol",
            estimated_effort_days=3.0,
            dependencies=["task_analyze_protocol"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="JSON-RPC implementation might have edge cases",
                mitigation_strategy="Implement comprehensive error handling and validation",
                impact="Protocol conformance issues"
            )
        )
        self.task_registry[task_implement_jsonrpc.id] = task_implement_jsonrpc
        self.phase_registry[phase_id].tasks.append(task_implement_jsonrpc.id)
        
        # Task: Create Protocol Conformance Tests
        task_protocol_tests = Task(
            id="task_protocol_tests",
            name="Create Protocol Conformance Tests",
            description="Create tests to verify protocol conformance",
            phase_id=phase_id,
            component_name="MCP Protocol",
            estimated_effort_days=2.5,
            dependencies=["task_implement_jsonrpc"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Test coverage might miss edge cases",
                mitigation_strategy="Use property-based testing and fuzzing",
                impact="Protocol conformance issues might be missed"
            )
        )
        self.task_registry[task_protocol_tests.id] = task_protocol_tests
        self.phase_registry[phase_id].tasks.append(task_protocol_tests.id)

    def _define_host_implementation_tasks(self, components: List[Dict[str, Any]]) -> None:
        """
        Define tasks for the Host Implementation phase.
        
        Args:
            components: List of components from the architecture design
        """
        phase_id = "phase_host_implementation"
        
        # Find the Host component
        host_component = next((c for c in components if c.get("name") == "MCPHost"), None)
        
        if not host_component:
            logger.warning("Host component not found in architecture design")
            return
        
        # Task: Implement Host Core
        task_implement_host_core = Task(
            id="task_implement_host_core",
            name="Implement Host Core",
            description="Implement the core functionality of the MCP Host component",
            phase_id=phase_id,
            component_name="MCPHost",
            estimated_effort_days=4.0,
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Host implementation is complex and critical",
                mitigation_strategy="Break down implementation into smaller, testable units",
                impact="Delay in the entire migration process"
            )
        )
        self.task_registry[task_implement_host_core.id] = task_implement_host_core
        self.phase_registry[phase_id].tasks.append(task_implement_host_core.id)
        
        # Task: Implement Consent Manager
        task_implement_consent_manager = Task(
            id="task_implement_consent_manager",
            name="Implement Consent Manager",
            description="Implement the consent management functionality of the MCP Host",
            phase_id=phase_id,
            component_name="MCPHost",
            estimated_effort_days=2.5,
            dependencies=["task_implement_host_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Consent management has security implications",
                mitigation_strategy="Implement with security best practices and thorough testing",
                impact="Security vulnerabilities in consent management"
            )
        )
        self.task_registry[task_implement_consent_manager.id] = task_implement_consent_manager
        self.phase_registry[phase_id].tasks.append(task_implement_consent_manager.id)
        
        # Task: Implement Context Manager
        task_implement_context_manager = Task(
            id="task_implement_context_manager",
            name="Implement Context Manager",
            description="Implement the context management functionality of the MCP Host",
            phase_id=phase_id,
            component_name="MCPHost",
            estimated_effort_days=2.5,
            dependencies=["task_implement_host_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Context management is complex and critical for proper operation",
                mitigation_strategy="Implement with clear interfaces and thorough testing",
                impact="Improper context management leading to operational issues"
            )
        )
        self.task_registry[task_implement_context_manager.id] = task_implement_context_manager
        self.phase_registry[phase_id].tasks.append(task_implement_context_manager.id)
        
        # Task: Implement Server Registry
        task_implement_server_registry = Task(
            id="task_implement_server_registry",
            name="Implement Server Registry",
            description="Implement the server registry functionality of the MCP Host",
            phase_id=phase_id,
            component_name="MCPHost",
            estimated_effort_days=2.0,
            dependencies=["task_implement_host_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Server registry needs to handle dynamic registration and deregistration",
                mitigation_strategy="Implement with thread-safety and proper error handling",
                impact="Issues with server registration and discovery"
            )
        )
        self.task_registry[task_implement_server_registry.id] = task_implement_server_registry
        self.phase_registry[phase_id].tasks.append(task_implement_server_registry.id)
        
        # Task: Implement Client Registry
        task_implement_client_registry = Task(
            id="task_implement_client_registry",
            name="Implement Client Registry",
            description="Implement the client registry functionality of the MCP Host",
            phase_id=phase_id,
            component_name="MCPHost",
            estimated_effort_days=2.0,
            dependencies=["task_implement_host_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Client registry needs to handle dynamic registration and deregistration",
                mitigation_strategy="Implement with thread-safety and proper error handling",
                impact="Issues with client registration and discovery"
            )
        )
        self.task_registry[task_implement_client_registry.id] = task_implement_client_registry
        self.phase_registry[phase_id].tasks.append(task_implement_client_registry.id)
        
        # Task: Create Host Unit Tests
        task_host_unit_tests = Task(
            id="task_host_unit_tests",
            name="Create Host Unit Tests",
            description="Create unit tests for the MCP Host component",
            phase_id=phase_id,
            component_name="MCPHost",
            estimated_effort_days=3.0,
            dependencies=[
                "task_implement_consent_manager",
                "task_implement_context_manager",
                "task_implement_server_registry",
                "task_implement_client_registry"
            ],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Test coverage might be incomplete",
                mitigation_strategy="Use test coverage tools and code reviews",
                impact="Bugs in the Host component might be missed"
            )
        )
        self.task_registry[task_host_unit_tests.id] = task_host_unit_tests
        self.phase_registry[phase_id].tasks.append(task_host_unit_tests.id)

    def _define_client_implementation_tasks(self, components: List[Dict[str, Any]]) -> None:
        """
        Define tasks for the Client Implementation phase.
        
        Args:
            components: List of components from the architecture design
        """
        phase_id = "phase_client_implementation"
        
        # Find the Client component
        client_component = next((c for c in components if c.get("name") == "MCPClient"), None)
        
        if not client_component:
            logger.warning("Client component not found in architecture design")
            return
        
        # Task: Implement Client Core
        task_implement_client_core = Task(
            id="task_implement_client_core",
            name="Implement Client Core",
            description="Implement the core functionality of the MCP Client component",
            phase_id=phase_id,
            component_name="MCPClient",
            estimated_effort_days=3.5,
            dependencies=["task_host_unit_tests"],  # Depends on Host implementation
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Client implementation is complex and depends on Host",
                mitigation_strategy="Ensure clear interfaces with Host and thorough testing",
                impact="Delay in the migration process"
            )
        )
        self.task_registry[task_implement_client_core.id] = task_implement_client_core
        self.phase_registry[phase_id].tasks.append(task_implement_client_core.id)
        
        # Task: Implement Subscription Manager
        task_implement_subscription_manager = Task(
            id="task_implement_subscription_manager",
            name="Implement Subscription Manager",
            description="Implement the subscription management functionality of the MCP Client",
            phase_id=phase_id,
            component_name="MCPClient",
            estimated_effort_days=2.5,
            dependencies=["task_implement_client_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Subscription management is complex and critical for resource updates",
                mitigation_strategy="Implement with clear interfaces and thorough testing",
                impact="Issues with resource subscriptions and updates"
            )
        )
        self.task_registry[task_implement_subscription_manager.id] = task_implement_subscription_manager
        self.phase_registry[phase_id].tasks.append(task_implement_subscription_manager.id)
        
        # Task: Implement Request Handler
        task_implement_request_handler = Task(
            id="task_implement_request_handler",
            name="Implement Request Handler",
            description="Implement the request handling functionality of the MCP Client",
            phase_id=phase_id,
            component_name="MCPClient",
            estimated_effort_days=2.0,
            dependencies=["task_implement_client_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Request handling needs to be robust and handle errors properly",
                mitigation_strategy="Implement with proper error handling and validation",
                impact="Issues with request handling and routing"
            )
        )
        self.task_registry[task_implement_request_handler.id] = task_implement_request_handler
        self.phase_registry[phase_id].tasks.append(task_implement_request_handler.id)
        
        # Task: Implement Response Handler
        task_implement_response_handler = Task(
            id="task_implement_response_handler",
            name="Implement Response Handler",
            description="Implement the response handling functionality of the MCP Client",
            phase_id=phase_id,
            component_name="MCPClient",
            estimated_effort_days=2.0,
            dependencies=["task_implement_client_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Response handling needs to be robust and handle errors properly",
                mitigation_strategy="Implement with proper error handling and validation",
                impact="Issues with response handling and routing"
            )
        )
        self.task_registry[task_implement_response_handler.id] = task_implement_response_handler
        self.phase_registry[phase_id].tasks.append(task_implement_response_handler.id)
        
        # Task: Create Client Unit Tests
        task_client_unit_tests = Task(
            id="task_client_unit_tests",
            name="Create Client Unit Tests",
            description="Create unit tests for the MCP Client component",
            phase_id=phase_id,
            component_name="MCPClient",
            estimated_effort_days=2.5,
            dependencies=[
                "task_implement_subscription_manager",
                "task_implement_request_handler",
                "task_implement_response_handler"
            ],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Test coverage might be incomplete",
                mitigation_strategy="Use test coverage tools and code reviews",
                impact="Bugs in the Client component might be missed"
            )
        )
        self.task_registry[task_client_unit_tests.id] = task_client_unit_tests
        self.phase_registry[phase_id].tasks.append(task_client_unit_tests.id)

    def _define_server_implementation_tasks(self, components: List[Dict[str, Any]]) -> None:
        """
        Define tasks for the Server Implementation phase.
        
        Args:
            components: List of components from the architecture design
        """
        phase_id = "phase_server_implementation"
        
        # Find the Server component
        server_component = next((c for c in components if c.get("name") == "MCPServer"), None)
        
        if not server_component:
            logger.warning("Server component not found in architecture design")
            return
        
        # Task: Implement Server Core
        task_implement_server_core = Task(
            id="task_implement_server_core",
            name="Implement Server Core",
            description="Implement the core functionality of the MCP Server component",
            phase_id=phase_id,
            component_name="MCPServer",
            estimated_effort_days=3.5,
            dependencies=["task_client_unit_tests"],  # Depends on Client implementation
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Server implementation is complex and depends on Client and Host",
                mitigation_strategy="Ensure clear interfaces with Client and Host and thorough testing",
                impact="Delay in the migration process"
            )
        )
        self.task_registry[task_implement_server_core.id] = task_implement_server_core
        self.phase_registry[phase_id].tasks.append(task_implement_server_core.id)
        
        # Task: Implement Capability Manager
        task_implement_capability_manager = Task(
            id="task_implement_capability_manager",
            name="Implement Capability Manager",
            description="Implement the capability management functionality of the MCP Server",
            phase_id=phase_id,
            component_name="MCPServer",
            estimated_effort_days=2.5,
            dependencies=["task_implement_server_core"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Capability management is complex and critical for proper operation",
                mitigation_strategy="Implement with clear interfaces and thorough testing",
                impact="Issues with capability discovery and execution"
            )
        )
        self.task_registry[task_implement_capability_manager.id] = task_implement_capability_manager
        self.phase_registry[phase_id].tasks.append(task_implement_capability_manager.id)
        
        # Task: Create Server Unit Tests
        task_server_unit_tests = Task(
            id="task_server_unit_tests",
            name="Create Server Unit Tests",
            description="Create unit tests for the MCP Server component",
            phase_id=phase_id,
            component_name="MCPServer",
            estimated_effort_days=2.5,
            dependencies=["task_implement_capability_manager"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Test coverage might be incomplete",
                mitigation_strategy="Use test coverage tools and code reviews",
                impact="Bugs in the Server component might be missed"
            )
        )
        self.task_registry[task_server_unit_tests.id] = task_server_unit_tests
        self.phase_registry[phase_id].tasks.append(task_server_unit_tests.id)

    def _define_tools_resources_tasks(self, components: List[Dict[str, Any]]) -> None:
        """
        Define tasks for the Tools and Resources Implementation phase.
        
        Args:
            components: List of components from the architecture design
        """
        phase_id = "phase_tools_resources"
        
        # Find tools and resources components
        tools_registry = next((c for c in components if c.get("name") == "ToolsRegistry"), None)
        resources_registry = next((c for c in components if c.get("name") == "ResourcesRegistry"), None)
        
        # Task: Implement Tools Registry
        task_implement_tools_registry = Task(
            id="task_implement_tools_registry",
            name="Implement Tools Registry",
            description="Implement the tools registry functionality",
            phase_id=phase_id,
            component_name="ToolsRegistry",
            estimated_effort_days=2.0,
            dependencies=["task_server_unit_tests"],  # Depends on Server implementation
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Tools registry needs to handle dynamic registration and discovery",
                mitigation_strategy="Implement with clear interfaces and thorough testing",
                impact="Issues with tool discovery and execution"
            )
        )
        self.task_registry[task_implement_tools_registry.id] = task_implement_tools_registry
        self.phase_registry[phase_id].tasks.append(task_implement_tools_registry.id)
        
        # Task: Implement Resources Registry
        task_implement_resources_registry = Task(
            id="task_implement_resources_registry",
            name="Implement Resources Registry",
            description="Implement the resources registry functionality",
            phase_id=phase_id,
            component_name="ResourcesRegistry",
            estimated_effort_days=2.0,
            dependencies=["task_server_unit_tests"],  # Depends on Server implementation
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Resources registry needs to handle dynamic registration and discovery",
                mitigation_strategy="Implement with clear interfaces and thorough testing",
                impact="Issues with resource discovery and access"
            )
        )
        self.task_registry[task_implement_resources_registry.id] = task_implement_resources_registry
        self.phase_registry[phase_id].tasks.append(task_implement_resources_registry.id)
        
        # Task: Implement Shell Tool
        task_implement_shell_tool = Task(
            id="task_implement_shell_tool",
            name="Implement Shell Tool",
            description="Implement the shell command tool",
            phase_id=phase_id,
            component_name="ShellTool",
            estimated_effort_days=1.5,
            dependencies=["task_implement_tools_registry"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Shell tool has security implications",
                mitigation_strategy="Implement with security best practices and proper sandboxing",
                impact="Security vulnerabilities in shell command execution"
            )
        )
        self.task_registry[task_implement_shell_tool.id] = task_implement_shell_tool
        self.phase_registry[phase_id].tasks.append(task_implement_shell_tool.id)
        
        # Task: Implement File Resource
        task_implement_file_resource = Task(
            id="task_implement_file_resource",
            name="Implement File Resource",
            description="Implement the file resource provider",
            phase_id=phase_id,
            component_name="FileResource",
            estimated_effort_days=1.5,
            dependencies=["task_implement_resources_registry"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="File resource has security implications",
                mitigation_strategy="Implement with security best practices and proper access control",
                impact="Security vulnerabilities in file access"
            )
        )
        self.task_registry[task_implement_file_resource.id] = task_implement_file_resource
        self.phase_registry[phase_id].tasks.append(task_implement_file_resource.id)
        
        # Task: Create Tools and Resources Unit Tests
        task_tools_resources_tests = Task(
            id="task_tools_resources_tests",
            name="Create Tools and Resources Unit Tests",
            description="Create unit tests for tools and resources",
            phase_id=phase_id,
            component_name="ToolsAndResources",
            estimated_effort_days=2.0,
            dependencies=["task_implement_shell_tool", "task_implement_file_resource"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Test coverage might be incomplete",
                mitigation_strategy="Use test coverage tools and code reviews",
                impact="Bugs in tools and resources might be missed"
            )
        )
        self.task_registry[task_tools_resources_tests.id] = task_tools_resources_tests
        self.phase_registry[phase_id].tasks.append(task_tools_resources_tests.id)

    def _define_security_model_tasks(self) -> None:
        """Define tasks for the Security Model phase."""
        phase_id = "phase_security_model"
        
        # Task: Design Security Model
        task_design_security_model = Task(
            id="task_design_security_model",
            name="Design Security Model",
            description="Design the security model for the MCP implementation",
            phase_id=phase_id,
            component_name="Security",
            estimated_effort_days=3.0,
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Security model is critical for the overall system security",
                mitigation_strategy="Consult with security experts and follow security best practices",
                impact="Security vulnerabilities in the MCP implementation"
            )
        )
        self.task_registry[task_design_security_model.id] = task_design_security_model
        self.phase_registry[phase_id].tasks.append(task_design_security_model.id)
        
        # Task: Implement Authentication
        task_implement_authentication = Task(
            id="task_implement_authentication",
            name="Implement Authentication",
            description="Implement authentication for the MCP implementation",
            phase_id=phase_id,
            component_name="Security",
            estimated_effort_days=2.5,
            dependencies=["task_design_security_model"],
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Authentication is critical for the overall system security",
                mitigation_strategy="Implement with security best practices and thorough testing",
                impact="Security vulnerabilities in authentication"
            )
        )
        self.task_registry[task_implement_authentication.id] = task_implement_authentication
        self.phase_registry[phase_id].tasks.append(task_implement_authentication.id)
        
        # Task: Implement Authorization
        task_implement_authorization = Task(
            id="task_implement_authorization",
            name="Implement Authorization",
            description="Implement authorization for the MCP implementation",
            phase_id=phase_id,
            component_name="Security",
            estimated_effort_days=2.5,
            dependencies=["task_design_security_model"],
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Authorization is critical for the overall system security",
                mitigation_strategy="Implement with security best practices and thorough testing",
                impact="Security vulnerabilities in authorization"
            )
        )
        self.task_registry[task_implement_authorization.id] = task_implement_authorization
        self.phase_registry[phase_id].tasks.append(task_implement_authorization.id)
        
        # Task: Create Security Unit Tests
        task_security_tests = Task(
            id="task_security_tests",
            name="Create Security Unit Tests",
            description="Create unit tests for the security model",
            phase_id=phase_id,
            component_name="Security",
            estimated_effort_days=2.0,
            dependencies=["task_implement_authentication", "task_implement_authorization"],
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Test coverage might be incomplete",
                mitigation_strategy="Use test coverage tools and security-focused code reviews",
                impact="Security vulnerabilities might be missed"
            )
        )
        self.task_registry[task_security_tests.id] = task_security_tests
        self.phase_registry[phase_id].tasks.append(task_security_tests.id)

    def _define_testing_validation_tasks(self) -> None:
        """Define tasks for the Testing and Validation phase."""
        phase_id = "phase_testing_validation"
        
        # Task: Create Integration Tests
        task_create_integration_tests = Task(
            id="task_create_integration_tests",
            name="Create Integration Tests",
            description="Create integration tests for the MCP implementation",
            phase_id=phase_id,
            component_name="Testing",
            estimated_effort_days=4.0,
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Integration tests might not cover all scenarios",
                mitigation_strategy="Use test coverage tools and thorough test planning",
                impact="Integration issues might be missed"
            )
        )
        self.task_registry[task_create_integration_tests.id] = task_create_integration_tests
        self.phase_registry[phase_id].tasks.append(task_create_integration_tests.id)
        
        # Task: Create End-to-End Tests
        task_create_e2e_tests = Task(
            id="task_create_e2e_tests",
            name="Create End-to-End Tests",
            description="Create end-to-end tests for the MCP implementation",
            phase_id=phase_id,
            component_name="Testing",
            estimated_effort_days=3.0,
            dependencies=["task_create_integration_tests"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="End-to-end tests might not cover all scenarios",
                mitigation_strategy="Use test coverage tools and thorough test planning",
                impact="End-to-end issues might be missed"
            )
        )
        self.task_registry[task_create_e2e_tests.id] = task_create_e2e_tests
        self.phase_registry[phase_id].tasks.append(task_create_e2e_tests.id)
        
        # Task: Create Performance Tests
        task_create_performance_tests = Task(
            id="task_create_performance_tests",
            name="Create Performance Tests",
            description="Create performance tests for the MCP implementation",
            phase_id=phase_id,
            component_name="Testing",
            estimated_effort_days=2.5,
            dependencies=["task_create_integration_tests"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Performance tests might not cover all scenarios",
                mitigation_strategy="Use performance testing tools and thorough test planning",
                impact="Performance issues might be missed"
            )
        )
        self.task_registry[task_create_performance_tests.id] = task_create_performance_tests
        self.phase_registry[phase_id].tasks.append(task_create_performance_tests.id)
        
        # Task: Run Conformance Tests
        task_run_conformance_tests = Task(
            id="task_run_conformance_tests",
            name="Run Conformance Tests",
            description="Run conformance tests for the MCP implementation",
            phase_id=phase_id,
            component_name="Testing",
            estimated_effort_days=2.0,
            dependencies=["task_create_integration_tests", "task_create_e2e_tests", "task_create_performance_tests"],
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Conformance tests might not pass",
                mitigation_strategy="Address all issues found during testing",
                impact="Non-conformant MCP implementation"
            )
        )
        self.task_registry[task_run_conformance_tests.id] = task_run_conformance_tests
        self.phase_registry[phase_id].tasks.append(task_run_conformance_tests.id)

    def _define_documentation_training_tasks(self) -> None:
        """Define tasks for the Documentation and Training phase."""
        phase_id = "phase_documentation_training"
        
        # Task: Create User Documentation
        task_create_user_docs = Task(
            id="task_create_user_docs",
            name="Create User Documentation",
            description="Create user documentation for the MCP implementation",
            phase_id=phase_id,
            component_name="Documentation",
            estimated_effort_days=3.0,
            risk_assessment=Risk(
                level=RiskLevel.LOW,
                description="Documentation might be incomplete",
                mitigation_strategy="Review documentation thoroughly",
                impact="Users might not understand how to use the MCP implementation"
            )
        )
        self.task_registry[task_create_user_docs.id] = task_create_user_docs
        self.phase_registry[phase_id].tasks.append(task_create_user_docs.id)
        
        # Task: Create Developer Documentation
        task_create_dev_docs = Task(
            id="task_create_dev_docs",
            name="Create Developer Documentation",
            description="Create developer documentation for the MCP implementation",
            phase_id=phase_id,
            component_name="Documentation",
            estimated_effort_days=3.5,
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Documentation might be incomplete",
                mitigation_strategy="Review documentation thoroughly",
                impact="Developers might not understand how to extend the MCP implementation"
            )
        )
        self.task_registry[task_create_dev_docs.id] = task_create_dev_docs
        self.phase_registry[phase_id].tasks.append(task_create_dev_docs.id)
        
        # Task: Create Training Materials
        task_create_training = Task(
            id="task_create_training",
            name="Create Training Materials",
            description="Create training materials for the MCP implementation",
            phase_id=phase_id,
            component_name="Training",
            estimated_effort_days=3.0,
            dependencies=["task_create_user_docs", "task_create_dev_docs"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Training materials might be incomplete",
                mitigation_strategy="Review training materials thoroughly",
                impact="Users and developers might not be properly trained"
            )
        )
        self.task_registry[task_create_training.id] = task_create_training
        self.phase_registry[phase_id].tasks.append(task_create_training.id)

    def _define_deployment_tasks(self) -> None:
        """Define tasks for the Deployment phase."""
        phase_id = "phase_deployment"
        
        # Task: Create Deployment Plan
        task_create_deployment_plan = Task(
            id="task_create_deployment_plan",
            name="Create Deployment Plan",
            description="Create a deployment plan for the MCP implementation",
            phase_id=phase_id,
            component_name="Deployment",
            estimated_effort_days=2.0,
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="Deployment plan might be incomplete",
                mitigation_strategy="Review deployment plan thoroughly",
                impact="Deployment might fail"
            )
        )
        self.task_registry[task_create_deployment_plan.id] = task_create_deployment_plan
        self.phase_registry[phase_id].tasks.append(task_create_deployment_plan.id)
        
        # Task: Set Up CI/CD Pipeline
        task_setup_cicd = Task(
            id="task_setup_cicd",
            name="Set Up CI/CD Pipeline",
            description="Set up a CI/CD pipeline for the MCP implementation",
            phase_id=phase_id,
            component_name="Deployment",
            estimated_effort_days=2.5,
            dependencies=["task_create_deployment_plan"],
            risk_assessment=Risk(
                level=RiskLevel.MEDIUM,
                description="CI/CD pipeline might have issues",
                mitigation_strategy="Test the pipeline thoroughly",
                impact="Automated deployment might fail"
            )
        )
        self.task_registry[task_setup_cicd.id] = task_setup_cicd
        self.phase_registry[phase_id].tasks.append(task_setup_cicd.id)
        
        # Task: Deploy to Production
        task_deploy_to_prod = Task(
            id="task_deploy_to_prod",
            name="Deploy to Production",
            description="Deploy the MCP implementation to production",
            phase_id=phase_id,
            component_name="Deployment",
            estimated_effort_days=1.5,
            dependencies=["task_setup_cicd"],
            risk_assessment=Risk(
                level=RiskLevel.HIGH,
                description="Production deployment might fail",
                mitigation_strategy="Test the deployment thoroughly in staging",
                impact="Production environment might be affected"
            )
        )
        self.task_registry[task_deploy_to_prod.id] = task_deploy_to_prod
        self.phase_registry[phase_id].tasks.append(task_deploy_to_prod.id)

    def _define_task_dependencies(self) -> None:
        """Define dependencies between tasks."""
        logger.info("Defining task dependencies...")
        
        # Create dependencies between tasks based on their phase dependencies
        for phase_id, phase in self.phase_registry.items():
            for dependency_phase_id in phase.dependencies:
                # Get all tasks in the dependency phase
                dependency_phase = self.phase_registry.get(dependency_phase_id)
                if not dependency_phase:
                    logger.warning(f"Dependency phase {dependency_phase_id} not found for phase {phase_id}")
                    continue
                
                # Get the last tasks in the dependency phase (tasks with no dependents within the phase)
                dependency_phase_last_tasks = self._get_last_tasks_in_phase(dependency_phase_id)
                
                # Get the first tasks in the current phase (tasks with no dependencies within the phase)
                phase_first_tasks = self._get_first_tasks_in_phase(phase_id)
                
                # Create dependencies from the last tasks in the dependency phase to the first tasks in the current phase
                for dependency_task_id in dependency_phase_last_tasks:
                    for task_id in phase_first_tasks:
                        dependency = Dependency(
                            source_task_id=dependency_task_id,
                            target_task_id=task_id,
                            type="finish-to-start",
                            description=f"Task {task_id} depends on task {dependency_task_id}"
                        )
                        self.dependency_registry[f"{dependency_task_id}-{task_id}"] = dependency
        
        logger.debug(f"Defined {len(self.dependency_registry)} task dependencies")

    def _get_last_tasks_in_phase(self, phase_id: str) -> List[str]:
        """
        Get the last tasks in a phase (tasks with no dependents within the phase).
        
        Args:
            phase_id: The ID of the phase
            
        Returns:
            List[str]: List of task IDs
        """
        phase = self.phase_registry.get(phase_id)
        if not phase:
            return []
        
        # Get all tasks in the phase
        phase_tasks = phase.tasks
        
        # Get all tasks that are dependencies of other tasks in the phase
        dependency_tasks = set()
        for task_id in phase_tasks:
            task = self.task_registry.get(task_id)
            if task:
                dependency_tasks.update(task.dependencies)
        
        # Get tasks that are not dependencies of other tasks in the phase
        last_tasks = [task_id for task_id in phase_tasks if task_id not in dependency_tasks]
        
        # If no last tasks found, use all tasks in the phase
        if not last_tasks:
            last_tasks = phase_tasks
        
        return last_tasks

    def _get_first_tasks_in_phase(self, phase_id: str) -> List[str]:
        """
        Get the first tasks in a phase (tasks with no dependencies within the phase).
        
        Args:
            phase_id: The ID of the phase
            
        Returns:
            List[str]: List of task IDs
        """
        phase = self.phase_registry.get(phase_id)
        if not phase:
            return []
        
        # Get all tasks in the phase
        phase_tasks = phase.tasks
        
        # Get tasks with no dependencies or with dependencies outside the phase
        first_tasks = []
        for task_id in phase_tasks:
            task = self.task_registry.get(task_id)
            if task:
                # Check if the task has no dependencies or if all dependencies are outside the phase
                if not task.dependencies or all(dep_id not in phase_tasks for dep_id in task.dependencies):
                    first_tasks.append(task_id)
        
        # If no first tasks found, use all tasks in the phase
        if not first_tasks:
            first_tasks = phase_tasks
        
        return first_tasks

    def _create_timeline(self) -> None:
        """Create a timeline for the migration plan."""
        logger.info("Creating timeline...")
        
        # Set start date to today
        start_date = datetime.now().date()
        
        # Calculate end date based on task effort and dependencies
        end_date = self._calculate_end_date(start_date)
        
        # Create timeline
        timeline = Timeline(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Calculate start and end dates for phases
        for phase_id, phase in self.phase_registry.items():
            phase_start_date, phase_end_date = self._calculate_phase_dates(phase_id, start_date)
            phase.start_date = phase_start_date.isoformat()
            phase.end_date = phase_end_date.isoformat()
            timeline.phases[phase_id] = {
                "start_date": phase_start_date.isoformat(),
                "end_date": phase_end_date.isoformat()
            }
        
        # Calculate start and end dates for tasks
        for task_id, task in self.task_registry.items():
            task_start_date, task_end_date = self._calculate_task_dates(task_id, start_date)
            task.start_date = task_start_date.isoformat()
            task.end_date = task_end_date.isoformat()
            timeline.tasks[task_id] = {
                "start_date": task_start_date.isoformat(),
                "end_date": task_end_date.isoformat()
            }
        
        # Set timeline in the plan
        self.plan.timeline = timeline
        
        logger.debug(f"Created timeline from {start_date.isoformat()} to {end_date.isoformat()}")

    def _calculate_end_date(self, start_date: datetime.date) -> datetime.date:
        """
        Calculate the end date of the migration plan based on task effort and dependencies.
        
        Args:
            start_date: The start date of the migration plan
            
        Returns:
            datetime.date: The end date of the migration plan
        """
        # Create a dictionary to store the end date of each task
        task_end_dates = {}
        
        # Calculate end dates for all tasks
        for task_id, task in self.task_registry.items():
            task_end_dates[task_id] = self._calculate_task_end_date(task_id, start_date, task_end_dates)
        
        # Find the latest end date
        if task_end_dates:
            return max(task_end_dates.values())
        else:
            return start_date

    def _calculate_task_end_date(
        self, task_id: str, start_date: datetime.date, task_end_dates: Dict[str, datetime.date]
    ) -> datetime.date:
        """
        Calculate the end date of a task based on its effort and dependencies.
        
        Args:
            task_id: The ID of the task
            start_date: The start date of the migration plan
            task_end_dates: Dictionary of task end dates
            
        Returns:
            datetime.date: The end date of the task
        """
        task = self.task_registry.get(task_id)
        if not task:
            return start_date
        
        # If the task has no dependencies, it starts on the start date
        if not task.dependencies:
            return start_date + timedelta(days=task.estimated_effort_days)
        
        # Calculate the start date of the task based on its dependencies
        task_start_date = start_date
        for dependency_id in task.dependencies:
            if dependency_id in task_end_dates:
                # Use the cached end date
                dependency_end_date = task_end_dates[dependency_id]
            else:
                # Calculate the end date of the dependency
                dependency_end_date = self._calculate_task_end_date(dependency_id, start_date, task_end_dates)
                task_end_dates[dependency_id] = dependency_end_date
            
            # Update the task start date if the dependency end date is later
            if dependency_end_date > task_start_date:
                task_start_date = dependency_end_date
        
        # Calculate the end date of the task
        return task_start_date + timedelta(days=task.estimated_effort_days)

    def _calculate_phase_dates(
        self, phase_id: str, start_date: datetime.date
    ) -> Tuple[datetime.date, datetime.date]:
        """
        Calculate the start and end dates of a phase based on its tasks.
        
        Args:
            phase_id: The ID of the phase
            start_date: The start date of the migration plan
            
        Returns:
            Tuple[datetime.date, datetime.date]: The start and end dates of the phase
        """
        phase = self.phase_registry.get(phase_id)
        if not phase or not phase.tasks:
            return start_date, start_date
        
        # Get the earliest start date and latest end date of the tasks in the phase
        phase_start_date = None
        phase_end_date = None
        
        for task_id in phase.tasks:
            task = self.task_registry.get(task_id)
            if task and task.start_date and task.end_date:
                task_start_date = datetime.fromisoformat(task.start_date).date()
                task_end_date = datetime.fromisoformat(task.end_date).date()
                
                if phase_start_date is None or task_start_date < phase_start_date:
                    phase_start_date = task_start_date
                
                if phase_end_date is None or task_end_date > phase_end_date:
                    phase_end_date = task_end_date
        
        # If no tasks have dates, use the start date
        if phase_start_date is None:
            phase_start_date = start_date
        
        if phase_end_date is None:
            phase_end_date = start_date
        
        return phase_start_date, phase_end_date

    def _calculate_task_dates(
        self, task_id: str, start_date: datetime.date
    ) -> Tuple[datetime.date, datetime.date]:
        """
        Calculate the start and end dates of a task based on its dependencies.
        
        Args:
            task_id: The ID of the task
            start_date: The start date of the migration plan
            
        Returns:
            Tuple[datetime.date, datetime.date]: The start and end dates of the task
        """
        task = self.task_registry.get(task_id)
        if not task:
            return start_date, start_date
        
        # If the task has no dependencies, it starts on the start date
        if not task.dependencies:
            task_start_date = start_date
        else:
            # Calculate the start date of the task based on its dependencies
            task_start_date = start_date
            for dependency_id in task.dependencies:
                dependency = self.task_registry.get(dependency_id)
                if dependency and dependency.end_date:
                    dependency_end_date = datetime.fromisoformat(dependency.end_date).date()
                    if dependency_end_date > task_start_date:
                        task_start_date = dependency_end_date
        
        # Calculate the end date of the task
        task_end_date = task_start_date + timedelta(days=task.estimated_effort_days)
        
        return task_start_date, task_end_date

    def save_plan(self, output_path: str) -> None:
        """
        Save the migration plan to a JSON file.
        
        Args:
            output_path: Path to save the plan to
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Custom JSON encoder to handle enum values
            class EnumEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, Enum):
                        return obj.value
                    return super().default(obj)
            
            # Convert plan to dictionary with custom handling for enums
            def convert_to_dict(obj):
                if isinstance(obj, list):
                    return [convert_to_dict(item) for item in obj]
                elif hasattr(obj, "__dataclass_fields__"):
                    result = {}
                    for key, value in asdict(obj).items():
                        if isinstance(value, Enum):
                            result[key] = value.value
                        else:
                            result[key] = convert_to_dict(value)
                    return result
                elif isinstance(obj, dict):
                    return {key: convert_to_dict(value) for key, value in obj.items()}
                elif isinstance(obj, Enum):
                    return obj.value
                else:
                    return obj
            
            # Convert plan to dictionary
            plan_dict = {
                "phases": convert_to_dict(self.plan.phases),
                "tasks": convert_to_dict(self.plan.tasks),
                "dependencies": convert_to_dict(self.plan.dependencies),
                "timeline": convert_to_dict(self.plan.timeline) if self.plan.timeline else None,
                "architecture_design_path": self.plan.architecture_design_path,
                "analysis_report_path": self.plan.analysis_report_path,
                "timestamp": self.plan.timestamp
            }
            
            # Save to JSON file
            with open(output_path, 'w') as f:
                json.dump(plan_dict, f, indent=2)
            
            logger.info(f"Migration plan saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving migration plan: {str(e)}")
            raise


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Create a migration plan based on the architecture design")
    
    parser.add_argument(
        "--architecture-design",
        type=str,
        default="data/migration/mcp/architecture_design.json",
        help="Path to the architecture design JSON file (default: data/migration/mcp/architecture_design.json)"
    )
    
    parser.add_argument(
        "--analysis-report",
        type=str,
        default="data/migration/mcp/analysis_report.json",
        help="Path to the analysis report JSON file (default: data/migration/mcp/analysis_report.json)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="data/migration/mcp/migration_plan.json",
        help="Path to output the migration plan (default: data/migration/mcp/migration_plan.json)"
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
        
        # Create planner
        planner = MigrationPlanner(
            architecture_design_path=args.architecture_design,
            analysis_report_path=args.analysis_report,
            verbose=args.verbose
        )
        
        # Create migration plan
        plan = planner.create_migration_plan()
        
        # Save plan
        planner.save_plan(args.output)
        
        # Print summary
        print("\nMigration Plan Summary:")
        print(f"Total phases: {len(plan.phases)}")
        print(f"Total tasks: {len(plan.tasks)}")
        print(f"Total dependencies: {len(plan.dependencies)}")
        if plan.timeline:
            print(f"Timeline: {plan.timeline.start_date} to {plan.timeline.end_date}")
        print(f"Plan saved to: {args.output}")
        
        # Print phase summary
        print("\nPhases:")
        for phase in sorted(plan.phases, key=lambda p: p.order):
            task_count = len(phase.tasks)
            print(f"{phase.order}. {phase.name} ({task_count} tasks)")
        
        return 0
    except Exception as e:
        logger.error(f"Error during migration plan creation: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
