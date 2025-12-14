# ReAct Framework: Reasoning + Acting with Human Feedback

## 🧠 Overview

The Gateway Governance Agent now implements a **ReAct (Reasoning + Acting)** framework that makes every decision transparent and improvable through human feedback.

### The ReAct Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                    SENSE (Observe)                          │
│  • Scan working directory                                   │
│  • Find gateway-selection.json or OpenAPI spec             │
│  • Detect PCI data, API characteristics                     │
│  • Identify missing context                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    THINK (Reason)                           │
│  • Analyze observations                                     │
│  • Consider policy rules                                    │
│  • Evaluate security implications                           │
│  • Document reasoning with confidence levels                │
│  • Consider alternatives                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    ACT (Plan & Execute)                     │
│  • Create action plan                                       │
│  • Explain why this action                                  │
│  • Specify expected outcome                                 │
│  • Request confirmation                                     │
│  • Execute and record results                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    FEEDBACK (Learn)                         │
│  • Request human feedback                                   │
│  • Record approval/corrections/suggestions                  │
│  • Self-reflection on outcomes                              │
│  • Store for future learning (RLHF)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Principles

### 1. **External Reasoning Storage**

All reasoning is stored in **JSON files**, not deep in code:
```
~/.gateway-governance/reasoning-store/
├── a1b2c3d4...json    # Full reasoning trace
├── b2c3d4e5...json    # Another trace
└── ...
```

Each trace contains:
- All observations made
- All thoughts and reasoning
- All actions planned and executed
- All feedback received
- Metrics and outcomes

### 2. **Transparent Decision Making**

Every decision includes:
- **What was observed** (Sense)
- **How it was interpreted** (Think)
- **Why this action** (Act)
- **What was learned** (Feedback)

### 3. **Human-in-the-Loop**

Before executing critical actions:
- System presents reasoning
- Human reviews and provides feedback
- System learns from corrections
- Future decisions improve

### 4. **Self-Reflection**

System reflects on:
- Did action achieve expected outcome?
- What was learned?
- Should approach be adjusted?

---

## 🔧 Using ReAct Mode

### Basic Usage

```python
from modules.react_agent import ReActAgent
import asyncio

async def main():
    agent = ReActAgent()
    
    # Use ReAct mode (with reasoning)
    result = await agent.process_gateway_selection(
        project_dir="/path/to/api",
        request_feedback=True  # Request human feedback
    )
    
    print(f"Status: {result['status']}")
    print(f"Trace ID: {result['trace_id']}")
    
    if result['status'] == 'awaiting_feedback':
        # System is asking for feedback
        print("\n🧠 Reasoning Summary:")
        print(result['reasoning_summary'])
        
        print("\n⚡ Proposed Action:")
        print(result['action_plan'])

asyncio.run(main())
```

### Via MCP Tool

```json
{
  "tool": "select_gateway_with_reasoning",
  "arguments": {
    "project_dir": "/path/to/api",
    "request_feedback": true
  }
}
```

---

## 📊 Reasoning Trace Structure

### Full Trace Example

```json
{
  "trace_id": "uuid",
  "session_id": "session-123",
  "task": "Select appropriate API gateway",
  "started_at": "2025-11-02T14:30:00Z",
  "completed_at": "2025-11-02T14:30:45Z",
  "status": "success",
  "summary": "Gateway selected: datapower",
  
  "steps": [
    {
      "step": 1,
      "type": "observation",
      "observation": "Found OpenAPI Specification: payment-api.yaml",
      "data": {"file_path": "...", "file_size": 2048}
    },
    {
      "step": 2,
      "type": "thought",
      "thought": "API handles PCI data",
      "reasoning": "Fields detected: cardNumber, cvv...",
      "confidence": 0.95,
      "alternatives_considered": []
    },
    {
      "step": 3,
      "type": "action",
      "action": "select_gateway",
      "parameters": {"gateway": "datapower"},
      "why_this_action": "Policy rule matched...",
      "expected_outcome": "Gateway selected",
      "status": "completed",
      "outcome_matches_expected": true
    },
    {
      "step": 4,
      "type": "self_reflection",
      "reflection": "Action successful",
      "learned": "Rule rule_002 works well for PCI APIs",
      "should_adjust": false
    }
  ],
  
  "observations": [...],
  "thoughts": [...],
  "actions": [...],
  "feedback": [...],
  
  "metrics": {
    "total_steps": 11,
    "successful_actions": 1,
    "success_rate": 1.0,
    "average_confidence": 0.95,
    "human_rating": 1.0
  }
}
```

---

## 🎭 The Four Phases Explained

### PHASE 1: SENSE (Observation)

**What it does:**
- Scans project directory
- Looks for `gateway-selection.json`
- Searches for OpenAPI Specification
- Parses OAS file
- Detects PCI/sensitive data
- Identifies missing context

**Example Observations:**
```json
{
  "observation": "Found OpenAPI Specification: payment-api.yaml",
  "data": {
    "file_path": "/path/to/payment-api.yaml",
    "file_size": 2048,
    "title": "Payment Processing API",
    "paths_count": 5
  }
}
```

```json
{
  "observation": "PCI analysis complete: true",
  "data": {
    "pci_detected": true,
    "pci_fields": ["cardNumber", "cvv", "expiryDate"],
    "confidence": 0.95,
    "method": "llm_openai"
  }
}
```

---

### PHASE 2: THINK (Reasoning)

**What it does:**
- Analyzes all observations
- Considers policy rules
- Evaluates security implications
- Documents reasoning
- Assigns confidence levels
- Considers alternatives

**Example Thoughts:**
```json
{
  "thought": "Analyzing API security characteristics",
  "reasoning": "The API handles PCI data. Fields detected: cardNumber, cvv, expiryDate, cardholderName. This is critical for gateway selection as PCI data requires DataPower.",
  "confidence": 0.95,
  "alternatives_considered": [],
  "context_used": {
    "recent_observations": [...],
    "recent_thoughts": [...]
  }
}
```

```json
{
  "thought": "Evaluating policy rules",
  "reasoning": "Considering 3 potential policy rules. Top rule: External PCI with OAuth/mTLS - DataPower",
  "confidence": 0.9,
  "alternatives_considered": [
    "Internal PCI - DataPower",
    "External PCI without Security - Escalate"
  ]
}
```

**Confidence Levels:**
- `1.0` - Certain (e.g., pre-configured file found)
- `0.9` - Very confident (policy rule clearly matches)
- `0.8` - Confident (PCI detected with high confidence)
- `0.7` - Moderately confident (pattern-based detection)
- `< 0.7` - Low confidence (ambiguous signals)

---

### PHASE 3: ACT (Planning & Execution)

**What it does:**
- Creates action plan
- Explains why this action
- Specifies expected outcome
- Requests human confirmation
- Executes action
- Records actual outcome

**Example Action:**
```json
{
  "action_id": "act-001",
  "action": "select_gateway",
  "parameters": {
    "gateway": "datapower",
    "rule_id": "rule_002"
  },
  "expected_outcome": "Gateway datapower selected and ready for deployment",
  "why_this_action": "Policy rule rule_002 matched: External API with PCI data and OAuth/mTLS → DataPower (PCI DSS compliant gateway)",
  "status": "completed",
  "result": {
    "gateway": "datapower",
    "reason": "..."
  },
  "outcome_matches_expected": true
}
```

---

### PHASE 4: FEEDBACK (Learning)

**Types of Feedback:**

1. **Self-Reflection** (automatic):
```json
{
  "type": "self_reflection",
  "reflection": "Action executed successfully",
  "learned": "Gateway selection completed using rule rule_002",
  "should_adjust": false,
  "adjustment": null
}
```

2. **Human Approval**:
```json
{
  "type": "approval",
  "feedback": "Correct decision. DataPower is the right choice.",
  "rating": 1.0,
  "corrections": {}
}
```

3. **Human Correction**:
```json
{
  "type": "correction",
  "feedback": "Should have used Apigee for this internal API",
  "rating": 0.3,
  "corrections": {
    "gateway": "apigee",
    "reason": "Internal APIs with OAuth should use Apigee"
  }
}
```

4. **Human Suggestion**:
```json
{
  "type": "suggestion",
  "feedback": "Consider checking if mTLS is actually configured",
  "rating": 0.8,
  "corrections": {
    "additional_check": "verify_mtls_config"
  }
}
```

---

## 🔍 Viewing Reasoning Traces

### View Current Trace

```python
from modules.react_agent import ReActAgent

agent = ReActAgent()
trace = agent.get_reasoning_trace()

print(f"Task: {trace['task']}")
print(f"Steps: {trace['total_steps']}")
print(f"Observations: {trace['observations']}")
print(f"Thoughts: {trace['thoughts']}")
print(f"Actions: {trace['actions']}")
```

### View Specific Trace

```python
from modules.reasoning_engine import ReasoningEngine

engine = ReasoningEngine()
trace = engine.load_trace("trace-id-here")

# View all observations
for obs in trace['observations']:
    print(f"{obs['observation']}: {obs['data']}")

# View all thoughts
for thought in trace['thoughts']:
    print(f"💭 {thought['thought']}")
    print(f"   Reasoning: {thought['reasoning']}")
    print(f"   Confidence: {thought['confidence']}")
```

### Search Traces

```python
# Find all successful PCI API selections
traces = engine.search_traces(
    task_pattern="payment",
    status="success",
    limit=10
)

for trace in traces:
    print(f"{trace['trace_id']}: {trace['task']} - {trace['status']}")
```

---

## 📝 Providing Feedback

### Via Code

```python
agent = ReActAgent()

await agent.provide_feedback(
    session_id="session-123",
    feedback_type="approval",
    feedback="Excellent reasoning. The DataPower selection was correct.",
    rating=1.0
)
```

### Via MCP Tool

```json
{
  "tool": "provide_feedback",
  "arguments": {
    "session_id": "session-123",
    "feedback_type": "correction",
    "feedback": "Should have considered cost implications",
    "rating": 0.7,
    "corrections": {
      "additional_factor": "cost_analysis"
    }
  }
}
```

---

## 🎓 Learning from Feedback (RLHF)

The system uses **Reinforcement Learning from Human Feedback** principles:

### Feedback Loop

```
1. Agent makes decision
2. Human provides feedback (approval/correction/suggestion)
3. Feedback stored in reasoning trace
4. Metrics calculated (success rate, average rating)
5. Future decisions reference past feedback
6. System improves over time
```

### Metrics Tracked

```json
{
  "metrics": {
    "total_actions": 50,
    "successful_actions": 47,
    "success_rate": 0.94,
    "average_confidence": 0.89,
    "human_rating": 0.91,
    "feedback_count": 35
  }
}
```

### Using Feedback for Improvement

```python
# Search for similar past cases
similar_traces = engine.search_traces(
    task_pattern="payment api",
    status="success"
)

# Learn from high-rated decisions
for trace in similar_traces:
    if trace.get('human_rating', 0) >= 0.9:
        # This decision was highly rated
        # Use similar reasoning
        pass
```

---

## 🔄 Complete Workflow Example

```python
#!/usr/bin/env python3
import asyncio
from modules.react_agent import ReActAgent

async def complete_workflow():
    agent = ReActAgent()
    
    # STEP 1: Run ReAct cycle
    print("🔍 STEP 1: Running ReAct analysis...")
    result = await agent.process_gateway_selection(
        project_dir="/path/to/payment-api",
        request_feedback=True
    )
    
    if result['status'] == 'awaiting_feedback':
        # STEP 2: Review reasoning
        print("\n🧠 STEP 2: Reviewing reasoning...")
        print(f"Task: {result['reasoning_summary']['task']}")
        print(f"Steps: {result['reasoning_summary']['total_steps']}")
        
        # STEP 3: Review action plan
        print("\n⚡ STEP 3: Proposed action...")
        plan = result['action_plan']
        print(f"Action: {plan['action']}")
        print(f"Gateway: {plan['gateway']}")
        print(f"Reason: {plan['reason']}")
        
        # STEP 4: Provide feedback
        print("\n📝 STEP 4: Providing feedback...")
        feedback_result = await agent.provide_feedback(
            session_id=result['session_id'],
            feedback_type="approval",
            feedback="Correct decision. DataPower is appropriate for PCI data.",
            rating=1.0
        )
        print(feedback_result['message'])
    
    # STEP 5: View final trace
    print("\n📊 STEP 5: Final trace summary...")
    trace_id = result['trace_id']
    
    from modules.reasoning_engine import ReasoningEngine
    engine = ReasoningEngine()
    trace = engine.load_trace(trace_id)
    
    print(f"Status: {trace['status']}")
    print(f"Metrics: {trace['metrics']}")

asyncio.run(complete_workflow())
```

---

## 📈 Benefits of ReAct Framework

### 1. **Transparency**
- Every decision is explainable
- Full audit trail of reasoning
- No "black box" decisions

### 2. **Accountability**
- Know exactly why a decision was made
- Trace back to specific observations and rules
- Clear responsibility chain

### 3. **Improvability**
- Learn from human feedback
- Adjust based on corrections
- Improve confidence over time

### 4. **Debuggability**
- When something goes wrong, inspect the trace
- See exactly where reasoning diverged
- Fix specific steps

### 5. **Compliance**
- Full audit logs for regulators
- Demonstrate decision-making process
- Show governance enforcement

---

## 🔧 Configuration

### Reasoning Store Location

Default: `~/.gateway-governance/reasoning-store/`

Custom location:
```python
from modules.reasoning_engine import ReasoningEngine

engine = ReasoningEngine(
    reasoning_store_dir="/custom/path/to/reasoning-store"
)
```

### Enabling/Disabling ReAct Mode

**Use ReAct mode when:**
- Critical decisions
- Learning phase
- Audit requirements
- Debugging issues

**Use fast mode when:**
- Batch processing
- Pre-configured APIs
- Production automation

```python
# Fast mode (original)
result = await agent.process_request(project_dir)

# ReAct mode (with reasoning)
result = await react_agent.process_gateway_selection(
    project_dir,
    request_feedback=True
)
```

---

## 📊 Comparing Modes

| Feature | Fast Mode | ReAct Mode |
|---------|-----------|------------|
| **Speed** | ~2-3 seconds | ~10-15 seconds |
| **Reasoning** | Internal only | Fully documented |
| **Transparency** | Limited | Complete |
| **Feedback** | Not supported | Full RLHF |
| **Audit** | Decision only | Full trace |
| **Learning** | No | Yes |
| **Use Case** | Production | Critical/Learning |

---

## 🎯 Best Practices

### 1. **Use ReAct for Critical Decisions**
- PCI data handling
- External APIs
- Production deployments
- Compliance-critical APIs

### 2. **Provide Quality Feedback**
- Be specific in corrections
- Include reasoning in feedback
- Rate honestly (0.0-1.0)
- Suggest improvements

### 3. **Review Reasoning Traces**
- Regularly inspect traces
- Look for patterns
- Identify improvement areas
- Share with team

### 4. **Store Traces Safely**
- Backup reasoning-store directory
- Rotate old traces
- Archive high-value traces
- Analyze metrics

### 5. **Integrate with Workflow**
- Use in dev for learning
- Use in staging for validation
- Use in prod for critical decisions
- Export traces for compliance

---

## 🚀 Future Enhancements

Planned improvements:
- [ ] Visual reasoning trace viewer (web UI)
- [ ] Automated pattern recognition from feedback
- [ ] Collaborative feedback (team ratings)
- [ ] Reasoning quality scoring
- [ ] A/B testing different reasoning strategies
- [ ] Integration with external knowledge bases

---

## 📚 Additional Resources

- `examples/reasoning-trace-example.json` - Example trace
- `modules/reasoning_engine.py` - Reasoning engine code
- `modules/react_agent.py` - ReAct agent code
- `test_react_agent.py` - Test suite

---

**With ReAct, every decision is transparent, explainable, and improvable!** 🧠⚡


