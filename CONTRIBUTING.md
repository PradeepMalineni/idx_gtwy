# Contributing to Gateway Governance Agent

Thank you for your interest in contributing! This document provides guidelines and standards for contributing to the Gateway Governance Agent.

---

## 🎯 Core Principles

Before contributing, please understand and adhere to these core principles:

### 1. **LLM for Inference Only**

✅ **ALLOWED:**
- Using LLM to detect PCI/sensitive data
- Using LLM to parse/analyze API specifications
- Using LLM to extract information from documentation

❌ **NOT ALLOWED:**
- Using LLM to make gateway selection decisions
- Using LLM to override policy rules
- Using LLM in the policy engine

### 2. **Policy Rules Must Be Static**

All gateway selection decisions must be based on:
- ✅ Static, auditable rules in YAML
- ✅ Explicit condition matching
- ✅ Traceable decision paths

NOT based on:
- ❌ LLM recommendations
- ❌ Dynamic/learned patterns
- ❌ Non-deterministic logic

### 3. **Complete Auditability**

Every decision must be:
- ✅ Logged with full context
- ✅ Traceable to a specific rule
- ✅ Timestamped
- ✅ Immutable once logged

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- An OpenAI or Anthropic API key
- Familiarity with async Python
- Understanding of MCP (Model Context Protocol)

### Development Setup

1. **Fork and clone:**

```bash
git clone https://github.com/yourname/IDX_MCP.git
cd IDX_MCP
```

2. **Run setup:**

```bash
./setup.sh
source venv/bin/activate
```

3. **Install dev dependencies:**

```bash
pip install pytest pytest-asyncio black mypy
```

4. **Run tests:**

```bash
python test_agent.py
```

---

## 📝 Contribution Guidelines

### Code Style

- **Python:** Follow PEP 8
- **Formatting:** Use `black` with default settings
- **Type Hints:** Use type annotations for all functions
- **Docstrings:** Use Google-style docstrings

```python
def example_function(param: str, optional: Optional[int] = None) -> Dict[str, Any]:
    """
    Brief description of function.
    
    Args:
        param: Description of param
        optional: Description of optional parameter
        
    Returns:
        Dictionary containing results
        
    Raises:
        ValueError: When param is invalid
    """
    pass
```

### Commit Messages

Use conventional commits:

```
feat: Add support for AWS API Gateway
fix: Correct PCI field detection for track data
docs: Update architecture documentation
test: Add tests for policy engine
refactor: Simplify OAS parser logic
```

### Branch Naming

```
feature/aws-gateway-support
fix/pci-detection-bug
docs/update-readme
test/add-integration-tests
```

---

## 🧪 Testing Requirements

All contributions must include tests:

### Unit Tests

```python
# tests/test_new_feature.py
import pytest
from modules.new_module import NewClass

def test_new_functionality():
    """Test that new feature works correctly"""
    obj = NewClass()
    result = obj.new_method()
    assert result == expected_value
```

### Integration Tests

```python
async def test_end_to_end_flow():
    """Test complete workflow with new feature"""
    agent = GatewayGovernanceAgent()
    result = await agent.process_request(test_dir)
    assert result["status"] == "success"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific test
pytest tests/test_policy_engine.py -v
```

---

## 🎨 Adding New Features

### Adding a New Gateway

1. **Update policy configuration:**

```yaml
# config/gateway-policy.yaml
gateways:
  aws_apigateway:
    name: "AWS API Gateway"
    description: "Serverless API gateway"
    capabilities:
      - "Lambda integration"
      - "Cognito authentication"
```

2. **Add routing rules:**

```yaml
rules:
  - id: rule_aws_001
    name: "Serverless APIs - AWS"
    priority: 15
    conditions:
      api_type: serverless
      cloud_provider: aws
    action: route
    gateway: aws_apigateway
    reason: "Serverless API on AWS → API Gateway"
```

3. **Update deployment manager:**

```python
# modules/deployment.py
SUPPORTED_GATEWAYS = ["apigee", "datapower", "aws_apigateway"]

async def _deploy_to_aws_apigateway(self, ...):
    # Implementation
    pass
```

4. **Add tests:**

```python
async def test_aws_gateway_selection():
    # Test implementation
    pass
```

5. **Update documentation:**
- Update README.md
- Add example in examples/
- Update ARCHITECTURE.md

### Adding a New LLM Provider

1. **Add provider to PCI detector:**

```python
# modules/pci_detector.py
async def _call_custom_llm(self, prompt: str) -> Dict[str, Any]:
    """
    Call custom LLM provider
    
    Args:
        prompt: Detection prompt
        
    Returns:
        Analysis results
    """
    # Implementation
    pass
```

2. **Update constructor:**

```python
def __init__(self, llm_provider: str = "openai"):
    self.llm_provider = llm_provider
    # Add custom provider check
```

3. **Add environment variable:**

```python
def _check_llm_availability(self) -> bool:
    if self.llm_provider == "custom":
        return bool(os.getenv("CUSTOM_LLM_API_KEY"))
```

4. **Add tests and docs**

### Adding New Policy Conditions

1. **Define condition in policy:**

```yaml
conditions:
  api_exposure: external
  has_pci: true
  compliance_level: high  # New condition
```

2. **Update policy engine matching:**

```python
# modules/policy_engine.py
def _matches_conditions(self, input_data, conditions):
    # Handle new condition type
    if "compliance_level" in conditions:
        # Custom logic
        pass
    return super()._matches_conditions(input_data, conditions)
```

3. **Update agent to collect new data**

4. **Add tests and docs**

---

## 🔒 Security Considerations

### When Contributing, Ensure:

1. **No Secrets in Code**
   - Use environment variables
   - Never commit API keys
   - Use `.env.example` for templates

2. **Validate User Input**
   - Sanitize file paths
   - Validate session IDs
   - Check for path traversal

3. **Maintain LLM Boundary**
   - LLM results go to context
   - Policy engine uses context
   - No LLM calls in policy engine

4. **Audit Everything**
   - Log all decisions
   - Include sufficient context
   - Don't log sensitive data

---

## 📋 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No linter errors
- [ ] Security guidelines followed

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe tests added/updated

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] LLM boundary maintained
- [ ] Audit logging added
- [ ] Security reviewed

## Related Issues
Fixes #123
```

### Review Process

1. Submit PR with clear description
2. Automated tests run
3. Code review by maintainers
4. Address feedback
5. Merge when approved

---

## 🐛 Bug Reports

### Template

```markdown
**Bug Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Create OAS file with...
2. Run select_gateway...
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: macOS 14.0
- Python: 3.11.5
- MCP Server version: 1.0.0
- LLM Provider: OpenAI

**Logs**
```
Include relevant logs
```

**Additional Context**
Any other relevant information
```

---

## 💡 Feature Requests

### Template

```markdown
**Feature Description**
Clear description of proposed feature

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this work?

**Alternatives Considered**
Other approaches considered

**Impact on Core Principles**
Does this maintain:
- LLM for inference only? Yes/No
- Static policy rules? Yes/No
- Complete auditability? Yes/No

**Additional Context**
Any other relevant information
```

---

## 📚 Documentation Standards

### Code Documentation

- **Every module** needs a module-level docstring
- **Every class** needs a class-level docstring
- **Every public function** needs a docstring with Args, Returns, Raises
- **Complex logic** needs inline comments

### User Documentation

When adding features, update:
- `README.md` - Main documentation
- `docs/QUICKSTART.md` - Quick start guide
- `docs/ARCHITECTURE.md` - Architecture details
- `docs/IDE_CONFIGURATION.md` - IDE setup (if relevant)

### Example Documentation

Add examples in `examples/` directory:
- Sample OAS files
- Configuration examples
- Policy rule examples

---

## 🎓 Learning Resources

### Understanding the Codebase

1. **Start with:** `docs/QUICKSTART.md`
2. **Then read:** `docs/ARCHITECTURE.md`
3. **Study code:** Start with `server.py`, then modules
4. **Run tests:** `python test_agent.py`

### Key Concepts

- **MCP Protocol:** https://modelcontextprotocol.io
- **OpenAPI Spec:** https://swagger.io/specification/
- **PCI DSS:** https://www.pcisecuritystandards.org/
- **Async Python:** https://docs.python.org/3/library/asyncio.html

---

## 🙏 Code of Conduct

### Our Standards

- ✅ Be respectful and inclusive
- ✅ Welcome newcomers
- ✅ Accept constructive criticism
- ✅ Focus on what's best for the community
- ✅ Show empathy

### Unacceptable Behavior

- ❌ Harassment or discrimination
- ❌ Trolling or insulting comments
- ❌ Personal or political attacks
- ❌ Publishing others' private information

### Enforcement

Violations will result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report issues to: ESGADEV@team.com

---

## 📞 Getting Help

### Questions?

- **GitHub Issues:** For bugs and features
- **Discussions:** For questions and ideas
- **Email:** ESGADEV@team.com

### Mentorship

New contributors can request mentorship:
- Code review guidance
- Architecture questions
- Best practices

---

## 🎖️ Recognition

Contributors are recognized in:
- `CONTRIBUTORS.md` file
- Release notes
- Project README

Thank you for contributing to Gateway Governance! 🚀

