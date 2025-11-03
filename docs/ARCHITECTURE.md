# Architecture & Design

This document explains the architectural decisions, design patterns, and security guardrails of the Gateway Governance Agent.

---

## 🎯 Design Principles

### 1. **Separation of Concerns**

The system is designed with clear separation between:

- **LLM Inference** (PCI detection) - Uses AI for data analysis
- **Policy Decisions** (Gateway selection) - Uses static, auditable rules
- **Orchestration** (Agent) - Coordinates workflow
- **State Management** (Context Manager) - Manages session data
- **Persistence** (Audit Logger) - Records all decisions

### 2. **Security First**

- ✅ LLM **never** makes gateway decisions
- ✅ All decisions follow static policy rules
- ✅ Complete audit trail for compliance
- ✅ Escalation workflow for security violations
- ✅ No sensitive data in logs

### 3. **Developer Experience**

- ✅ Conversational interaction
- ✅ Smart contextual questions
- ✅ Works across all IDEs via MCP
- ✅ Fast inference (<5 seconds)
- ✅ Clear, actionable decisions

---

## 🏗️ System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         MCP Server                          │
│                       (server.py)                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         GatewayGovernanceAgent                       │  │
│  │         (Main Orchestrator)                          │  │
│  │                                                      │  │
│  │  • Workflow coordination                            │  │
│  │  • Session management                               │  │
│  │  • Tool call handling                               │  │
│  └──────────┬───────────────────────────────────────────┘  │
│             │                                              │
│  ┌──────────▼──────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  OASParser          │  │ PCIDetector  │  │ Policy   │  │
│  │                     │  │              │  │ Engine   │  │
│  │  • Find OAS files   │  │ • LLM call   │  │ • Rules  │  │
│  │  • Parse YAML/JSON  │  │ • Pattern    │  │ • Match  │  │
│  │  • Extract fields   │  │   fallback   │  │ • Decide │  │
│  └─────────────────────┘  └──────────────┘  └──────────┘  │
│                                                             │
│  ┌─────────────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  ContextManager     │  │ AuditLogger  │  │ Deploy   │  │
│  │                     │  │              │  │ Manager  │  │
│  │  • Session state    │  │ • JSONL log  │  │ • GitHub │  │
│  │  • Context data     │  │ • Export     │  │ • Harness│  │
│  │  • Cleanup          │  │ • Stats      │  │ • Stub   │  │
│  └─────────────────────┘  └──────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Breakdown

### server.py

**Responsibility:** MCP server and main orchestration

**Key Components:**
- `GatewayGovernanceAgent` - Main agent class
- MCP tool handlers (`@app.call_tool()`)
- Tool definitions (`@app.list_tools()`)
- Main event loop

**Flow:**
1. MCP client connects via stdio
2. Client calls tool (e.g., `select_gateway`)
3. Agent orchestrates workflow
4. Returns result to client

---

### modules/oas_parser.py

**Responsibility:** OpenAPI Specification detection and parsing

**Key Methods:**
- `find_oas_file()` - Searches for OAS files in project
- `parse_oas_file()` - Parses YAML/JSON OAS
- `extract_schemas()` - Extracts schema definitions
- `extract_fields()` - Gets all field names

**Search Strategy:**
1. Check common filenames (`openapi.yaml`, `api.yaml`, etc.)
2. Search for files with OAS extensions (`.yaml`, `.yml`, `.json`)
3. Look in subdirectories (`api/`, `specs/`, `docs/`)
4. Validate each file for `openapi` field

---

### modules/pci_detector.py

**Responsibility:** Detect PCI/cardholder data using LLM

**⚠️ CRITICAL GUARDRAIL:** This module uses LLM ONLY for inference, NOT for decisions.

**Key Methods:**
- `analyze_oas_for_pci()` - Main analysis entry point
- `_llm_based_detection()` - LLM inference (preferred)
- `_pattern_based_detection()` - Fallback (no LLM needed)
- `_call_openai()` / `_call_anthropic()` - LLM providers

**LLM Prompt Design:**
```
Input:
  - Field names
  - Field types
  - Field descriptions
  
Output (JSON only):
  {
    "has_pci": bool,
    "pci_fields": [list],
    "confidence": float,
    "reasoning": string
  }
```

**Fallback Pattern Matching:**
- Checks field names against known PCI patterns
- `cardnumber`, `cvv`, `pan`, `expirydate`, etc.
- Lower confidence but works without LLM

---

### modules/policy_engine.py

**Responsibility:** Apply static policy rules for gateway selection

**⚠️ CRITICAL GUARDRAIL:** This module NEVER uses LLM. Only static rule matching.

**Rule Evaluation:**
1. Load rules from `config/gateway-policy.yaml`
2. Sort by priority (ascending)
3. Iterate until first match
4. Return decision from matched rule

**Rule Structure:**
```yaml
- id: rule_001
  priority: 1
  conditions:
    api_exposure: external
    has_pci: true
    auth_type: none
  action: escalate
  reason: "Security escalation required"
```

**Condition Matching:**
- All conditions must match (AND logic)
- Supports exact match and list of values
- Empty conditions = default rule (matches all)

**Actions:**
- `route` - Route to specified gateway
- `escalate` - Security escalation to email

---

### modules/context_manager.py

**Responsibility:** Manage session state and context

**Session Lifecycle:**
1. `create_session()` - New session with UUID
2. `update_context()` - Add/update data
3. `get_context()` - Retrieve session data
4. `close_session()` - Mark as closed
5. `cleanup_old_sessions()` - Remove stale sessions

**Context Data:**
```python
{
  "session_id": "uuid",
  "project_dir": "/path",
  "oas_file": "/path/openapi.yaml",
  "pci_detected": true,
  "pci_fields": ["cardNumber", "cvv"],
  "api_exposure": "external",
  "auth_type": "oauth",
  "gateway": "datapower",
  "reason": "...",
  "created_at": "2025-11-01T10:30:00Z"
}
```

---

### modules/audit_logger.py

**Responsibility:** Log all gateway selection decisions

**Log Format:** JSONL (JSON Lines) - one JSON object per line

**Audit Entry:**
```json
{
  "timestamp": "ISO-8601",
  "session_id": "uuid",
  "project_dir": "/path",
  "decision": {
    "status": "success|escalation",
    "gateway": "apigee|datapower",
    "reason": "...",
    "rule_id": "rule_002"
  },
  "context": {
    "pci_detected": true,
    "pci_fields": [...],
    "api_exposure": "external",
    "auth_type": "oauth"
  }
}
```

**Features:**
- Append-only log (immutable)
- Export to JSON or CSV
- Statistics calculation
- Per-project filtering

**Storage Location:**
```
~/.gateway-governance/audit-logs/gateway-decisions.jsonl
```

---

### modules/deployment.py

**Responsibility:** Deploy APIs to selected gateway

**Deployment Methods:**
- `github_actions` - Trigger GitHub Actions workflow
- `harness` - Trigger Harness pipeline
- `gitlab_ci` - Trigger GitLab CI
- `stub` - Create deployment metadata (default)

**Stub Deployment:**
Creates `gateway-deployment.json` in project with:
- Selected gateway
- OAS file path
- Deployment method
- Next steps for manual deployment

**Real Deployment:**
- Requires configuration in `~/.gateway-governance/deployment-config.json`
- Calls CI/CD platform API
- Returns deployment status

---

## 🔒 Security Guardrails

### 1. LLM Boundary

```
┌─────────────────┐       ┌─────────────────┐
│  LLM ZONE       │       │  POLICY ZONE    │
│  (Inference)    │       │  (Decisions)    │
├─────────────────┤       ├─────────────────┤
│ • Detect PCI    │  ❌   │ • Select gateway│
│ • Parse fields  │  NO   │ • Apply rules   │
│ • Confidence    │  LLM  │ • Route/Escalate│
└─────────────────┘       └─────────────────┘
```

**Enforcement:**
- `pci_detector.py` returns only analysis, not decisions
- `policy_engine.py` never calls LLM
- Audit log shows rule ID that made decision

### 2. Decision Traceability

Every decision includes:
- ✅ Rule ID that matched
- ✅ Input conditions
- ✅ Timestamp
- ✅ Session context

This allows:
- Compliance audits
- Policy debugging
- Rollback analysis
- Pattern detection

### 3. Escalation Workflow

When dangerous pattern detected:
```yaml
conditions:
  api_exposure: external
  has_pci: true
  auth_type: none
action: escalate
escalation_email: "ESGADEV@team.com"
```

**Result:**
- ❌ No gateway selected
- 📧 Email notification generated
- 📝 Logged with "escalation" status
- 🚫 Deployment blocked

### 4. Immutable Audit Log

- Append-only JSONL file
- No deletion or modification
- Timestamped entries
- Can be shipped to SIEM

---

## 🔄 Data Flow

### Complete Decision Flow

```
1. Developer Request
   ↓
2. Check gateway-selection.json
   ├─ Found → Use it (skip analysis)
   └─ Not found → Continue
   ↓
3. Find OAS file
   ├─ Found → Parse it
   └─ Not found → Error
   ↓
4. Extract fields from OAS
   ↓
5. LLM Analysis (PCI Detection)
   ├─ Success → Use LLM result
   └─ Failed → Use pattern matching
   ↓
6. Store PCI analysis in context
   ↓
7. Check for missing context
   ├─ Missing → Ask questions
   └─ Complete → Continue
   ↓
8. Developer answers questions
   ↓
9. Policy Engine Evaluation
   ├─ Match rule 1 → Return decision
   ├─ Match rule 2 → Return decision
   └─ Default rule → Return decision
   ↓
10. Log decision to audit
   ↓
11. Optional: Deploy to gateway
```

---

## 🧪 Testing Strategy

### Unit Tests

Each module has isolated tests:

```python
# test_oas_parser.py
def test_find_oas_file():
    parser = OASParser()
    result = parser.find_oas_file(test_dir)
    assert result is not None

# test_pci_detector.py
async def test_pattern_detection():
    detector = PCIDetector()
    result = await detector._pattern_based_detection(fields)
    assert result["has_pci"] == True
```

### Integration Tests

Test complete workflows:

```python
# test_agent.py
async def test_end_to_end():
    agent = GatewayGovernanceAgent()
    result = await agent.process_request(project_dir)
    # Verify complete flow
```

### Policy Validation

```python
engine = PolicyEngine()
validation = engine.validate_policy()
assert validation["valid"] == True
```

---

## 📊 Performance Considerations

### Caching Strategy

- **OAS Parsing:** Cache parsed specs by file hash
- **LLM Results:** Cache by OAS content hash (24h TTL)
- **Policy Rules:** Load once at startup

### Optimization

- **Parallel Processing:** Can analyze multiple APIs concurrently
- **Lazy Loading:** Only load modules when needed
- **Batch Mode:** Support bulk analysis for CI/CD

---

## 🔮 Extensibility

### Adding New Gateways

1. Add gateway to `config/gateway-policy.yaml`:
```yaml
gateways:
  kong:
    name: "Kong Gateway"
    capabilities: [...]
```

2. Add rules routing to new gateway:
```yaml
rules:
  - gateway: kong
    conditions: {...}
```

### Adding New LLM Providers

1. Add to `modules/pci_detector.py`:
```python
async def _call_custom_provider(self, prompt):
    # Implementation
    pass
```

2. Update constructor:
```python
if self.llm_provider == "custom":
    return await self._call_custom_provider(prompt)
```

### Custom Policy Conditions

Add new condition types in `policy_engine.py`:

```python
def _matches_conditions(self, input_data, conditions):
    # Add custom matching logic
    if "custom_field" in conditions:
        # Handle custom field
    return super()._matches_conditions(input_data, conditions)
```

---

## 📈 Monitoring & Observability

### Metrics to Track

1. **Decision Metrics:**
   - Gateway distribution (% Apigee vs DataPower)
   - Escalation rate
   - PCI detection rate

2. **Performance Metrics:**
   - Decision time (p50, p95, p99)
   - LLM call latency
   - Error rate

3. **Usage Metrics:**
   - Decisions per day
   - Unique projects
   - Pre-configured vs analyzed

### Log Analysis

```python
from modules.audit_logger import AuditLogger

logger = AuditLogger()
stats = await logger.get_statistics()

print(f"Total decisions: {stats['total_decisions']}")
print(f"Apigee: {stats['gateways']['apigee']}")
print(f"DataPower: {stats['gateways']['datapower']}")
print(f"Escalations: {stats['escalations']}")
```

---

## 🛠️ Operational Considerations

### Backup & Recovery

**Audit Logs:**
```bash
# Backup
cp ~/.gateway-governance/audit-logs/gateway-decisions.jsonl \
   /backup/gateway-decisions-$(date +%Y%m%d).jsonl

# Restore
cp /backup/gateway-decisions-*.jsonl \
   ~/.gateway-governance/audit-logs/gateway-decisions.jsonl
```

### Disaster Recovery

1. Policy files in git (version controlled)
2. Audit logs backed up daily
3. Session state is ephemeral (can rebuild)

### Scaling

**Horizontal Scaling:**
- Run multiple MCP server instances
- Share audit logs via network file system
- Use Redis for session state

**Vertical Scaling:**
- Current design handles 1000s of decisions/day
- LLM calls are async (non-blocking)
- Policy evaluation is CPU-light

---

## 📝 Compliance & Governance

### PCI DSS Alignment

The system helps achieve:
- **Requirement 2:** Ensure gateway selection for cardholder data
- **Requirement 10:** Audit trail of all decisions
- **Requirement 6:** Secure development (shift-left)

### SOC 2 Controls

- **CC6.1:** Logical access controls (escalation)
- **CC7.2:** System monitoring (audit logs)
- **A1.2:** Data confidentiality (PCI detection)

### Export for Compliance

```python
logger = AuditLogger()
logger.export_logs("audit-2025-Q1.csv", format="csv")
```

---

## 🎓 Best Practices

### For Developers

1. ✅ Create `gateway-selection.json` for production APIs
2. ✅ Use meaningful API descriptions in OAS
3. ✅ Tag PCI fields clearly in schema
4. ✅ Review audit logs regularly

### For Governance Teams

1. ✅ Customize policy rules for your organization
2. ✅ Monitor escalation rate
3. ✅ Review PCI detection accuracy
4. ✅ Export audit logs for compliance reporting

### For Platform Teams

1. ✅ Set up CI/CD integration for deployment
2. ✅ Monitor MCP server health
3. ✅ Back up audit logs
4. ✅ Keep policy rules in version control

---

**Architecture designed for security, auditability, and developer experience** 🚀

