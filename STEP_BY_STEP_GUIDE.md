# 🎯 Step-by-Step Guide: Gateway Governance Agent

Complete walkthrough from installation to your first gateway selection.

---

## ✅ Step 1: Initial Setup

### 1.1 Navigate to Project Directory

```bash
cd /Users/pradeepm/ProjX/IDX_MCP
```

### 1.2 Run Setup Script

```bash
./setup.sh
```

**What this does:**
- Checks Python version (needs 3.10+)
- Creates virtual environment in `venv/`
- Installs all dependencies from `requirements.txt`
- Creates audit log directory at `~/.gateway-governance/audit-logs`

**Expected output:**
```
🚀 Gateway Governance Agent - Setup
====================================
✅ Found Python 3.11
✅ Virtual environment created
📦 Installing dependencies...
✅ Setup complete!
```

### 1.3 Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

---

## 🔑 Step 2: Configure API Key

Choose **ONE** provider for PCI detection:

### Option A: OpenAI (Recommended)

1. Get API key from: https://platform.openai.com/api-keys

2. Set environment variable:
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

3. Verify:
```bash
echo $OPENAI_API_KEY
```

### Option B: Anthropic

1. Get API key from: https://console.anthropic.com/

2. Set environment variable:
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

3. Verify:
```bash
echo $ANTHROPIC_API_KEY
```

### Make it Permanent (Optional)

Add to your shell config file:

```bash
# For zsh (macOS default)
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🧪 Step 3: Test the Installation

### 3.1 Run Test Suite

```bash
python test_agent.py
```

**What this tests:**
1. Non-PCI API (Pet Store) → Should select **Apigee**
2. PCI API (Payment) → Should select **DataPower**
3. Pre-configured gateway → Should use existing config
4. Audit logs → Should show recent decisions

**Expected output:**
```
🧪 Gateway Governance Agent - Test Suite
=========================================

TEST 1: Pet Store API (Non-PCI)
============================================================
📊 Result:
Status: needs_input

❓ Questions needed:
  - Is this API exposed externally or used internally only?
    Options: ['external', 'internal']
  - What type of authentication is used for this API?
    Options: ['oauth', 'mtls', 'both', 'none']

✍️  Providing answers...

✅ Gateway Selected: APIGEE
📝 Reason: External API without PCI data with OAuth → Apigee (modern cloud gateway)
🔖 Rule: rule_004

TEST 2: Payment API (PCI Data)
============================================================
🔍 PCI Analysis:
  PCI Detected: True
  PCI Fields: ['cardNumber', 'cvv', 'expiryDate', 'cardholderName']

✅ Gateway Selected: DATAPOWER
📝 Reason: External API with PCI data and strong authentication → DataPower (PCI DSS compliant gateway)
🔖 Rule: rule_002

✅ All tests completed!
```

### 3.2 If Tests Fail

**Problem:** `ModuleNotFoundError: No module named 'mcp'`

**Solution:**
```bash
pip install -r requirements.txt
```

**Problem:** `OpenAI API key not found`

**Solution:**
```bash
export OPENAI_API_KEY='sk-your-key'
python test_agent.py
```

---

## 📝 Step 4: Try Your First Real Example

### 4.1 Create a Test Project

```bash
mkdir -p /tmp/my-first-api
cd /tmp/my-first-api
```

### 4.2 Create a Simple OpenAPI Spec

Create file `openapi.yaml`:

```yaml
openapi: 3.0.0
info:
  title: Customer API
  version: 1.0.0
  description: API for managing customer data

paths:
  /customers:
    get:
      summary: List customers
      responses:
        '200':
          description: List of customers
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Customer'
    
    post:
      summary: Create customer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Customer'
      responses:
        '201':
          description: Customer created

components:
  schemas:
    Customer:
      type: object
      required:
        - name
        - email
      properties:
        id:
          type: integer
          description: Customer ID
        name:
          type: string
          description: Customer name
        email:
          type: string
          format: email
          description: Customer email
        phone:
          type: string
          description: Phone number
        address:
          type: string
          description: Mailing address

  securitySchemes:
    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth/authorize
          tokenUrl: https://auth.example.com/oauth/token
          scopes:
            read:customers: Read customer data
            write:customers: Create/update customers

security:
  - OAuth2: [read:customers]
```

Save this file as `/tmp/my-first-api/openapi.yaml`

### 4.3 Run Gateway Selection

Create a Python script to test:

```bash
cd /Users/pradeepm/ProjX/IDX_MCP
```

Create file `my_test.py`:

```python
#!/usr/bin/env python3
import asyncio
from server import GatewayGovernanceAgent

async def main():
    # Initialize agent
    agent = GatewayGovernanceAgent()
    
    # Run gateway selection for your API
    print("🔍 Analyzing your API...")
    result = await agent.process_request("/tmp/my-first-api")
    
    print(f"\n📊 Result: {result.get('status')}")
    
    # If questions are needed, answer them
    if result.get('status') == 'needs_input':
        print("\n❓ Agent needs more information:")
        
        for q in result.get('questions', []):
            print(f"\nQuestion: {q['question']}")
            print(f"Options: {q['options']}")
        
        # Provide answers
        print("\n✍️  Providing answers...")
        answers = {
            "api_exposure": "internal",  # This is an internal API
            "auth_type": "oauth"         # Uses OAuth authentication
        }
        
        result = await agent.answer_questions(result['session_id'], answers)
    
    # Display final decision
    print("\n" + "="*60)
    print("🎯 FINAL DECISION")
    print("="*60)
    print(f"✅ Gateway: {result.get('gateway', 'N/A').upper()}")
    print(f"📝 Reason: {result.get('reason', 'N/A')}")
    print(f"🔖 Rule ID: {result.get('rule_id', 'N/A')}")
    print(f"📋 Rule Name: {result.get('rule_name', 'N/A')}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.4 Run Your Test

```bash
python my_test.py
```

**Expected Output:**

```
🔍 Analyzing your API...

📊 Result: needs_input

❓ Agent needs more information:

Question: Is this API exposed externally or used internally only?
Options: ['external', 'internal']

Question: What type of authentication is used for this API?
Options: ['oauth', 'mtls', 'both', 'none']

✍️  Providing answers...

============================================================
🎯 FINAL DECISION
============================================================
✅ Gateway: APIGEE
📝 Reason: Internal API without PCI data → Apigee (lightweight option)
🔖 Rule ID: rule_006
📋 Rule Name: Internal non-PCI - Apigee
============================================================
```

### 4.5 Understanding the Decision

**What happened:**
1. ✅ Agent found `openapi.yaml` in `/tmp/my-first-api/`
2. 🔍 Analyzed fields: `id`, `name`, `email`, `phone`, `address`
3. ✅ **No PCI data detected** (no card numbers, CVV, etc.)
4. ❓ Asked for context (internal/external, auth type)
5. 📊 Applied policy rule #6: Internal + No PCI = **Apigee**
6. 📝 Logged decision to audit log

---

## 💳 Step 5: Try a PCI Example

### 5.1 Create Payment API

```bash
mkdir -p /tmp/payment-api
cp /Users/pradeepm/ProjX/IDX_MCP/examples/payment-api.yaml /tmp/payment-api/openapi.yaml
```

### 5.2 Analyze Payment API

Modify `my_test.py` to use `/tmp/payment-api`:

```python
result = await agent.process_request("/tmp/payment-api")
```

Then run:

```bash
python my_test.py
```

**Expected Output:**

```
🔍 Analyzing your API...

📊 Result: needs_input

🔍 Current Analysis:
  PCI Detected: True
  PCI Fields: ['cardNumber', 'cvv', 'expiryDate', 'cardholderName']

❓ Agent needs more information:
...

✍️  Providing answers...
  api_exposure: external
  auth_type: both  (OAuth + mTLS)

============================================================
🎯 FINAL DECISION
============================================================
✅ Gateway: DATAPOWER
📝 Reason: External API with PCI data and strong authentication → DataPower (PCI DSS compliant gateway)
🔖 Rule ID: rule_002
============================================================
```

**Why DataPower?**
- 🚨 PCI data detected (card fields)
- 🌐 External facing API
- 🔒 Strong authentication (OAuth + mTLS)
- ✅ Rule #2 matched: Requires PCI-compliant gateway

---

## 🚨 Step 6: See Security Escalation

### 6.1 Test Dangerous Pattern

Modify answers to simulate insecure setup:

```python
answers = {
    "api_exposure": "external",  # External API
    "auth_type": "none"          # No authentication! 🚨
}
```

### 6.2 Run Again

```bash
python my_test.py
```

**Expected Output:**

```
============================================================
🎯 FINAL DECISION
============================================================
🚨 STATUS: ESCALATION REQUIRED
📧 Contact: ESGADEV@team.com
📝 Reason: External API with PCI data but no authentication - security escalation required
🔖 Rule ID: rule_001
⚠️  Message: 🚨 Security Escalation Required: External API with PCI data but no authentication
Please contact ESGADEV@team.com
🚫 DEPLOYMENT: BLOCKED
============================================================
```

**What happened:**
- 🚨 Dangerous pattern detected: External + PCI + No Auth
- 🔝 Escalated to security team
- 🚫 Deployment blocked
- 📝 Logged as "escalation" status

This is the **security guardrail** in action!

---

## 📊 Step 7: View Audit Logs

### 7.1 Check Audit Logs

```python
# Add to my_test.py
from modules.audit_logger import AuditLogger

async def view_logs():
    logger = AuditLogger()
    logs = await logger.get_recent_logs(limit=5)
    
    print("\n📋 Recent Decisions:")
    print("="*60)
    
    for i, log in enumerate(logs, 1):
        print(f"\n{i}. {log['timestamp']}")
        print(f"   Project: {log['project_dir']}")
        decision = log.get('decision', {})
        print(f"   Gateway: {decision.get('gateway', 'N/A')}")
        print(f"   Status: {decision.get('status')}")
        print(f"   Rule: {decision.get('rule_id')}")
        context = log.get('context', {})
        print(f"   PCI: {context.get('pci_detected')}")

# Add to main()
await view_logs()
```

### 7.2 Run to See History

```bash
python my_test.py
```

**Output:**
```
📋 Recent Decisions:
============================================================

1. 2025-11-02T10:45:23Z
   Project: /tmp/payment-api
   Gateway: N/A
   Status: escalation
   Rule: rule_001
   PCI: True

2. 2025-11-02T10:42:15Z
   Project: /tmp/payment-api
   Gateway: datapower
   Status: success
   Rule: rule_002
   PCI: True

3. 2025-11-02T10:40:05Z
   Project: /tmp/my-first-api
   Gateway: apigee
   Status: success
   Rule: rule_006
   PCI: False
```

### 7.3 Export Audit Logs

```python
from modules.audit_logger import AuditLogger

logger = AuditLogger()
logger.export_logs("/tmp/audit-export.csv", format="csv")
print("✅ Exported to /tmp/audit-export.csv")
```

Open in Excel/Numbers for analysis!

---

## 🎯 Step 8: Configure Your IDE

### For VS Code

1. **Install MCP Extension** (if not already installed)
   - Open Extensions (Cmd+Shift+X)
   - Search for "MCP"
   - Install

2. **Create Configuration**

Create `.vscode/settings.json` in your project:

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

3. **Restart VS Code**

4. **Use the Agent**

- Open Command Palette (Cmd+Shift+P)
- Type "MCP"
- Select "MCP: Call Tool"
- Choose `gateway-governance`
- Select `select_gateway`
- Provide project path

### For Cursor

1. **Create Config**

Create `.cursor/mcp-config.json`:

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

2. **Restart Cursor**

3. **Use in Chat**

Simply type in Cursor chat:
```
@gateway-governance Select and deploy to appropriate gateway for my API in /tmp/my-first-api
```

---

## 🎨 Step 9: Customize Policies

### 9.1 Open Policy File

```bash
code /Users/pradeepm/ProjX/IDX_MCP/config/gateway-policy.yaml
```

### 9.2 Add Custom Rule

Add after existing rules:

```yaml
  - id: rule_custom_001
    name: "High-Priority APIs - DataPower"
    priority: 10
    conditions:
      api_exposure: external
      has_pci: false
      # Add custom condition (requires extending code)
    action: route
    gateway: datapower
    reason: "High-priority external API → DataPower for reliability"
```

### 9.3 Validate Policy

```python
from modules.policy_engine import PolicyEngine

engine = PolicyEngine()
validation = engine.validate_policy()

print(f"✅ Valid: {validation['valid']}")
print(f"📊 Rules: {validation['rules_count']}")
print(f"⚠️  Warnings: {validation['warnings']}")
print(f"❌ Errors: {validation['errors']}")
```

---

## 🚀 Step 10: Run as MCP Server

### 10.1 Start Server

```bash
cd /Users/pradeepm/ProjX/IDX_MCP
source venv/bin/activate
export OPENAI_API_KEY='your-key'
python server.py
```

**Expected:**
```
INFO:__main__:Starting Gateway Governance Agent MCP Server...
```

The server is now running and waiting for MCP client connections.

### 10.2 Connect from IDE

Your IDE's MCP client will connect via stdio protocol and can call these tools:

1. `select_gateway` - Analyze and select gateway
2. `answer_questions` - Provide contextual answers
3. `view_audit_log` - View decision history
4. `deploy_to_gateway` - Trigger deployment

---

## 📚 Next Steps

### Learn More

1. **Read Full Docs**
   - `README.md` - Complete documentation
   - `docs/ARCHITECTURE.md` - How it works internally
   - `docs/IDE_CONFIGURATION.md` - IDE setup details

2. **Customize**
   - Edit `config/gateway-policy.yaml` for your rules
   - Add more examples in `examples/`
   - Extend modules for custom logic

3. **Deploy**
   - Set up GitHub Actions workflow
   - Configure Harness pipeline
   - Enable real deployments

### Common Use Cases

**Use Case 1: Pre-configure Production APIs**
```json
// Create gateway-selection.json in your API repo
{
  "gateway": "datapower",
  "reason": "Production payment API - PCI compliance required"
}
```

**Use Case 2: Batch Analysis**
```python
# Analyze multiple APIs
apis = ["/path/api1", "/path/api2", "/path/api3"]
for api_path in apis:
    result = await agent.process_request(api_path)
    print(f"{api_path}: {result['gateway']}")
```

**Use Case 3: CI/CD Integration**
```yaml
# .github/workflows/gateway-check.yml
- name: Check Gateway
  run: |
    python -c "
    import asyncio
    from server import GatewayGovernanceAgent
    async def check():
        agent = GatewayGovernanceAgent()
        result = await agent.process_request('.')
        assert result['status'] == 'success'
    asyncio.run(check())
    "
```

---

## 🆘 Troubleshooting

### Issue: "No OpenAPI spec found"

**Check:**
```bash
ls -la /tmp/my-first-api/
# Should see openapi.yaml
```

**Solution:** Ensure file is named `openapi.yaml`, `api.yaml`, or `swagger.yaml`

### Issue: "LLM detection failed"

**Check:**
```bash
echo $OPENAI_API_KEY
# Should show your key
```

**Solution:** Agent will fall back to pattern matching automatically

### Issue: "Session not found"

**Solution:** Use fresh session_id from `select_gateway` response

---

## ✅ Quick Reference

### Run Tests
```bash
python test_agent.py
```

### Start Server
```bash
python server.py
```

### View Audit Logs
```bash
cat ~/.gateway-governance/audit-logs/gateway-decisions.jsonl | tail -5 | jq
```

### Validate Policy
```bash
python -c "from modules.policy_engine import PolicyEngine; e=PolicyEngine(); print(e.validate_policy())"
```

---

**You're all set! 🎉**

Start using the Gateway Governance Agent to make smart gateway decisions for your APIs!

