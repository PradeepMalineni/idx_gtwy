# Gateway Governance Agent 🚀

**Shift-Left API Gateway Selection & Deployment**

An intelligent MCP (Model Context Protocol) server that helps developers select and deploy APIs to the correct API Gateway (Apigee or DataPower) at development time using policy-driven decision-making.

---

## 🎯 Overview

The Gateway Governance Agent automates the process of selecting the appropriate API gateway based on:

- **PCI/Sensitive Data Detection** (using LLM inference)
- **API Exposure** (external vs internal)
- **Authentication Type** (OAuth, mTLS, both, or none)
- **Static Policy Rules** (auditable, not LLM-based)

### Key Features

✅ **Multi-IDE Support** - Works across VS Code, IntelliJ, Eclipse, and any IDE supporting MCP  
✅ **Policy-Driven Decisions** - Static, auditable rules (no LLM in decision logic)  
✅ **PCI Data Detection** - LLM-based inference to detect cardholder data  
✅ **Conversational Q&A** - Asks for missing context interactively  
✅ **Audit Logging** - Full traceability of all decisions  
✅ **Deployment Integration** - Stub support for GitHub Actions, Harness, GitLab CI  
✅ **Security First** - Escalation workflow for security violations  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    IDE (Any)                        │
│  ┌─────────────────────────────────────────────┐   │
│  │       MCP Client (Built into IDE)           │   │
│  └────────────────┬────────────────────────────┘   │
└───────────────────┼─────────────────────────────────┘
                    │ MCP Protocol
┌───────────────────▼─────────────────────────────────┐
│        Gateway Governance Agent (MCP Server)        │
│  ┌─────────────────────────────────────────────┐   │
│  │  Agent Orchestrator                         │   │
│  │  - Workflow coordination                    │   │
│  │  - Session management                       │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ OAS Parser   │  │ PCI Detector │  │ Policy   │  │
│  │              │  │ (LLM-based)  │  │ Engine   │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │ Audit Logger │  │ Context Mgr  │  │ Deploy   │  │
│  │              │  │              │  │ Manager  │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API Key or Anthropic API Key (for PCI detection)
- MCP-compatible IDE (e.g., VS Code with MCP extension)

### Installation

1. **Clone the repository**

```bash
cd /Users/pradeepm/ProjX/IDX_MCP
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up API keys** (choose one)

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# OR for Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

4. **Run the MCP server**

```bash
python server.py
```

The server will start and listen for MCP client connections via stdio.

### MCP Client Configuration

Add this to your IDE's MCP configuration (e.g., VS Code):

**`.vscode/mcp-settings.json`**:

```json
{
  "mcpServers": {
    "gateway-governance": {
      "command": "python",
      "args": ["/Users/pradeepm/ProjX/IDX_MCP/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

---

## 📖 Usage

### Basic Workflow

1. **Developer invokes the agent:**

   ```
   "Select and deploy to appropriate gateway for my API"
   ```

2. **Agent checks for existing configuration:**
   - Looks for `gateway-selection.json` in project directory
   - If found, uses pre-configured gateway

3. **If no config exists, agent:**
   - Finds OpenAPI Specification file (`.yaml`, `.yml`, `.json`)
   - Analyzes API for PCI/sensitive data using LLM
   - Asks developer for missing context:
     - Is API external or internal?
     - What authentication is used?

4. **Agent applies policy rules** (static, not LLM):
   - Evaluates conditions against rules in `config/gateway-policy.yaml`
   - Returns gateway decision with reason

5. **Optionally deploys** to selected gateway

---

## 🔧 MCP Tools

The agent exposes these tools via MCP:

### 1. `select_gateway`

Analyzes API and selects appropriate gateway.

**Input:**
```json
{
  "project_dir": "/path/to/your/api/project",
  "auto_deploy": false
}
```

**Output:**
```json
{
  "status": "success",
  "gateway": "datapower",
  "reason": "External API with PCI data and OAuth → DataPower (PCI DSS compliant gateway)",
  "rule_id": "rule_002",
  "session_id": "uuid-here",
  "message": "✅ Gateway Selected: DATAPOWER..."
}
```

### 2. `answer_questions`

Provide answers to contextual questions.

**Input:**
```json
{
  "session_id": "uuid-from-select-gateway",
  "answers": {
    "api_exposure": "external",
    "auth_type": "oauth"
  }
}
```

### 3. `view_audit_log`

View recent gateway selection decisions.

**Input:**
```json
{
  "limit": 10
}
```

### 4. `deploy_to_gateway`

Deploy API to selected gateway.

**Input:**
```json
{
  "gateway": "apigee",
  "project_dir": "/path/to/project"
}
```

### 5. `generate_and_deploy_proxy` ✨ NEW

Generate proxy bundle from seed template and deploy to dev environment.

**Input:**
```json
{
  "session_id": "uuid-from-select-gateway",
  "confirmed": false
}
```

**Output (Confirmation):**
```json
{
  "status": "confirmation_needed",
  "message": "Ready to generate APIGEE proxy bundle...",
  "next_steps": ["..."]
}
```

**Input (Confirmed):**
```json
{
  "session_id": "uuid",
  "confirmed": true
}
```

**Output (Success):**
```json
{
  "status": "success",
  "bundle_path": "/path/to/api.zip",
  "test_url": "https://org-dev.apigee.net/v1/api",
  "next_steps": ["..."]
}
```

---

## 📋 Policy Rules

Policy rules are defined in `config/gateway-policy.yaml`.

### Rule Priority

Rules are evaluated in priority order (lower number = higher priority). First matching rule wins.

### Example Rules

| Priority | Conditions | Gateway | Reason |
|----------|-----------|---------|--------|
| 1 | External + PCI + No Auth | **Escalate** | Security violation |
| 2 | External + PCI + OAuth/mTLS | **DataPower** | PCI compliance required |
| 3 | Internal + PCI | **DataPower** | PCI compliance required |
| 4 | External + No PCI + OAuth | **Apigee** | Modern cloud gateway |
| 5 | Internal + No PCI | **Apigee** | Lightweight option |
| 999 | Default | **Apigee** | Default fallback |

### Customizing Rules

Edit `config/gateway-policy.yaml` to add/modify rules:

```yaml
rules:
  - id: rule_custom
    name: "My Custom Rule"
    priority: 10
    conditions:
      api_exposure: external
      has_pci: false
      auth_type: mtls
    action: route
    gateway: apigee
    reason: "Custom routing logic"
```

---

## 🔍 PCI Data Detection

The agent uses LLM (OpenAI or Anthropic) to detect PCI/cardholder data in your API.

### What it detects:

- **Primary Account Number (PAN)** / Card Number
- **CVV/CVC** / Security Code
- **Expiration Date**
- **Cardholder Name**
- **Track Data**
- **PIN/PIN Block**

### How it works:

1. Extracts all fields from OpenAPI spec
2. Sends field names, types, and descriptions to LLM
3. LLM analyzes and returns PCI detection results
4. **IMPORTANT:** LLM is used ONLY for inference, NOT for gateway decisions

### Fallback

If LLM is unavailable, falls back to pattern-based detection using static field name patterns.

---

## 📊 Audit Logging

All gateway selection decisions are logged to:

```
~/.gateway-governance/audit-logs/gateway-decisions.jsonl
```

### Audit Entry Format

```json
{
  "timestamp": "2025-11-01T10:30:00Z",
  "session_id": "uuid",
  "project_dir": "/path/to/project",
  "decision": {
    "status": "success",
    "gateway": "datapower",
    "reason": "External API with PCI data...",
    "rule_id": "rule_002"
  },
  "context": {
    "pci_detected": true,
    "pci_fields": ["cardNumber", "cvv", "expiryDate"],
    "api_exposure": "external",
    "auth_type": "oauth"
  }
}
```

### Viewing Audit Logs

Use the `view_audit_log` MCP tool or directly read the JSONL file.

---

## 🚢 Deployment

The agent includes deployment stubs for:

- **GitHub Actions** - Trigger workflow on commit
- **Harness** - Trigger pipeline via API
- **GitLab CI** - Trigger pipeline on push

### Configuration

Create `~/.gateway-governance/deployment-config.json`:

```json
{
  "apigee": {
    "method": "github_actions",
    "workflow": ".github/workflows/deploy-apigee.yml",
    "enabled": true
  },
  "datapower": {
    "method": "harness",
    "pipeline": "datapower-deployment",
    "enabled": true
  }
}
```

### GitHub Actions Example

`.github/workflows/deploy-apigee.yml`:

```yaml
name: Deploy to Apigee

on:
  workflow_dispatch:
    inputs:
      gateway:
        required: true
      oas_file:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Apigee
        run: |
          apigee apis create -o ${{ secrets.APIGEE_ORG }} \
            -n my-api -f ${{ github.event.inputs.oas_file }}
```

---

## 🛡️ Guardrails

### Security Controls

1. ✅ **LLM used ONLY for inference** (PCI detection), never for decisions
2. ✅ **Static policy rules** are auditable and version-controlled
3. ✅ **Escalation workflow** for security violations
4. ✅ **Complete audit trail** of all decisions
5. ✅ **Conversational clarifications** for missing context

### Policy Validation

Validate your policy file:

```python
from modules.policy_engine import PolicyEngine

engine = PolicyEngine()
validation = engine.validate_policy()
print(validation)
```

---

## 📁 Project Structure

```
IDX_MCP/
├── server.py                    # Main MCP server entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── modules/                     # Core modules
│   ├── __init__.py
│   ├── oas_parser.py           # OpenAPI Spec parsing
│   ├── pci_detector.py         # PCI detection (LLM-based)
│   ├── policy_engine.py        # Static policy rule engine
│   ├── context_manager.py      # Session state management
│   ├── audit_logger.py         # Audit logging
│   └── deployment.py           # Deployment integration
│
├── config/                      # Configuration files
│   └── gateway-policy.yaml     # Policy rules definition
│
└── examples/                    # Example files
    ├── petstore-api.yaml       # Non-PCI API example
    ├── payment-api.yaml        # PCI API example
    └── gateway-selection.json  # Pre-configured example
```

---

## 🧪 Testing

### Test with Example APIs

**Non-PCI API (should route to Apigee):**

```bash
# Copy example
cp examples/petstore-api.yaml /tmp/test-project/openapi.yaml

# Run tool
select_gateway(project_dir="/tmp/test-project")
```

**PCI API (should route to DataPower):**

```bash
# Copy example
cp examples/payment-api.yaml /tmp/test-project/openapi.yaml

# Run tool
select_gateway(project_dir="/tmp/test-project")
```

**Pre-configured:**

```bash
# Copy pre-configured selection
cp examples/gateway-selection.json /tmp/test-project/

# Run tool - should use pre-configured gateway
select_gateway(project_dir="/tmp/test-project")
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | One of | OpenAI API key for PCI detection |
| `ANTHROPIC_API_KEY` | these | Anthropic API key for PCI detection |
| `GH_TOKEN` | Optional | GitHub token for deployment |
| `HARNESS_API_KEY` | Optional | Harness API key for deployment |

---

## 📚 Advanced Usage

### Custom LLM Provider

Modify `modules/pci_detector.py` to add custom LLM provider:

```python
async def _call_custom_llm(self, prompt: str) -> Dict[str, Any]:
    # Your custom LLM integration
    pass
```

### Custom Policy Rules

Add organization-specific rules to `config/gateway-policy.yaml`.

### Integration with CI/CD

The agent can trigger deployments via:
- GitHub Actions workflows
- Harness pipelines
- GitLab CI pipelines
- Custom webhooks

---

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. LLM is used ONLY for inference, not decisions
2. Policy rules remain static and auditable
3. All decisions are logged
4. Tests pass

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙋 Support

For issues or questions:
- GitHub Issues: [Create an issue](#)
- Email: ESGADEV@team.com

---

## 🎯 Roadmap

- [ ] Support for Azure API Management
- [ ] Integration with AWS API Gateway
- [ ] Advanced PII detection (beyond PCI)
- [ ] Real-time policy validation in IDE
- [ ] Dashboard for audit log visualization
- [ ] Multi-tenancy support
- [ ] RBAC for policy management

---

**Built with ❤️ for Shift-Left Governance**

# idx_gtwy
