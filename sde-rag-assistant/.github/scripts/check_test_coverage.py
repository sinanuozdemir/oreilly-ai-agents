#!/usr/bin/env python3
"""
Test Coverage Analysis Script

Checks if changed code has corresponding test coverage.
"""

import argparse
import json
import os
import re
import subprocess
from typing import List, Dict, Set


def get_changed_functions(diff_text: str) -> Dict[str, List[str]]:
    """Extract functions changed per file from git diff."""
    changed = {}
    current_file = None
    
    for line in diff_text.split('\n'):
        # Track which file we're in
        if line.startswith('diff --git'):
            match = re.search(r'diff --git a/(.*?) b/', line)
            if match:
                current_file = match.group(1)
                changed[current_file] = []
        
        # Look for function definitions in the diff
        if current_file and line.startswith('+') and not line.startswith('+++'):
            # Match Python function definitions
            func_match = re.search(r'^\+def (\w+)\(', line)
            if func_match:
                changed[current_file].append(func_match.group(1))
            
            # Match class definitions
            class_match = re.search(r'^\+class (\w+)\(', line)
            if class_match:
                changed[current_file].append(class_match.group(1))
    
    # Remove empty entries
    return {k: v for k, v in changed.items() if v}


def find_test_files(directory: str = ".") -> List[str]:
    """Find all test files in the project."""
    test_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden and cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(os.path.join(root, file))
            elif file.endswith('_test.py'):
                test_files.append(os.path.join(root, file))
    
    return test_files


def parse_test_file(test_path: str) -> Set[str]:
    """Extract function names tested in a test file."""
    tested_functions = set()
    
    try:
        with open(test_path, 'r') as f:
            content = f.read()
        
        # Look for test function definitions
        test_pattern = r'def (test_\w+)\('
        tested_functions.update(re.findall(test_pattern, content))
        
        # Look for functions being tested (commonly called within tests)
        func_calls = re.findall(r'\.(\w+)\(', content)
        tested_functions.update(func_calls)
        
    except Exception:
        pass
    
    return tested_functions


def analyze_coverage(changed_functions: Dict[str, List[str]], 
                     test_files: List[str]) -> Dict:
    """Analyze test coverage for changed functions."""
    
    # Build map of all tested functions
    all_tested = set()
    test_file_map = {}  # function -> test file
    
    for test_file in test_files:
        tested = parse_test_file(test_file)
        for func in tested:
            all_tested.add(func)
            if func not in test_file_map:
                test_file_map[func] = []
            test_file_map[func].append(test_file)
    
    # Check coverage for each changed function
    coverage_report = {
        "covered": [],
        "uncovered": [],
        "needs_update": []
    }
    
    for filepath, functions in changed_functions.items():
        # Skip test files themselves
        if 'test' in filepath.lower():
            continue
        
        for func in functions:
            # Check if there's a test for this function
            test_name = f"test_{func.lower()}"
            alt_test_name = f"test_{func}"
            
            is_covered = (
                test_name in all_tested or 
                alt_test_name in all_tested or
                func in all_tested
            )
            
            if is_covered:
                coverage_report["covered"].append({
                    "function": func,
                    "file": filepath,
                    "test_found": True
                })
            else:
                coverage_report["uncovered"].append({
                    "function": func,
                    "file": filepath,
                    "suggested_test": f"test_{func.lower()}.py"
                })
    
    return coverage_report


def create_coverage_report(pr_number: int, coverage: Dict) -> str:
    """Create a markdown report for test coverage."""
    
    total = len(coverage["covered"]) + len(coverage["uncovered"])
    
    if total == 0:
        return """
## 🧪 Test Coverage Analysis

No new functions detected in this PR.
"""
    
    coverage_pct = len(coverage["covered"]) / total * 100
    
    report = f"""## 🧪 Test Coverage Analysis

**PR:** #{pr_number}  
**Coverage:** {len(coverage['covered'])}/{total} functions ({coverage_pct:.1f}%)

"""
    
    if coverage["uncovered"]:
        report += "### ⚠️ Functions Missing Tests\n\n"
        report += "| Function | File | Suggested Test File |\n"
        report += "|----------|------|---------------------|\n"
        
        for item in coverage["uncovered"][:15]:
            report += f"| `{item['function']}` | `{item['file']}` | `{item['suggested_test']}` |\n"
        
        if len(coverage["uncovered"]) > 15:
            report += f"| ... | ... | ... |\n"
            report += f"\n*And {len(coverage['uncovered']) - 15} more functions...*\n"
        
        report += "\n### 📝 Recommendations\n\n"
        report += "1. Add unit tests for each uncovered function\n"
        report += "2. Include edge case testing\n"
        report += "3. Add integration tests if the function interacts with external systems\n"
        
    else:
        report += "### ✅ All Changed Functions Have Tests\n\n"
        report += "Great job! All modified functions appear to have test coverage.\n"
    
    if coverage["covered"]:
        report += f"\n### ✓ Covered Functions ({len(coverage['covered'])})\n\n"
        for item in coverage["covered"][:10]:
            report += f"- `{item['function']}` in `{item['file']}`\n"
    
    report += """
---

*Generated by the Test Coverage Analysis Agent*
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Check Test Coverage')
    parser.add_argument('--pr-number', type=int, required=True)
    parser.add_argument('--base-ref', default='HEAD~1')
    
    args = parser.parse_args()
    
    print(f"🧪 Analyzing test coverage for PR #{args.pr_number}")
    
    # Get diff
    result = subprocess.run(
        ['git', 'diff', args.base_ref, 'HEAD'],
        capture_output=True,
        text=True
    )
    diff = result.stdout
    
    # Get changed functions
    changed = get_changed_functions(diff)
    print(f"📁 Found changes in {len(changed)} files")
    
    # Find test files
    test_files = find_test_files()
    print(f"🧪 Found {len(test_files)} test files")
    
    # Analyze coverage
    coverage = analyze_coverage(changed, test_files)
    print(f"   ✓ Covered: {len(coverage['covered'])}")
    print(f"   ✗ Uncovered: {len(coverage['uncovered'])}")
    
    # Create report
    report = create_coverage_report(args.pr_number, coverage)
    
    # Save if there are findings
    if coverage["uncovered"] or coverage["covered"]:
        with open('test_coverage_report.md', 'w') as f:
            f.write(report)
        
        with open('coverage_analysis.json', 'w') as f:
            json.dump(coverage, f, indent=2)
        
        print("✅ Coverage report saved")
    else:
        print("ℹ️ No functions to analyze")


if __name__ == '__main__':
    main()
