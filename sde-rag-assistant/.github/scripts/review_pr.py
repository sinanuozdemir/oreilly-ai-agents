#!/usr/bin/env python3
"""
GitHub Action Script: AI Code Review Agent

This script runs as part of CI/CD to analyze PRs and provide AI-powered feedback.
"""

import argparse
import json
import os
import re
from typing import List, Dict
import requests


def get_pr_diff(repo: str, pr_number: int, token: str) -> str:
    """Fetch PR diff from GitHub API."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error fetching PR: {response.status_code}")
        return ""


def parse_changed_files(diff_text: str) -> List[Dict]:
    """Parse git diff to extract changed files and functions."""
    files = []
    
    # Simple regex to find file changes
    file_pattern = r'diff --git a/(.*?) b/'
    matches = re.findall(file_pattern, diff_text)
    
    for filepath in matches:
        # Detect function/class changes
        functions_changed = []
        
        # Look for Python function definitions in diff
        if filepath.endswith('.py'):
            func_pattern = r'[+\-]def (\w+)\('
            class_pattern = r'[+\-]class (\w+)\('
            
            # Extract section of diff for this file
            file_section = re.search(
                rf'diff --git a/{re.escape(filepath)} b/{re.escape(filepath)}.*?(?=diff --git|$)',
                diff_text,
                re.DOTALL
            )
            
            if file_section:
                section_text = file_section.group()
                functions_changed = re.findall(func_pattern, section_text)
                classes_changed = re.findall(class_pattern, section_text)
                functions_changed.extend(classes_changed)
        
        files.append({
            "path": filepath,
            "functions_changed": list(set(functions_changed))  # Remove duplicates
        })
    
    return files


def analyze_impact(files: List[Dict]) -> Dict:
    """Analyze impact of changes."""
    analysis = {
        "api_changes": [],
        "test_impact": [],
        "security_sensitive": False,
        "risk_level": "low"
    }
    
    for file in files:
        filepath = file["path"]
        
        # Check for API-related files
        if any(keyword in filepath.lower() for keyword in ['api', 'endpoint', 'route', 'view']):
            analysis["api_changes"].append(filepath)
            analysis["risk_level"] = "medium"
        
        # Check for auth/security files
        if any(keyword in filepath.lower() for keyword in ['auth', 'login', 'password', 'token', 'security']):
            analysis["security_sensitive"] = True
            analysis["risk_level"] = "high"
        
        # Check for payment-related changes
        if any(keyword in filepath.lower() for keyword in ['payment', 'stripe', 'charge', 'refund', 'billing']):
            analysis["security_sensitive"] = True
            analysis["risk_level"] = "high"
        
        # Check for test files
        if 'test' in filepath.lower():
            analysis["test_impact"].append(filepath)
    
    return analysis


def generate_test_suggestions(files: List[Dict]) -> List[Dict]:
    """Generate test suggestions based on changed files."""
    suggestions = []
    
    for file in files:
        filepath = file["path"]
        functions = file.get("functions_changed", [])
        
        # Skip test files themselves
        if 'test' in filepath.lower():
            continue
        
        # Suggest tests for changed functions
        if functions:
            for func in functions:
                suggestions.append({
                    "file": filepath,
                    "function": func,
                    "suggested_test": f"test_{func}",
                    "priority": "HIGH" if len(functions) <= 2 else "MEDIUM"
                })
        else:
            # Generic suggestion if we can't detect functions
            suggestions.append({
                "file": filepath,
                "function": "N/A",
                "suggested_test": f"Add unit tests for changes in {filepath}",
                "priority": "MEDIUM"
            })
    
    return suggestions


def create_review_report(pr_number: int, files: List[Dict], 
                         impact: Dict, suggestions: List[Dict]) -> str:
    """Create a formatted markdown report for the PR review."""
    
    report = f"""## 🤖 AI Code Review Report

**PR:** #{pr_number}  
**Files Changed:** {len(files)}  
**Risk Level:** {impact['risk_level'].upper()}

---

### 📊 Impact Analysis

"""
    
    if impact['api_changes']:
        report += "**API Changes Detected:**\n"
        for api_file in impact['api_changes']:
            report += f"- ⚠️ `{api_file}` - Verify API documentation is updated\n"
        report += "\n"
    
    if impact['security_sensitive']:
        report += "**🔒 Security Review Required**\n"
        report += "- Changes affect authentication, payment, or security components\n"
        report += "- Ensure security review is completed\n"
        report += "- Verify no sensitive data is logged\n\n"
    
    # Test suggestions
    report += "### 🧪 Test Suggestions\n\n"
    
    if suggestions:
        report += "| File | Function | Suggested Test | Priority |\n"
        report += "|------|----------|----------------|----------|\n"
        
        for sug in suggestions[:10]:  # Limit to 10 suggestions
            report += f"| `{sug['file']}` | {sug['function']} | {sug['suggested_test']} | {sug['priority']} |\n"
    else:
        report += "✅ No test suggestions - files may already have adequate coverage.\n"
    
    # Changed files summary
    report += "\n### 📁 Files Changed\n\n"
    for file in files[:20]:  # Limit to 20 files
        funcs = ", ".join(file.get("functions_changed", [])[:5])
        if funcs:
            report += f"- `{file['path']}` - Functions: {funcs}\n"
        else:
            report += f"- `{file['path']}`\n"
    
    if len(files) > 20:
        report += f"- ... and {len(files) - 20} more files\n"
    
    report += """

---

*This review was generated automatically by the AI Code Review Agent.*
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='AI Code Review Agent')
    parser.add_argument('--pr-number', type=int, required=True, help='PR number')
    parser.add_argument('--repo', type=str, required=True, help='Repository (owner/repo)')
    parser.add_argument('--changed-files', type=str, help='File with list of changed files')
    
    args = parser.parse_args()
    
    print(f"🔍 Analyzing PR #{args.pr_number} in {args.repo}")
    
    # Get GitHub token
    github_token = os.environ.get('GITHUB_TOKEN', '')
    
    # Get PR diff
    if github_token:
        diff = get_pr_diff(args.repo, args.pr_number, github_token)
        files = parse_changed_files(diff)
    else:
        # Fallback: read from file
        files = []
        if args.changed_files and os.path.exists(args.changed_files):
            with open(args.changed_files) as f:
                for line in f:
                    files.append({"path": line.strip(), "functions_changed": []})
    
    print(f"📁 Found {len(files)} changed files")
    
    # Analyze impact
    impact = analyze_impact(files)
    print(f"⚠️  Risk level: {impact['risk_level']}")
    
    # Generate test suggestions
    suggestions = generate_test_suggestions(files)
    print(f"🧪 Generated {len(suggestions)} test suggestions")
    
    # Create report
    report = create_review_report(args.pr_number, files, impact, suggestions)
    
    # Save report
    with open('review_report.md', 'w') as f:
        f.write(report)
    
    # Save JSON data for other tools
    with open('impact_analysis.json', 'w') as f:
        json.dump(impact, f, indent=2)
    
    with open('test_suggestions.json', 'w') as f:
        json.dump(suggestions, f, indent=2)
    
    print("✅ Review complete!")
    print("   - review_report.md")
    print("   - impact_analysis.json")
    print("   - test_suggestions.json")


if __name__ == '__main__':
    main()
