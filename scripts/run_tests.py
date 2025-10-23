#!/usr/bin/env python3
"""
Test runner script for Void Bot
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type="all", verbose=False, coverage=True, parallel=False):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])
    
    # Add test type filter
    if test_type == "unit":
        cmd.extend(["tests/unit", "-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["tests/integration", "-m", "integration"])
    elif test_type == "e2e":
        cmd.extend(["tests/e2e", "-m", "e2e"])
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        return False
    
    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def run_linting():
    """Run code linting."""
    print("Running code linting...")
    
    # Run flake8
    flake8_cmd = ["python", "-m", "flake8", ".", "--exclude=venv,venv-test"]
    flake8_result = subprocess.run(flake8_cmd)
    
    # Run mypy
    mypy_cmd = ["python", "-m", "mypy", ".", "--ignore-missing-imports"]
    mypy_result = subprocess.run(mypy_cmd)
    
    # Run bandit for security
    bandit_cmd = ["python", "-m", "bandit", "-r", ".", "-f", "json", "-o", "reports/bandit.json"]
    bandit_result = subprocess.run(bandit_cmd)
    
    return all([
        flake8_result.returncode == 0,
        mypy_result.returncode == 0,
        bandit_result.returncode == 0
    ])


def run_security_scan():
    """Run security scanning."""
    print("Running security scan...")
    
    # Run safety for dependency vulnerabilities
    safety_cmd = ["python", "-m", "safety", "check", "--json", "--output", "reports/safety.json"]
    safety_result = subprocess.run(safety_cmd)
    
    return safety_result.returncode == 0


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Void Bot Test Runner")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "e2e", "all"], 
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run code linting"
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security scanning"
    )
    parser.add_argument(
        "--all-checks",
        action="store_true",
        help="Run all checks (tests, linting, security)"
    )
    
    args = parser.parse_args()
    
    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    success = True
    
    if args.all_checks:
        # Run all checks
        print("Running all checks...")
        
        # Run tests
        print("\n=== Running Tests ===")
        success &= run_tests(args.type, args.verbose, not args.no_coverage, args.parallel)
        
        # Run linting
        print("\n=== Running Linting ===")
        success &= run_linting()
        
        # Run security scan
        print("\n=== Running Security Scan ===")
        success &= run_security_scan()
        
    else:
        # Run specific checks
        if args.lint:
            success &= run_linting()
        
        if args.security:
            success &= run_security_scan()
        
        if not args.lint and not args.security:
            # Run tests by default
            success &= run_tests(args.type, args.verbose, not args.no_coverage, args.parallel)
    
    if success:
        print("\n[SUCCESS] All checks passed!")
        sys.exit(0)
    else:
        print("\n[FAILED] Some checks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
