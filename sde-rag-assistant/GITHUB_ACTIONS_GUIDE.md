# 🤖 GitHub Actions Guide - AI Code Review Bot

This guide covers the production-ready CI/CD integration for automated code review using RAG (Retrieval-Augmented Generation).

## 📋 Table of Contents

1. [Overview](#overview)
2. [Setup Instructions](#setup-instructions)
3. [Workflow Details](#workflow-details)
4. [How It Works](#how-it-works)
5. [Customization](#customization)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

---

## Overview

We provide **two tiers** of GitHub Actions workflows:

### Tier 1: Basic Code Review (`code-review-agent.yml`)
- ✅ Runs on every PR
- ✅ Identifies changed files and functions
- ✅ Generates test suggestions
- ✅ Posts review comments

### Tier 2: Smart RAG Review (`smart-rag-review.yml`)
- 🧠 Context-aware analysis
- 🔗 Finds related files across codebase
- ⚠️ Detects API impacts and security risks
- 🧪 Comprehensive test coverage analysis
- 💡 Smart suggestions with checklists

---

## Setup Instructions

### Step 1: Add Repository Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Value | Required |
|--------|-------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes |
| `GITHUB_TOKEN` | Auto-generated | ✅ Auto |

### Step 2: Enable Workflows

1. Push the `.github/workflows/` directory to your repository
2. Go to **Actions** tab in your repo
3. Enable workflows if prompted

### Step 3: Test with a PR

1. Create a new branch: `git checkout -b test-pr`
2. Make a code change (e.g., modify a Python file)
3. Push and create a PR
4. Watch the Actions tab for the workflow run
5. Check the PR comments for the review

---

## Workflow Details

### Basic Code Review Agent

**File:** `.github/workflows/code-review-agent.yml`

**Triggers:**
- Pull request opened/synchronized
- Manual trigger (workflow_dispatch)

**What it does:**
```
1. Checkout PR code
2. Install dependencies (chromadb, openai, requests)
3. Get list of changed files
4. Run review_pr.py script
5. Post review comment to PR
6. Upload artifacts (reports, JSON data)
```

**Output:**
- Review comment on PR with:
  - Impact analysis
  - Test suggestions table
  - Changed files summary

### Smart RAG Review

**File:** `.github/workflows/smart-rag-review.yml`

**Triggers:**
- Pull request opened/synchronized/reopened
- Manual trigger with base_ref input

**What it does:**
```
1. Checkout with full git history
2. Run smart_review.py (RAG-enabled analysis)
3. Find related files across codebase
4. Detect API route changes
5. Run check_test_coverage.py
6. Post/update review comments
7. Upload all artifacts
```

**Output:**
- Smart review comment with:
  - Context-aware analysis
  - Related file mappings
  - Priority-based suggestions
  - Security & performance flags

---

## How It Works

### 1. Diff Analysis

```python
# Extract from git diff
files = [
    {"path": "src/auth/login.py", "functions": ["authenticate", "login"]},
    {"path": "src/api/users.py", "functions": ["get_user"]}
]
```

### 2. Context Retrieval (RAG)

```python
# Scan codebase for relationships
for file in all_codebase_files:
    if imports_changed_module(file):
        related_files.append(file)
    if calls_changed_function(file):
        impacted_apis.append(file)
```

### 3. Impact Analysis

```python
risk_checks = {
    "security": ["auth", "login", "password", "token"],
    "api": ["route", "endpoint", "api"],
    "payment": ["stripe", "charge", "payment"]
}
```

### 4. Suggestion Generation

```python
suggestions = []

for func in changed_functions:
    if not has_test(func):
        suggestions.append({
            "type": "test_coverage",
            "priority": "HIGH",
            "message": f"Add test for {func}()"
        })
```

### 5. Report Generation

Markdown report created with:
- Tables for readability
- Emojis for quick scanning
- Checklists for action items
- Links to related files

---

## Customization

### Adding Custom Rules

Edit `.github/scripts/review_pr.py`:

```python
def analyze_impact(files):
    # Add your custom checks
    if "database" in filepath:
        analysis["database_changes"].append(filepath)
        
    # Check for specific patterns
    if re.search(r'RAW_QUERY|execute\(', content):
        analysis["sql_injection_risk"] = True
```

### Changing Risk Levels

Modify the risk detection logic:

```python
# In review_pr.py or smart_review.py
risk_keywords = {
    "critical": ["password", "secret", "token", "api_key"],
    "high": ["payment", "stripe", "billing"],
    "medium": ["api", "endpoint", "route"],
    "low": ["docs", "comments", "readme"]
}
```

### Custom Output Format

Modify the report templates in the scripts:

```python
def create_review_report(...):
    # Add custom sections
    report += "### Your Custom Section\n\n"
    report += custom_analysis_results
```

### Integration with Other Tools

Add steps to the workflow:

```yaml
- name: Run linter
  run: pylint src/

- name: Run type checker
  run: mypy src/

- name: Run security scanner
  run: bandit -r src/
```

---

## Troubleshooting

### Issue: Workflow not triggering

**Check:**
- File is in `.github/workflows/` (exact path)
- YAML syntax is valid
- Workflow is enabled in repo settings
- You're opening a PR (not just pushing)

### Issue: "Permission denied" on scripts

**Fix:**
```bash
chmod +x .github/scripts/*.py
```

Or add to workflow:
```yaml
- name: Make scripts executable
  run: chmod +x .github/scripts/*.py
```

### Issue: OpenAI API errors

**Check:**
- `OPENAI_API_KEY` secret is set correctly
- API key has credits available
- Key has access to required models

### Issue: Empty review comments

**Debug:**
```yaml
- name: Debug
  run: |
    cat review_report.md
    ls -la *.json
```

### Issue: Comment not posting

**Check:**
- `GITHUB_TOKEN` has permissions
- PR number is correct
- No rate limiting

---

## Security Considerations

### 🔒 Secrets Management

- Never commit API keys to the repo
- Use GitHub Secrets for all sensitive data
- Rotate keys regularly
- Use least-privilege API keys

### 🛡️ Code Safety

- Workflows run in isolated environments
- Scripts don't execute arbitrary code
- No external network calls except to GitHub/OpenAI

### ⚠️ Rate Limits

Be aware of:
- GitHub API rate limits (5000 requests/hour)
- OpenAI API rate limits
- Action runner minutes (2000 min/month for free)

### 📝 Audit Trail

All reviews are:
- Posted as PR comments (visible history)
- Saved as artifacts (downloadable)
- Logged in Actions tab

---

## Real-World Deployment Tips

### 1. Gradual Rollout

Start with:
```yaml
on:
  pull_request:
    paths:
      - 'src/auth/**'  # Only auth changes first
```

Then expand to more paths.

### 2. Required Checks

Make review passing required:
1. Go to **Settings → Branches**
2. Add rule for `main`
3. Require status checks to pass
4. Select your workflow

### 3. Notifications

Add Slack notifications for high-risk PRs:

```yaml
- name: Notify Slack
  if: contains(steps.review.outputs.risk, 'high')
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {"text": "High-risk PR detected: ${{ github.event.pull_request.html_url }}"}
```

### 4. Metrics

Track effectiveness:
- Number of issues caught
- Time saved in reviews
- Test coverage improvement

---

## Example PR Workflow

```bash
# Developer creates PR
git checkout -b feature/new-auth
git commit -m "Add OAuth support"
git push origin feature/new-auth
# Create PR on GitHub

# Workflow triggers automatically
# 1. Analyzes changes to auth files
# 2. Finds related: middleware.py, test_auth.py
# 3. Detects: Security-sensitive changes
# 4. Suggests: OAuth flow tests, token validation
# 5. Posts: Detailed review comment

# Developer sees comment and:
# - Adds missing tests
# - Updates documentation
# - Requests security review

# Reviewer sees:
# - AI-generated context
# - Related file mappings
# - Risk assessment
# - Test coverage status
```

---

## Next Steps

1. ✅ Set up secrets
2. ✅ Push workflows
3. ✅ Test with a PR
4. ✅ Customize rules for your codebase
5. ✅ Train your team on the workflow
6. 📊 Measure impact over time

---

**Questions?** Check the script comments or modify the workflows for your needs!
