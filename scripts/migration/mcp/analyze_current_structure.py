#!/usr/bin/env python3
"""
MCP Migration - Current Structure Analysis Script

This script analyzes the current project structure and compares it with the target
structure defined in structure.yaml. It identifies components that need to be migrated,
components that are missing, and components that are already in place.

Usage:
    python analyze_current_structure.py [--codebase-path PATH] [--target-structure PATH] [--output PATH]

Arguments:
    --codebase-path PATH       Path to the codebase to analyze (default: current directory)
    --target-structure PATH    Path to the target structure YAML file (default: structure.yaml)
    --output PATH              Path to output the analysis report (default: analysis_report.json)
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


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("mcp_analysis.log")
    ]
)
logger = logging.getLogger("mcp_analysis")


@dataclass
class Component:
    """Represents a component in the project structure."""
    name: str
    path: str
    description: str = ""
    required_files: List[str] = field(default_factory=list)
    components: Dict[str, "Component"] = field(default_factory=dict)
    existing_files: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)


@dataclass
class AnalysisReport:
    """Represents the analysis report."""
    components: List[Dict[str, Any]] = field(default_factory=list)
    migration_candidates: List[Dict[str, Any]] = field(default_factory=list)
    missing_components: List[Dict[str, Any]] = field(default_factory=list)
    existing_components: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = ""
    codebase_path: str = ""
    target_structure_path: str = ""


class StructureAnalyzer:
    """Analyzes the current project structure and compares it with the target structure."""

    def __init__(self, codebase_path: str, target_structure_path: str, verbose: bool = False):
        """
        Initialize the StructureAnalyzer.

        Args:
            codebase_path: Path to the codebase to analyze
            target_structure_path: Path to the target structure YAML file
            verbose: Whether to enable verbose logging
        """
        self.codebase_path = os.path.abspath(codebase_path)
        self.target_structure_path = target_structure_path
        self.verbose = verbose
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        logger.info(f"Initializing StructureAnalyzer with codebase path: {self.codebase_path}")
        logger.info(f"Target structure path: {self.target_structure_path}")
        
        # Validate paths
        self._validate_paths()
        
        # Load target structure
        self.target_structure = self._load_target_structure()
        
        # Initialize analysis report
        self.report = AnalysisReport(
            codebase_path=self.codebase_path,
            target_structure_path=self.target_structure_path,
            timestamp=self._get_timestamp()
        )

    def _validate_paths(self) -> None:
        """Validate that the specified paths exist."""
        if not os.path.exists(self.codebase_path):
            raise FileNotFoundError(f"Codebase path does not exist: {self.codebase_path}")
        
        if not os.path.exists(self.target_structure_path):
            raise FileNotFoundError(f"Target structure file does not exist: {self.target_structure_path}")

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

    def _get_timestamp(self) -> str:
        """Get the current timestamp as a string."""
        from datetime import datetime
        return datetime.now().isoformat()

    def analyze(self) -> AnalysisReport:
        """
        Analyze the current project structure and compare it with the target structure.
        
        Returns:
            AnalysisReport: The analysis report
        """
        logger.info("Starting structure analysis...")
        
        # Get the structure definition from the loaded YAML
        structure_def = self.target_structure.get("structure", {})
        
        # Analyze each top-level component
        for component_name, component_def in structure_def.items():
            logger.info(f"Analyzing component: {component_name}")
            component = self._analyze_component(component_name, component_def, os.path.join(self.codebase_path, component_name))
            
            # Add component to the report
            self._add_component_to_report(component)
        
        logger.info("Structure analysis completed")
        return self.report

    def _analyze_component(self, name: str, definition: Dict[str, Any], path: str) -> Component:
        """
        Analyze a component and its subcomponents.
        
        Args:
            name: Name of the component
            definition: Component definition from the target structure
            path: Path to the component in the codebase
            
        Returns:
            Component: The analyzed component
        """
        logger.debug(f"Analyzing component {name} at path {path}")
        
        # Create a new component
        component = Component(
            name=name,
            path=path,
            description=definition.get("description", "")
        )
        
        # Check required files
        required_files = definition.get("required_files", [])
        component.required_files = required_files
        
        existing_files = []
        missing_files = []
        
        for file_path in required_files:
            absolute_path = os.path.join(self.codebase_path, file_path)
            if os.path.exists(absolute_path):
                existing_files.append(file_path)
                logger.debug(f"File exists: {file_path}")
            else:
                missing_files.append(file_path)
                logger.debug(f"File missing: {file_path}")
        
        component.existing_files = existing_files
        component.missing_files = missing_files
        
        # Analyze subcomponents
        subcomponents = definition.get("components", {})
        for subcomponent_name, subcomponent_def in subcomponents.items():
            subcomponent_path = os.path.join(path, subcomponent_name)
            subcomponent = self._analyze_component(
                subcomponent_name, 
                subcomponent_def, 
                subcomponent_path
            )
            component.components[subcomponent_name] = subcomponent
        
        return component

    def _add_component_to_report(self, component: Component) -> None:
        """
        Add a component to the analysis report.
        
        Args:
            component: The component to add to the report
        """
        # Convert component to dictionary for the report
        component_dict = self._component_to_dict(component)
        
        # Add to components list
        self.report.components.append(component_dict)
        
        # Determine if this is a migration candidate, missing, or existing component
        if component.missing_files and component.existing_files:
            # Component exists but needs migration
            self.report.migration_candidates.append(component_dict)
        elif not component.existing_files and component.missing_files:
            # Component is completely missing
            self.report.missing_components.append(component_dict)
        elif component.existing_files and not component.missing_files:
            # Component exists completely
            self.report.existing_components.append(component_dict)
        
        # Process subcomponents
        for subcomponent in component.components.values():
            self._add_component_to_report(subcomponent)

    def _component_to_dict(self, component: Component) -> Dict[str, Any]:
        """
        Convert a Component object to a dictionary for the report.
        
        Args:
            component: The component to convert
            
        Returns:
            Dict[str, Any]: The component as a dictionary
        """
        return {
            "name": component.name,
            "path": component.path,
            "description": component.description,
            "required_files": component.required_files,
            "existing_files": component.existing_files,
            "missing_files": component.missing_files,
            "migration_status": self._get_migration_status(component),
            "completion_percentage": self._calculate_completion_percentage(component)
        }

    def _get_migration_status(self, component: Component) -> str:
        """
        Determine the migration status of a component.
        
        Args:
            component: The component to check
            
        Returns:
            str: The migration status ("complete", "partial", or "missing")
        """
        if not component.required_files:
            # If no required files, check subcomponents
            if not component.components:
                return "complete"  # No requirements, so it's complete
            
            # Check if all subcomponents are complete
            statuses = [self._get_migration_status(c) for c in component.components.values()]
            if all(s == "complete" for s in statuses):
                return "complete"
            elif all(s == "missing" for s in statuses):
                return "missing"
            else:
                return "partial"
        
        # Check based on required files
        if not component.missing_files:
            return "complete"
        elif not component.existing_files:
            return "missing"
        else:
            return "partial"

    def _calculate_completion_percentage(self, component: Component) -> float:
        """
        Calculate the completion percentage of a component.
        
        Args:
            component: The component to calculate completion for
            
        Returns:
            float: The completion percentage (0-100)
        """
        if not component.required_files:
            # If no required files, check subcomponents
            if not component.components:
                return 100.0  # No requirements, so it's 100% complete
            
            # Calculate average of subcomponents
            percentages = [self._calculate_completion_percentage(c) for c in component.components.values()]
            return sum(percentages) / len(percentages) if percentages else 100.0
        
        # Calculate based on required files
        total_files = len(component.required_files)
        existing_files = len(component.existing_files)
        
        if total_files == 0:
            return 100.0
        
        return (existing_files / total_files) * 100.0

    def save_report(self, output_path: str) -> None:
        """
        Save the analysis report to a JSON file.
        
        Args:
            output_path: Path to save the report to
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Convert report to dictionary
            report_dict = asdict(self.report)
            
            # Save to JSON file
            with open(output_path, 'w') as f:
                json.dump(report_dict, f, indent=2)
            
            logger.info(f"Analysis report saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving analysis report: {str(e)}")
            raise


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Analyze current project structure for MCP migration")
    
    parser.add_argument(
        "--codebase-path",
        type=str,
        default=".",
        help="Path to the codebase to analyze (default: current directory)"
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
        default="data/migration/mcp/analysis_report.json",
        help="Path to output the analysis report (default: data/migration/mcp/analysis_report.json)"
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
        
        # Create analyzer
        analyzer = StructureAnalyzer(
            codebase_path=args.codebase_path,
            target_structure_path=args.target_structure,
            verbose=args.verbose
        )
        
        # Perform analysis
        report = analyzer.analyze()
        
        # Save report
        analyzer.save_report(args.output)
        
        # Print summary
        print("\nAnalysis Summary:")
        print(f"Total components: {len(report.components)}")
        print(f"Migration candidates: {len(report.migration_candidates)}")
        print(f"Missing components: {len(report.missing_components)}")
        print(f"Existing components: {len(report.existing_components)}")
        print(f"Report saved to: {args.output}")
        
        return 0
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())