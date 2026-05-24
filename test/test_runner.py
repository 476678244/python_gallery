#!/usr/bin/env python3
"""Test runner script for SafeClaw"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=False, coverage=False, marker=None):
    """Run tests with specified options"""
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend([
            "--cov=core",
            "--cov=services", 
            "--cov=models",
            "--cov=utils",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
    
    # Add marker filter
    if marker:
        cmd.extend(["-m", marker])
    
    # Add test type filter
    if test_type == "unit":
        cmd.append("tests/unit")
    elif test_type == "integration":
        cmd.append("tests/integration")
    elif test_type == "ui":
        cmd.append("-m ui")
    elif test_type == "workflow":
        cmd.append("-m workflow")
    elif test_type == "memory":
        cmd.append("-m memory")
    elif test_type == "safety":
        cmd.append("-m safety")
    elif test_type == "llm":
        cmd.append("-m llm")
    elif test_type == "skills":
        cmd.append("-m skills")
    elif test_type == "slow":
        cmd.append("-m slow")
    # Default: all tests
    
    # Add timeout for tests
    cmd.extend(["--timeout=300"])
    
    # Add exit on first failure for CI
    if os.environ.get("CI"):
        cmd.append("-x")
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code: {e.returncode}")
        return e.returncode

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="SafeClaw Test Runner")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "integration", "ui", "workflow", "memory", "safety", "llm", "skills", "slow"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "-m", "--marker",
        help="Run tests with specific pytest marker"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running"
    )
    
    args = parser.parse_args()
    
    # Install test dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest", "pytest-cov", "pytest-asyncio", "pytest-mock",
            "pytest-timeout", "pytest-xdist"
        ], check=True)
    
    # Run tests
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage,
        marker=args.marker
    )
    
    # Print coverage summary if generated
    if args.coverage and Path("htmlcov").exists():
        print("\nCoverage report generated in htmlcov/index.html")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
