# Quick Start Guide

Get up and running with the Gateway Governance Agent in 5 minutes!

---

## 🚀 Installation

### 1. Run Setup Script

```bash
cd /Users/pradeepm/ProjX/IDX_MCP
./setup.sh
```

This will:
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Check for API keys

### 2. Set API Key

Choose one:

**OpenAI:**
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

**Anthropic:**
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

Add to `~/.bashrc` or `~/.zshrc` to persist.

### 3. Test the Server

```bash
source venv/bin/activate
python test_agent.py
```

You should see test results for different API scenarios.

---

## 📝 Your First Gateway Selection

### Scenario 1: Simple Non-PCI API

1. **Create a test project:**

```bash
mkdir -p /tmp/my-api
cd /tmp/my-api
```

2. **Create a simple OpenAPI spec** (`openapi.yaml`):

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      summary: Get users
      responses:
        '200':
          description: List of users
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
```

3. **Run the agent:**

```python
from server import GatewayGovernanceAgent
import asyncio

async def main():
    agent = GatewayGovernanceAgent()
    result = await agent.process_request("/tmp/my-api")
    
    # Answer questions if needed
    if result.get('status') == 'needs_input':
        session_id = result['session_id']
        answers = {
            "api_exposure": "internal",
            "auth_type": "oauth"
        }
        result = await agent.answer_questions(session_id, answers)
    
    print(f"Gateway: {result['gateway']}")
    print(f"Reason: {result['reason']}")

asyncio.run(main())
```

**Expected output:**
```
Gateway: apigee
Reason: Internal API without PCI data → Apigee (lightweight option)
```

---

### Scenario 2: Payment API with PCI Data

1. **Use the payment example:**

```bash
mkdir -p /tmp/payment-api
cp examples/payment-api.yaml /tmp/payment-api/openapi.yaml
```

2. **Run the agent:**

```python
from server import GatewayGovernanceAgent
import asyncio

async def main():
    agent = GatewayGovernanceAgent()
    result = await agent.process_request("/tmp/payment-api")
    
    # The agent will detect PCI fields: cardNumber, cvv, expiryDate
    print(f"PCI Detected: {result.get('current_analysis', {}).get('pci_detected')}")
    print(f"PCI Fields: {result.get('current_analysis', {}).get('pci_fields')}")
    
    # Answer questions
    if result.get('status') == 'needs_input':
        session_id = result['session_id']
        answers = {
            "api_exposure": "external",
            "auth_type": "both"  # OAuth + mTLS
        }
        result = await agent.answer_questions(session_id, answers)
    
    print(f"Gateway: {result['gateway']}")
    print(f"Reason: {result['reason']}")

asyncio.run(main())
```

**Expected output:**
```
PCI Detected: True
PCI Fields: ['cardNumber', 'cvv', 'expiryDate', 'cardholderName']
Gateway: datapower
Reason: External API with PCI data and OAuth/mTLS → DataPower (PCI DSS compliant gateway)
```

---

### Scenario 3: Pre-configured Gateway

If you already know which gateway to use, create `gateway-selection.json`:

```json
{
  "gateway": "datapower",
  "reason": "Pre-configured for compliance requirements"
}
```

The agent will use this without analysis.

---

## 🎯 Using in Your IDE

### VS Code

1. Install MCP extension
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

3. Use command palette: "MCP: Select Gateway"

### Cursor

In chat, simply say:

```
@gateway-governance Select and deploy to appropriate gateway for my API
```

---

## 🔍 Common Commands

### View Audit Logs

```python
from modules.audit_logger import AuditLogger
import asyncio

async def view_logs():
    logger = AuditLogger()
    logs = await logger.get_recent_logs(limit=10)
    
    for log in logs:
        print(f"Project: {log['project_dir']}")
        print(f"Gateway: {log['decision']['gateway']}")
        print(f"Timestamp: {log['timestamp']}")
        print("---")

asyncio.run(view_logs())
```

### Validate Policy

```python
from modules.policy_engine import PolicyEngine

engine = PolicyEngine()
validation = engine.validate_policy()

print(f"Valid: {validation['valid']}")
print(f"Rules: {validation['rules_count']}")
print(f"Errors: {validation['errors']}")
```

### Test PCI Detection

```python
from modules.pci_detector import PCIDetector
import asyncio

async def test_pci():
    detector = PCIDetector()
    
    # Mock OAS with PCI fields
    oas_spec = {
        "openapi": "3.0.0",
        "components": {
            "schemas": {
                "Payment": {
                    "properties": {
                        "cardNumber": {"type": "string"},
                        "cvv": {"type": "string"},
                        "amount": {"type": "number"}
                    }
                }
            }
        }
    }
    
    result = await detector.analyze_oas_for_pci(oas_spec)
    print(f"PCI Detected: {result['has_pci']}")
    print(f"PCI Fields: {result['pci_fields']}")
    print(f"Confidence: {result['confidence']}")

asyncio.run(test_pci())
```

---

## 📊 Understanding the Decision Flow

```
┌─────────────────────────────────────┐
│  Developer: "Select gateway"        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Check gateway-selection.json       │
│  Found? → Use it ✅                 │
└──────────────┬──────────────────────┘
               │ Not found
               ▼
┌─────────────────────────────────────┐
│  Find OpenAPI Spec file             │
│  (.yaml, .yml, .json)               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Analyze for PCI data (LLM)         │
│  • cardNumber, cvv, etc.            │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Ask missing context                │
│  • External or Internal?            │
│  • Auth type?                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Apply Policy Rules (Static)        │
│  Match first rule by priority       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Decision: Apigee or DataPower      │
│  (or Escalate if security issue)    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Log to Audit                       │
│  Optional: Deploy                   │
└─────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### "No OpenAPI spec found"

- Ensure you have a file named `openapi.yaml`, `api.yaml`, or similar
- File must contain `openapi: 3.0.0` field
- Check file is in project root or `api/`, `specs/`, `docs/` subdirectories

### "LLM detection failed"

- Verify API key: `echo $OPENAI_API_KEY`
- Check internet connection
- Falls back to pattern-based detection automatically

### "No rules matched"

- Check `config/gateway-policy.yaml` exists
- Verify your answers match rule conditions
- Default rule should always match

### Import errors

- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

---

## 📚 Next Steps

1. **Customize Policy Rules**
   - Edit `config/gateway-policy.yaml`
   - Add organization-specific rules

2. **Configure Deployment**
   - Set up GitHub Actions workflow
   - Configure Harness pipeline
   - Test deployment flow

3. **Integrate with IDE**
   - Follow [IDE Configuration Guide](IDE_CONFIGURATION.md)
   - Set up keyboard shortcuts
   - Add to team workflow

4. **Review Audit Logs**
   - Monitor decisions
   - Export to CSV for reporting
   - Share with governance team

---

## 💡 Tips

- **Use pre-configured `gateway-selection.json`** for production APIs that shouldn't change
- **Run tests before deploying** to catch issues early
- **Review audit logs regularly** for compliance reporting
- **Customize policy rules** to match your organization's requirements
- **Set up IDE integration** for seamless developer experience

---

## 🆘 Need Help?

- Check [README.md](../README.md) for full documentation
- View [IDE Configuration](IDE_CONFIGURATION.md) for setup help
- Email: ESGADEV@team.com

Happy gateway governance! 🚀

