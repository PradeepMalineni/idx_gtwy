# Installation Guide

Quick installation guide for the Gateway Governance Agent.

---

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Operating System**: macOS, Linux, or Windows WSL
- **API Key**: OpenAI or Anthropic (for PCI detection)
- **IDE**: Any MCP-compatible IDE (VS Code, IntelliJ, Cursor, etc.)

---

## 🚀 Installation Steps

### Method 1: Automated Setup (Recommended)

```bash
# 1. Navigate to project directory
cd /Users/pradeepm/ProjX/IDX_MCP

# 2. Run setup script
./setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Set API key (choose one)
export OPENAI_API_KEY='sk-your-openai-key-here'
# OR
export ANTHROPIC_API_KEY='sk-ant-your-anthropic-key-here'

# 5. Test installation
python test_agent.py
```

### Method 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create directories
mkdir -p ~/.gateway-governance/audit-logs

# 4. Set API key
export OPENAI_API_KEY='sk-your-key'

# 5. Test installation
python test_agent.py
```

---

## 🔑 API Key Setup

### OpenAI

1. Get API key from: https://platform.openai.com/api-keys
2. Set environment variable:

```bash
# Temporary (current session)
export OPENAI_API_KEY='sk-your-key'

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.zshrc
source ~/.zshrc
```

### Anthropic

1. Get API key from: https://console.anthropic.com/
2. Set environment variable:

```bash
# Temporary
export ANTHROPIC_API_KEY='sk-ant-your-key'

# Permanent
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key"' >> ~/.zshrc
source ~/.zshrc
```

---

## 🧪 Verify Installation

### Test 1: Run Test Suite

```bash
source venv/bin/activate
python test_agent.py
```

Expected output:
```
🧪 Gateway Governance Agent - Test Suite
=========================================

TEST 1: Pet Store API (Non-PCI)
============================================================
✅ Gateway Selected: APIGEE
...

✅ All tests completed!
```

### Test 2: Check Dependencies

```bash
pip list | grep -E "mcp|openai|anthropic|PyYAML"
```

Expected:
```
mcp                    0.9.0
openai                 1.0.0
anthropic              0.39.0
PyYAML                 6.0
```

### Test 3: Validate Policy

```python
from modules.policy_engine import PolicyEngine

engine = PolicyEngine()
validation = engine.validate_policy()
print(f"Valid: {validation['valid']}")
print(f"Rules: {validation['rules_count']}")
```

Expected:
```
Valid: True
Rules: 7
```

---

## 🎯 IDE Configuration

### VS Code

1. Install MCP extension (if not already installed)

2. Add to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "gateway-governance": {
      "command": "python",
      "args": ["/Users/pradeepm/ProjX/IDX_MCP/server.py"],
      "env": {
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
      }
    }
  }
}
```

3. Restart VS Code

4. Verify: Open Command Palette → "MCP: List Servers" → Should see "gateway-governance"

### Cursor

1. Create `.cursor/mcp-config.json`:

```json
{
  "servers": {
    "gateway-governance": {
      "command": "python",
      "args": ["/Users/pradeepm/ProjX/IDX_MCP/server.py"],
      "env": {
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
      }
    }
  }
}
```

2. Restart Cursor

3. In chat: `@gateway-governance` should autocomplete

### IntelliJ / PyCharm

1. Settings → Plugins → Install "MCP"
2. Settings → Tools → MCP Servers → Add
   - Name: `Gateway Governance`
   - Command: `python`
   - Args: `/Users/pradeepm/ProjX/IDX_MCP/server.py`
   - Env: `OPENAI_API_KEY=your-key`
3. Restart IntelliJ

---

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'mcp'"

**Solution:**
```bash
source venv/bin/activate  # Make sure venv is activated
pip install -r requirements.txt
```

### Issue: "ImportError: No module named 'yaml'"

**Solution:**
```bash
pip install PyYAML
```

### Issue: "OpenAI API key not found"

**Solution:**
```bash
# Check if set
echo $OPENAI_API_KEY

# Set it
export OPENAI_API_KEY='sk-your-key'

# Verify
python -c "import os; print('Key set' if os.getenv('OPENAI_API_KEY') else 'Not set')"
```

### Issue: "Permission denied: ./setup.sh"

**Solution:**
```bash
chmod +x setup.sh
./setup.sh
```

### Issue: "MCP server not connecting in IDE"

**Solutions:**

1. Check server runs standalone:
   ```bash
   python server.py
   # Should not error
   ```

2. Check IDE MCP configuration syntax

3. Check environment variables are accessible to IDE

4. Restart IDE completely

---

## 📦 Deployment Configuration (Optional)

If you want to enable actual deployments (not just stubs):

### GitHub Actions

1. Create `~/.gateway-governance/deployment-config.json`:

```json
{
  "apigee": {
    "method": "github_actions",
    "workflow": ".github/workflows/deploy-apigee.yml",
    "enabled": true
  }
}
```

2. Install GitHub CLI:
```bash
brew install gh  # macOS
# or
apt install gh   # Linux
```

3. Authenticate:
```bash
gh auth login
```

### Harness

```json
{
  "datapower": {
    "method": "harness",
    "pipeline": "datapower-deployment",
    "enabled": true
  }
}
```

---

## 🎓 Next Steps

1. ✅ Installation complete
2. 📖 Read `docs/QUICKSTART.md` for first usage
3. 🎯 Configure your IDE (see above)
4. 🔧 Customize `config/gateway-policy.yaml` for your org
5. 🚀 Start using the agent!

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.11+ |
| RAM | 512 MB | 1 GB |
| Disk | 100 MB | 500 MB |
| Network | Required for LLM | Required |

---

## 🆘 Getting Help

- **Documentation**: See `README.md` and `docs/`
- **Issues**: Create GitHub issue
- **Email**: ESGADEV@team.com

---

**Installation Complete!** 🎉

Run `python test_agent.py` to verify everything works.

