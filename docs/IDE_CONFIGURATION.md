# IDE Configuration Guide

This guide shows how to configure different IDEs to connect to the Gateway Governance Agent MCP server.

---

## VS Code

### 1. Install MCP Extension

Install the MCP extension for VS Code from the marketplace.

### 2. Configure MCP Server

Create or edit `.vscode/settings.json` in your workspace:

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

### 3. Restart VS Code

The MCP server will automatically start when VS Code launches.

### 4. Use the Agent

Open the command palette (Cmd/Ctrl+Shift+P) and search for MCP commands:

- `MCP: Select Gateway for API`
- `MCP: View Audit Logs`
- `MCP: Deploy to Gateway`

---

## IntelliJ IDEA / PyCharm

### 1. Install MCP Plugin

Go to Settings → Plugins → Search for "MCP" → Install

### 2. Configure MCP Server

Go to Settings → Tools → MCP Servers → Add New Server:

- **Name:** Gateway Governance
- **Command:** `python`
- **Args:** `/Users/pradeepm/ProjX/IDX_MCP/server.py`
- **Environment Variables:**
  - `OPENAI_API_KEY`: Your API key

### 3. Restart IntelliJ

### 4. Use the Agent

Right-click in your project → MCP Tools → Gateway Governance

---

## Eclipse

### 1. Install MCP Plugin

Help → Eclipse Marketplace → Search "MCP" → Install

### 2. Configure Server

Window → Preferences → MCP → Servers → Add

- **Server Name:** Gateway Governance Agent
- **Executable:** `python`
- **Arguments:** `/Users/pradeepm/ProjX/IDX_MCP/server.py`
- **Environment:**
  ```
  OPENAI_API_KEY=your-key-here
  ```

### 3. Restart Eclipse

### 4. Use the Agent

Project → Right-click → MCP → Gateway Governance

---

## Cursor

Cursor has built-in MCP support.

### 1. Configure MCP Server

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

### 2. Restart Cursor

### 3. Use in Chat

Simply ask in the Cursor chat:

```
@gateway-governance Select and deploy to appropriate gateway for my API
```

---

## Command Line (Testing)

You can also interact with the MCP server directly via command line for testing:

```bash
# Start the server
python server.py

# In another terminal, use MCP client
mcp-client --server stdio --command "python server.py" \
  --tool select_gateway \
  --arg project_dir=/path/to/project
```

---

## Environment Variables

All IDEs should have access to these environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | One of | OpenAI API key for PCI detection |
| `ANTHROPIC_API_KEY` | these | Anthropic API key for PCI detection |

### Setting Environment Variables

**macOS/Linux (Bash/Zsh):**

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export OPENAI_API_KEY='sk-...'
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

**Windows:**

```powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-...', 'User')
```

---

## Troubleshooting

### MCP Server Not Starting

1. Check Python version (3.10+ required):
   ```bash
   python --version
   ```

2. Verify dependencies installed:
   ```bash
   pip list | grep mcp
   ```

3. Check server logs (look in IDE console)

### API Key Issues

1. Verify API key is set:
   ```bash
   echo $OPENAI_API_KEY
   ```

2. Test API key:
   ```bash
   python -c "import openai; print(openai.api_key[:10])"
   ```

### Connection Refused

1. Ensure only one instance of server is running
2. Check firewall settings
3. Restart IDE

---

## Advanced Configuration

### Custom Policy File

Set custom policy location via environment variable:

```json
{
  "env": {
    "GATEWAY_POLICY_FILE": "/path/to/custom-policy.yaml"
  }
}
```

### Custom Audit Log Directory

```json
{
  "env": {
    "AUDIT_LOG_DIR": "/path/to/custom/logs"
  }
}
```

### Disable Auto-Deployment

```json
{
  "env": {
    "DISABLE_AUTO_DEPLOY": "true"
  }
}
```

---

## Multi-Workspace Setup

If you work on multiple projects, you can:

1. **Option A:** Use the same MCP server for all workspaces
   - Server tracks sessions separately
   - Audit logs are centralized

2. **Option B:** Run separate servers per workspace
   - Different policy files per project
   - Isolated audit logs

Example for Option B:

```json
{
  "mcp.servers": {
    "gateway-governance-projectA": {
      "command": "python",
      "args": ["/path/to/IDX_MCP/server.py"],
      "env": {
        "GATEWAY_POLICY_FILE": "/path/to/projectA/policy.yaml"
      }
    },
    "gateway-governance-projectB": {
      "command": "python",
      "args": ["/path/to/IDX_MCP/server.py"],
      "env": {
        "GATEWAY_POLICY_FILE": "/path/to/projectB/policy.yaml"
      }
    }
  }
}
```

