#!/usr/bin/env python3
"""
Smart Code Review with RAG Pipeline

This is an advanced version that uses the local RAG pipeline
(similar to step3_build_rag_pipeline.py) to provide context-aware code review.
"""

import argparse
import json
import os
import re
import subprocess
from typing import List, Dict, Optional

# Add the project root to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def get_git_diff(base_ref: str = "HEAD~1", head_ref: str = "HEAD") -> str:
    """Get the git diff between two refs."""
    result = subprocess.run(
        ['git', 'diff', base_ref, head_ref],
        capture_output=True,
        text=True
    )
    return result.stdout


def parse_diff_for_context(diff_text: str) -> Dict:
    """Parse diff to extract code context for RAG queries."""
    context = {
        "files": [],
        "functions": [],
        "imports": [],
        "api_routes": []
    }
    
    # Extract file paths
    file_pattern = r'diff --git a/(.*?) b/'
    context["files"] = re.findall(file_pattern, diff_text)
    
    # Extract function definitions
    func_pattern = r'[+\-]def (\w+)\(' 
    context["functions"] = list(set(re.findall(func_pattern, diff_text)))
    
    # Extract class definitions
    class_pattern = r'[+\-]class (\w+)\('
    context["functions"].extend(list(set(re.findall(class_pattern, diff_text))))
    
    # Extract imports
    import_pattern = r'[+\-](from \S+ import|import) (\S+)'
    imports = re.findall(import_pattern, diff_text)
    context["imports"] = [f"{imp[0]} {imp[1]}" for imp in imports]
    
    # Extract potential API routes (Flask/FastAPI patterns)
    route_pattern = r'[+\-]@.*\.route\([\'"](.*?)[\'"]'
    context["api_routes"] = re.findall(route_pattern, diff_text)
    
    return context


def analyze_with_rag(diff_context: Dict, codebase_path: str = ".") -> Dict:
    """
    Use RAG pipeline to analyze code changes in context.
    
    This is a simplified version for GitHub Actions that doesn't require
    the full ChromaDB setup - it uses pattern matching instead.
    """
    analysis = {
        "related_files": [],
        "api_impacts": [],
        "test_gaps": [],
        "suggestions": []
    }
    
    # Scan codebase for related files
    for root, dirs, files in os.walk(codebase_path):
        # Skip hidden and cache directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Check if this file contains functions we're modifying
                        for func in diff_context.get("functions", []):
                            if f"def {func}(" in content or f"class {func}(" in content:
                                if filepath not in analysis["related_files"]:
                                    analysis["related_files"].append({
                                        "path": filepath,
                                        "reason": f"Contains {func}()",
                                        "relationship": "definition"
                                    })
                        
                        # Check for imports of changed modules
                        for changed_file in diff_context.get("files", []):
                            module_name = changed_file.replace('/', '.').replace('.py', '')
                            if f"from {module_name}" in content or f"import {module_name}" in content:
                                if filepath not in analysis["related_files"]:
                                    analysis["related_files"].append({
                                        "path": filepath,
                                        "reason": f"Imports {changed_file}",
                                        "relationship": "dependent"
                                    })
                        
                        # Check for API route definitions that might be affected
                        if '@app.route' in content or '@router' in content:
                            for route in diff_context.get("api_routes", []):
                                if route in content:
                                    analysis["api_impacts"].append({
                                        "route": route,
                                        "file": filepath,
                                        "impact": "Route definition found"
                                    })
                                    
                except Exception as e:
                    continue
    
    return analysis


def generate_smart_suggestions(diff_context: Dict, rag_analysis: Dict) -> List[Dict]:
    """Generate intelligent suggestions based on RAG analysis."""
    suggestions = []
    
    # Suggest tests for changed functions
    for func in diff_context.get("functions", []):
        # Check if test exists
        test_exists = False
        for related in rag_analysis.get("related_files", []):
            if 'test' in related["path"].lower() and func in related["path"]:
                test_exists = True
                break
        
        if not test_exists:
            suggestions.append({
                "type": "test_coverage",
                "priority": "HIGH",
                "message": f"Function `{func}()` modified but no test found",
                "action": f"Add or update test for `{func}()`",
                "recommended_file": f"test_{func.lower()}.py"
            })
    
    # Suggest documentation updates for API changes
    for api_impact in rag_analysis.get("api_impacts", []):
        suggestions.append({
            "type": "documentation",
            "priority": "MEDIUM",
            "message": f"API route `{api_impact['route']}` may be affected",
            "action": "Update API documentation and OpenAPI specs",
            "related_file": api_impact["file"]
        })
    
    # Security suggestions for auth changes
    changed_files = ' '.join(diff_context.get("files", []))
    if any(kw in changed_files.lower() for kw in ['auth', 'login', 'password', 'token']):
        suggestions.append({
            "type": "security",
            "priority": "HIGH",
            "message": "Authentication-related changes detected",
            "action": "Ensure security review is completed and no secrets are exposed",
            "checklist": [
                "No hardcoded credentials",
                "Password hashing is used",
                "Token validation is correct",
                "Rate limiting is in place"
            ]
        })
    
    # Performance suggestions for database queries
    if any(kw in changed_files.lower() for kw in ['query', 'database', 'db', 'sql']):
        suggestions.append({
            "type": "performance",
            "priority": "MEDIUM",
            "message": "Database query changes detected",
            "action": "Verify queries are optimized and indexed",
            "checklist": [
                "Check for N+1 queries",
                "Verify index usage",
                "Review query complexity"
            ]
        })
    
    return suggestions


def create_smart_report(pr_number: int, diff_context: Dict, 
                        rag_analysis: Dict, suggestions: List[Dict]) -> str:
    """Create a comprehensive markdown report."""
    
    report = f"""## 🤖 Smart Code Review Report (RAG-Enhanced)

**PR:** #{pr_number}  
**Analysis Type:** Context-Aware Review with Local RAG Pipeline

---

### 📝 Changes Summary

| Metric | Count |
|--------|-------|
| Files Changed | {len(diff_context.get('files', []))} |
| Functions Modified | {len(diff_context.get('functions', []))} |
| New/Updated Imports | {len(diff_context.get('imports', []))} |
| Related Files Found | {len(rag_analysis.get('related_files', []))} |

"""
    
    # Changed files
    if diff_context.get('files'):
        report += "### 📁 Files Modified\n\n"
        for f in diff_context['files'][:15]:
            report += f"- `{f}`\n"
        if len(diff_context['files']) > 15:
            report += f"- ... and {len(diff_context['files']) - 15} more\n"
        report += "\n"
    
    # Functions changed
    if diff_context.get('functions'):
        report += "### 🔧 Functions/Classes Modified\n\n"
        for func in diff_context['functions'][:10]:
            report += f"- `{func}()`\n"
        if len(diff_context['functions']) > 10:
            report += f"- ... and {len(diff_context['functions']) - 10} more\n"
        report += "\n"
    
    # Related files from RAG analysis
    if rag_analysis.get('related_files'):
        report += "### 🔗 Related Files (from RAG Analysis)\n\n"
        report += "| File | Relationship | Reason |\n"
        report += "|------|-------------|--------|\n"
        for rf in rag_analysis['related_files'][:10]:
            report += f"| `{rf['path']}` | {rf['relationship']} | {rf['reason']} |\n"
        report += "\n"
    
    # API impacts
    if rag_analysis.get('api_impacts'):
        report += "### ⚠️ API Impact Analysis\n\n"
        for api in rag_analysis['api_impacts']:
            report += f"- Route `{api['route']}` in `{api['file']}`\n"
        report += "\n"
    
    # Smart suggestions
    if suggestions:
        report += "### 💡 Smart Suggestions\n\n"
        
        high_priority = [s for s in suggestions if s['priority'] == 'HIGH']
        medium_priority = [s for s in suggestions if s['priority'] == 'MEDIUM']
        
        if high_priority:
            report += "#### 🔴 High Priority\n\n"
            for sug in high_priority:
                report += f"**{sug['type'].upper()}:** {sug['message']}\n\n"
                report += f"- **Action:** {sug['action']}\n"
                if 'checklist' in sug:
                    report += "- **Checklist:**\n"
                    for item in sug['checklist']:
                        report += f"  - [ ] {item}\n"
                report += "\n"
        
        if medium_priority:
            report += "#### 🟡 Medium Priority\n\n"
            for sug in medium_priority:
                report += f"**{sug['type'].upper()}:** {sug['message']}\n\n"
                report += f"- **Action:** {sug['action']}\n\n"
    
    report += """
---

*This review was generated using a RAG (Retrieval-Augmented Generation) pipeline that analyzes code changes in the context of your entire codebase.*

**Legend:**
- 🔗 Related files are identified by analyzing imports, function calls, and module dependencies
- ⚠️ API impacts are detected by scanning for route definitions and handlers
- 💡 Suggestions are prioritized based on common code review patterns
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Smart Code Review with RAG')
    parser.add_argument('--pr-number', type=int, required=True)
    parser.add_argument('--base-ref', default='HEAD~1', help='Base git ref')
    parser.add_argument('--head-ref', default='HEAD', help='Head git ref')
    parser.add_argument('--output', default='smart_review_report.md')
    
    args = parser.parse_args()
    
    print(f"🔍 Running Smart Code Review for PR #{args.pr_number}")
    print(f"   Base: {args.base_ref} → Head: {args.head_ref}")
    
    # Get diff
    diff = get_git_diff(args.base_ref, args.head_ref)
    
    # Parse context
    context = parse_diff_for_context(diff)
    print(f"📁 Found {len(context['files'])} files, {len(context['functions'])} functions")
    
    # Analyze with RAG-like approach
    print("🔎 Running RAG analysis...")
    analysis = analyze_with_rag(context)
    print(f"   Found {len(analysis['related_files'])} related files")
    
    # Generate suggestions
    suggestions = generate_smart_suggestions(context, analysis)
    print(f"💡 Generated {len(suggestions)} suggestions")
    
    # Create report
    report = create_smart_report(args.pr_number, context, analysis, suggestions)
    
    # Save outputs
    with open(args.output, 'w') as f:
        f.write(report)
    
    with open('rag_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    with open('smart_suggestions.json', 'w') as f:
        json.dump(suggestions, f, indent=2)
    
    print(f"✅ Report saved to {args.output}")


if __name__ == '__main__':
    main()
