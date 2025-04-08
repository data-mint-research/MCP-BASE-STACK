#!/usr/bin/env python3
"""
Code Standards Enforcement Script

This script provides a unified interface to check and fix code quality issues
based on the standards defined in the specification manifest. It integrates with
the QualityEnforcer class and provides more granular control over which standards
to enforce.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

try:
    from core.quality.enforcer import QualityEnforcer
    from core.config.settings import get_config
    HAS_QUALITY_ENFORCER = True
except ImportError:
    HAS_QUALITY_ENFORCER = False
    print("Warning: QualityEnforcer not available. Running in standalone mode.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("enforce_code_standards")

# Define paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SPEC_MANIFEST_PATH = PROJECT_ROOT / "config" / "specifications" / "specification-manifest.json"
REPORT_DIR = PROJECT_ROOT / "data" / "reports"
CHECK_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "utils" / "quality" / "check-code-quality.sh"
FIX_SCRIPT_PATH = PROJECT_ROOT / "scripts" / "utils" / "quality" / "fix-code-quality.sh"
KG_PATH = PROJECT_ROOT / "core" / "kg" / "data" / "knowledge_graph.graphml"

# Define file categories
FILE_CATEGORIES = {
    "python": ["*.py"],
    "shell": ["*.sh"],
    "markdown": ["*.md"],
    "yaml": ["*.yml", "*.yaml"],
    "json": ["*.json"],
    "javascript": ["*.js", "*.jsx"],
    "typescript": ["*.ts", "*.tsx"],
    "css": ["*.css", "*.scss", "*.sass"],
    "html": ["*.html", "*.htm"],
    "xml": ["*.xml"],
    "toml": ["*.toml"],
    "ini": ["*.ini"],
    "dockerfile": ["Dockerfile*"],
    "makefile": ["Makefile*"],
}

# Define tools by category
TOOLS_BY_CATEGORY = {
    "python": ["black", "isort", "flake8", "mypy", "pylint", "autopep8", "autoflake"],
    "shell": ["shellcheck", "shfmt"],
    "markdown": ["markdownlint"],
    "yaml": ["yamllint"],
    "json": [],
    "javascript": [],
    "typescript": [],
    "css": [],
    "html": [],
    "xml": [],
    "toml": [],
    "ini": [],
    "dockerfile": [],
    "makefile": [],
    "general": ["prettier"],
}


class CodeStandardsEnforcer:
    """
    A class that provides a unified interface to check and fix code quality issues.
    
    This class integrates with the QualityEnforcer class and provides more granular
    control over which standards to enforce.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CodeStandardsEnforcer.
        
        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.enforcer = QualityEnforcer() if HAS_QUALITY_ENFORCER else None
        self.spec_manifest = self._load_spec_manifest()
        self.report_dir = REPORT_DIR
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_spec_manifest(self) -> Dict[str, Any]:
        """
        Load the specification manifest.
        
        Returns:
            The specification manifest as a dictionary.
        """
        try:
            with open(SPEC_MANIFEST_PATH, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading specification manifest: {e}")
            return {}
    
    def _get_files_by_category(self, category: str, include_dirs: Optional[List[str]] = None,
                              exclude_dirs: Optional[List[str]] = None) -> List[str]:
        """
        Get files by category.
        
        Args:
            category: The category of files to get.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            
        Returns:
            List of file paths.
        """
        if category not in FILE_CATEGORIES:
            logger.warning(f"Unknown category: {category}")
            return []
        
        patterns = FILE_CATEGORIES[category]
        files = []
        
        include_dirs = include_dirs or ["."]
        exclude_dirs = exclude_dirs or [".git", "venv", "node_modules", "__pycache__"]
        
        for include_dir in include_dirs:
            for pattern in patterns:
                cmd = ["find", include_dir, "-type", "f", "-name", pattern]
                
                # Add exclude directories
                for exclude_dir in exclude_dirs:
                    cmd.extend(["-not", "-path", f"*/{exclude_dir}/*"])
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    found_files = result.stdout.strip().split("\n")
                    files.extend([f for f in found_files if f])
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error finding {pattern} files: {e}")
        
        return files
    
    def _run_shell_script(self, script_path: Path, args: List[str] = None) -> Tuple[int, str]:
        """
        Run a shell script.
        
        Args:
            script_path: Path to the shell script.
            args: Optional list of arguments to pass to the script.
            
        Returns:
            Tuple of (return_code, output).
        """
        args = args or []
        cmd = [str(script_path)] + args
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode, result.stdout + result.stderr
        except subprocess.SubprocessError as e:
            logger.error(f"Error running script {script_path}: {e}")
            return 1, str(e)
    
    def check_code_quality(self, categories: Optional[List[str]] = None,
                          tools: Optional[List[str]] = None,
                          include_dirs: Optional[List[str]] = None,
                          exclude_dirs: Optional[List[str]] = None,
                          report_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Check code quality.
        
        Args:
            categories: Optional list of file categories to check.
            tools: Optional list of tools to use.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            report_file: Optional path to the report file.
            
        Returns:
            Dictionary with the check results.
        """
        if self.enforcer:
            try:
                logger.info("Using QualityEnforcer for code quality checks")
                return self._check_with_enforcer(categories, tools, include_dirs, exclude_dirs, report_file)
            except Exception as e:
                logger.error(f"Error using QualityEnforcer: {e}")
                logger.info("Falling back to shell script for code quality checks")
                return self._check_with_script(categories, tools, include_dirs, exclude_dirs, report_file)
        else:
            logger.info("Using shell script for code quality checks")
            return self._check_with_script(categories, tools, include_dirs, exclude_dirs, report_file)
    
    def _check_with_enforcer(self, categories: Optional[List[str]] = None,
                            tools: Optional[List[str]] = None,
                            include_dirs: Optional[List[str]] = None,
                            exclude_dirs: Optional[List[str]] = None,
                            report_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Check code quality using the QualityEnforcer.
        
        Args:
            categories: Optional list of file categories to check.
            tools: Optional list of tools to use.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            report_file: Optional path to the report file.
            
        Returns:
            Dictionary with the check results.
        """
        # Get files to check
        files_to_check = []
        if categories:
            for category in categories:
                files_to_check.extend(self._get_files_by_category(category, include_dirs, exclude_dirs))
        else:
            # Use all files
            include_dirs = include_dirs or ["."]
            for include_dir in include_dirs:
                cmd = ["find", include_dir, "-type", "f"]
                
                # Add exclude directories
                exclude_dirs = exclude_dirs or [".git", "venv", "node_modules", "__pycache__"]
                for exclude_dir in exclude_dirs:
                    cmd.extend(["-not", "-path", f"*/{exclude_dir}/*"])
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    found_files = result.stdout.strip().split("\n")
                    files_to_check.extend([f for f in found_files if f])
                except subprocess.CalledProcessError as e:
                    logger.error(f"Error finding files: {e}")
        
        # Run checks
        results = []
        if tools:
            for tool in tools:
                if tool == "black":
                    results.extend(self.enforcer.run_check("black", files_to_check))
                elif tool == "isort":
                    results.extend(self.enforcer.run_check("isort", files_to_check))
                elif tool == "flake8":
                    results.extend(self.enforcer.run_check("flake8", files_to_check))
                elif tool == "mypy":
                    results.extend(self.enforcer.run_check("mypy", files_to_check))
                elif tool == "pylint":
                    results.extend(self.enforcer.run_check("pylint", files_to_check))
                else:
                    logger.warning(f"Unknown tool: {tool}")
        else:
            # Run all checks
            results = self.enforcer.run_all_checks(files_to_check)
        
        # Generate report
        # Convert QualityCheckResult objects to dictionaries with serializable values
        serializable_results = []
        for result in results:
            result_dict = {}
            for key, value in result.__dict__.items():
                # Convert enum values to strings
                if hasattr(value, 'value'):
                    result_dict[key] = value.value
                else:
                    result_dict[key] = value
            serializable_results.append(result_dict)
            
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": serializable_results,
            "summary": {
                "total_checks": len(results),
                "passed": len([r for r in results if not hasattr(r, 'error') or not r.error]),
                "failed": len([r for r in results if hasattr(r, 'error') and r.error]),
            }
        }
        
        # Save report
        if report_file:
            report_path = Path(report_file)
        else:
            report_path = self.report_dir / f"code_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to {report_path}")
        
        # Update knowledge graph
        self._update_knowledge_graph(report)
        
        return report
    
    def _check_with_script(self, categories: Optional[List[str]] = None,
                          tools: Optional[List[str]] = None,
                          include_dirs: Optional[List[str]] = None,
                          exclude_dirs: Optional[List[str]] = None,
                          report_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Check code quality using the shell script.
        
        Args:
            categories: Optional list of file categories to check.
            tools: Optional list of tools to use.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            report_file: Optional path to the report file.
            
        Returns:
            Dictionary with the check results.
        """
        args = []
        
        # Add categories
        if categories:
            args.append("--categories")
            args.append(",".join(categories))
        
        # Add tools
        if tools:
            args.append("--tools")
            args.append(",".join(tools))
        
        # Add include directories
        if include_dirs:
            args.append("--include-dirs")
            args.append(",".join(include_dirs))
        
        # Add exclude directories
        if exclude_dirs:
            args.append("--exclude-dirs")
            args.append(",".join(exclude_dirs))
        
        # Add report file
        if report_file:
            args.append("--report")
            args.append(report_file)
        
        # Run the script
        return_code, output = self._run_shell_script(CHECK_SCRIPT_PATH, args)
        
        # Parse the report
        if report_file:
            report_path = Path(report_file)
        else:
            # Find the latest report
            reports = list(self.report_dir.glob("code_quality_report_*.json"))
            if reports:
                report_path = max(reports, key=os.path.getmtime)
            else:
                logger.warning("No report found")
                return {"error": "No report found"}
        
        try:
            with open(report_path, "r") as f:
                report = json.load(f)
            
            logger.info(f"Report loaded from {report_path}")
            return report
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading report: {e}")
            return {"error": str(e), "output": output}
    
    def fix_code_quality(self, categories: Optional[List[str]] = None,
                        tools: Optional[List[str]] = None,
                        include_dirs: Optional[List[str]] = None,
                        exclude_dirs: Optional[List[str]] = None,
                        report_file: Optional[str] = None,
                        interactive: bool = False,
                        preview: bool = False,
                        verify: bool = True) -> Dict[str, Any]:
        """
        Fix code quality issues.
        
        Args:
            categories: Optional list of file categories to fix.
            tools: Optional list of tools to use.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            report_file: Optional path to the report file.
            interactive: Whether to use interactive mode.
            preview: Whether to preview fixes before applying them.
            verify: Whether to verify fixes after applying them.
            
        Returns:
            Dictionary with the fix results.
        """
        if self.enforcer:
            try:
                logger.info("Using QualityEnforcer for code quality fixes")
                return self._fix_with_enforcer(categories, tools, include_dirs, exclude_dirs, report_file,
                                            interactive, preview, verify)
            except Exception as e:
                logger.error(f"Error using QualityEnforcer: {e}")
                logger.info("Falling back to shell script for code quality fixes")
                return self._fix_with_script(categories, tools, include_dirs, exclude_dirs, report_file)
        else:
            logger.info("Using shell script for code quality fixes")
            return self._fix_with_script(categories, tools, include_dirs, exclude_dirs, report_file)
    
    def _fix_with_enforcer(self, categories: Optional[List[str]] = None,
                          tools: Optional[List[str]] = None,
                          include_dirs: Optional[List[str]] = None,
                          exclude_dirs: Optional[List[str]] = None,
                          report_file: Optional[str] = None,
                          interactive: bool = False,
                          preview: bool = False,
                          verify: bool = True) -> Dict[str, Any]:
        """
        Fix code quality issues using the QualityEnforcer.
        
        Args:
            categories: Optional list of file categories to fix.
            tools: Optional list of tools to use.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            report_file: Optional path to the report file.
            interactive: Whether to use interactive mode.
            preview: Whether to preview fixes before applying them.
            verify: Whether to verify fixes after applying them.
            
        Returns:
            Dictionary with the fix results.
        """
        # First run checks to get issues
        check_report = self.check_code_quality(categories, tools, include_dirs, exclude_dirs)
        
        # Get results that can be fixed
        fixable_results = [r for r in check_report["results"] if r.get("fix_available", False)]
        
        if not fixable_results:
            logger.info("No fixable issues found")
            return {"fixed": 0, "unfixed": len(check_report["results"])}
        
        # Fix issues
        fixed_count, unfixed_count = self.enforcer.auto_fix_issues(
            file_paths=None,  # Use the files from the check
            interactive=interactive,
            preview=preview,
            verify=verify
        )
        
        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "fixed_count": fixed_count,
            "unfixed_count": unfixed_count,
            "total_issues": len(check_report["results"]),
            "fixable_issues": len(fixable_results),
        }
        
        # Save report
        if report_file:
            report_path = Path(report_file)
        else:
            report_path = self.report_dir / f"code_quality_fixes_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Fix report saved to {report_path}")
        
        # Update knowledge graph
        self._update_knowledge_graph(report, fixes=True)
        
        return report
    
    def _fix_with_script(self, categories: Optional[List[str]] = None,
                        tools: Optional[List[str]] = None,
                        include_dirs: Optional[List[str]] = None,
                        exclude_dirs: Optional[List[str]] = None,
                        report_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Fix code quality issues using the shell script.
        
        Args:
            categories: Optional list of file categories to fix.
            tools: Optional list of tools to use.
            include_dirs: Optional list of directories to include.
            exclude_dirs: Optional list of directories to exclude.
            report_file: Optional path to the report file.
            
        Returns:
            Dictionary with the fix results.
        """
        args = []
        
        # Add categories
        if categories:
            args.append("--categories")
            args.append(",".join(categories))
        
        # Add tools
        if tools:
            args.append("--tools")
            args.append(",".join(tools))
        
        # Add include directories
        if include_dirs:
            args.append("--include-dirs")
            args.append(",".join(include_dirs))
        
        # Add exclude directories
        if exclude_dirs:
            args.append("--exclude-dirs")
            args.append(",".join(exclude_dirs))
        
        # Add report file
        if report_file:
            args.append("--report")
            args.append(report_file)
        
        # Run the script
        return_code, output = self._run_shell_script(FIX_SCRIPT_PATH, args)
        
        # Parse the report
        if report_file:
            report_path = Path(report_file)
        else:
            # Find the latest report
            reports = list(self.report_dir.glob("code_quality_fixes_report_*.json"))
            if reports:
                report_path = max(reports, key=os.path.getmtime)
            else:
                logger.warning("No report found")
                return {"error": "No report found"}
        
        try:
            with open(report_path, "r") as f:
                report = json.load(f)
            
            logger.info(f"Report loaded from {report_path}")
            return report
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading report: {e}")
            return {"error": str(e), "output": output}
    
    def _update_knowledge_graph(self, report: Dict[str, Any], fixes: bool = False) -> None:
        """
        Update the knowledge graph with the report.
        
        Args:
            report: The report to update the knowledge graph with.
            fixes: Whether the report is for fixes.
        """
        if not os.path.exists(KG_PATH):
            logger.warning(f"Knowledge graph not found at {KG_PATH}")
            return
        
        logger.info("Updating knowledge graph...")
        
        # Save the report to a temporary file
        report_path = self.report_dir / f"temp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Run the Python script to update the knowledge graph
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "utils" / "quality" / "check_code_quality_nodes.py"),
            "--report", str(report_path)
        ]
        
        if fixes:
            cmd.append("--fixes")
        
        try:
            subprocess.run(cmd, check=True)
            logger.info("Knowledge graph updated successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating knowledge graph: {e}")
        
        # Remove the temporary file
        os.unlink(report_path)


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Enforce code standards")
    
    # Main actions
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check code quality")
    group.add_argument("--fix", action="store_true", help="Fix code quality issues")
    group.add_argument("--list-categories", action="store_true", help="List available file categories")
    group.add_argument("--list-tools", action="store_true", help="List available tools")
    
    # Options for both check and fix
    parser.add_argument("--categories", type=str, help="Comma-separated list of file categories to check/fix")
    parser.add_argument("--tools", type=str, help="Comma-separated list of tools to use")
    parser.add_argument("--include-dirs", type=str, help="Comma-separated list of directories to include")
    parser.add_argument("--exclude-dirs", type=str, help="Comma-separated list of directories to exclude")
    parser.add_argument("--report", type=str, help="Path to the report file")
    
    # Options for fix only
    parser.add_argument("--interactive", action="store_true", help="Use interactive mode for fixes")
    parser.add_argument("--preview", action="store_true", help="Preview fixes before applying them")
    parser.add_argument("--no-verify", action="store_true", help="Don't verify fixes after applying them")
    
    return parser.parse_args()


def main() -> int:
    """
    Main function.
    
    Returns:
        Exit code.
    """
    args = parse_args()
    
    # Handle list options
    if args.list_categories:
        print("Available file categories:")
        for category in sorted(FILE_CATEGORIES.keys()):
            patterns = ", ".join(FILE_CATEGORIES[category])
            print(f"  {category}: {patterns}")
        return 0
    
    if args.list_tools:
        print("Available tools by category:")
        for category, tools in sorted(TOOLS_BY_CATEGORY.items()):
            if tools:
                print(f"  {category}: {', '.join(tools)}")
        return 0
    
    # Parse options for check and fix commands
    categories = args.categories.split(",") if args.categories else None
    tools = args.tools.split(",") if args.tools else None
    include_dirs = args.include_dirs.split(",") if args.include_dirs else None
    exclude_dirs = args.exclude_dirs.split(",") if args.exclude_dirs else None
    
    # Create enforcer
    enforcer = CodeStandardsEnforcer()
    
    # Run check action
    if args.check:
        logger.info("Checking code quality...")
        report = enforcer.check_code_quality(
            categories=categories,
            tools=tools,
            include_dirs=include_dirs,
            exclude_dirs=exclude_dirs,
            report_file=args.report
        )
        
        # Print summary
        if "summary" in report:
            print("\nSummary:")
            print(f"  Total checks: {report['summary']['total_checks']}")
            print(f"  Passed: {report['summary']['passed']}")
            print(f"  Failed: {report['summary']['failed']}")
        
        # Return non-zero if any checks failed
        return 1 if report.get("summary", {}).get("failed", 0) > 0 else 0
    
    # Run fix action
    elif args.fix:
        logger.info("Fixing code quality issues...")
        report = enforcer.fix_code_quality(
            categories=categories,
            tools=tools,
            include_dirs=include_dirs,
            exclude_dirs=exclude_dirs,
            report_file=args.report,
            interactive=args.interactive,
            preview=args.preview,
            verify=not args.no_verify
        )
        
        # Print summary
        print("\nSummary:")
        print(f"  Fixed issues: {report.get('fixed_count', 0)}")
        print(f"  Unfixed issues: {report.get('unfixed_count', 0)}")
        
        # Return non-zero if any issues couldn't be fixed
        return 1 if report.get("unfixed_count", 0) > 0 else 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())