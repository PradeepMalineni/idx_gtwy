# Proxy Generation & Deployment Guide

This guide explains how to generate proxy bundles from seed templates and deploy to dev environments for both Apigee and DataPower.

---

## 🎯 Overview

After the Gateway Governance Agent selects the appropriate gateway, you can automatically:

1. **Generate** proxy bundle/configuration from seed template
2. **Deploy** to dev environment for testing
3. **Verify** deployment and test endpoints

This streamlines the path from API specification to deployed proxy.

---

## 🚀 Quick Start

### Step 1: Select Gateway

```python
from server import GatewayGovernanceAgent
import asyncio

async def main():
    agent = GatewayGovernanceAgent()
    
    # Select gateway
    result = await agent.process_request("/path/to/your/api")
    
    # Answer questions if needed
    if result['status'] == 'needs_input':
        result = await agent.answer_questions(
            result['session_id'],
            {
                "api_exposure": "external",
                "auth_type": "oauth"
            }
        )
    
    print(f"Gateway: {result['gateway']}")
    session_id = result['session_id']

asyncio.run(main())
```

### Step 2: Generate and Deploy (with confirmation)

```python
from modules.deployment import DeploymentManager
from modules.context_manager import ContextManager

async def deploy():
    deployment_mgr = DeploymentManager()
    context_mgr = ContextManager()
    
    # Get session context
    context = context_mgr.get_context(session_id)
    
    # First call - request confirmation
    result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=context['project_dir'],
        api_name="Customer API",
        confirmed=False  # Request confirmation
    )
    
    print(result['message'])
    print("Next steps:", result['next_steps'])
    
    # User confirms
    user_confirmed = input("Proceed with deployment? (y/n): ")
    
    if user_confirmed.lower() == 'y':
        # Second call - deploy
        result = await deployment_mgr.generate_and_deploy(
            gateway=context['gateway'],
            oas_spec=context['oas_spec'],
            oas_file=context['oas_file'],
            project_dir=context['project_dir'],
            api_name="Customer API",
            confirmed=True  # Deploy
        )
        
        print(f"✅ {result['message']}")
        print(f"Bundle: {result['bundle_path']}")
        print(f"Test URL: {result['test_url']}")

asyncio.run(deploy())
```

---

## 📦 Apigee Proxy Generation

### What Gets Generated

#### 1. Proxy Bundle Structure

```
{api-name}.zip
└── apiproxy/
    ├── customer-api.xml              # Main proxy config
    ├── proxies/
    │   └── default.xml               # Proxy endpoint
    ├── targets/
    │   └── default.xml               # Target endpoint
    ├── policies/
    │   ├── Spike-Arrest.xml          # Rate limiting
    │   ├── Verify-API-Key.xml        # API key auth
    │   ├── CORS.xml                  # CORS headers
    │   └── Response-Cache.xml        # Response caching
    └── resources/
        └── jsc/                      # JavaScript resources
```

#### 2. Default Policies

| Policy | Purpose | Configuration |
|--------|---------|---------------|
| **Spike Arrest** | Rate limiting | 100 requests/minute |
| **Verify API Key** | Authentication | Query param: `apikey` |
| **CORS** | Cross-origin | Allow all origins |
| **Response Cache** | Performance | 5 minute TTL |

#### 3. Proxy Configuration

```xml
<APIProxy name="customer-api">
    <DisplayName>Customer API</DisplayName>
    <Description>API proxy for Customer API</Description>
    <BasePath>/v1/customers</BasePath>
    <ProxyEndpoints>
        <ProxyEndpoint>default</ProxyEndpoint>
    </ProxyEndpoints>
    <TargetEndpoints>
        <TargetEndpoint>default</TargetEndpoint>
    </TargetEndpoints>
</APIProxy>
```

### Deployment Process

1. **Generate Bundle**
   - Creates ZIP file in `{project}/build/apigee/`
   - Includes all policies and configuration

2. **Upload to Apigee**
   - Uses `apigeecli` if available
   - Falls back to manual instructions

3. **Deploy to Dev**
   - Deploys to `dev` environment
   - Creates revision 1

### Environment Variables

```bash
# Required for automated deployment
export APIGEE_ORG="your-org"
export APIGEE_TOKEN="your-token"

# Optional
export APIGEE_ENV="dev"  # Default: dev
```

### Manual Deployment

If automated deployment is not configured:

```bash
# Install CLI
npm install -g apigeecli

# Deploy bundle
apigeecli apis create \
  -o your-org \
  -n customer-api \
  -p build/apigee/customer-api.zip \
  -t your-token

# Deploy to environment
apigeecli apis deploy \
  -o your-org \
  -n customer-api \
  -e dev \
  -t your-token
```

### Testing Deployed API

```bash
# Get API key from Apigee
# Then test:

curl "https://your-org-dev.apigee.net/v1/customers?apikey=your-api-key"
```

---

## ⚙️ DataPower Configuration Generation

### What Gets Generated

#### 1. Configuration Package Structure

```
{api-name}-datapower.zip
└── datapower/
    ├── customer-api-mpgw.xml         # Multi-Protocol Gateway
    ├── customer-api-policy.xml       # Processing policy
    └── customer-api-api.yaml         # API configuration
```

#### 2. Multi-Protocol Gateway (MPGW)

```xml
<MultiProtocolGateway name="customer-api-mpgw">
    <LocalAddress>0.0.0.0</LocalAddress>
    <LocalPort>8443</LocalPort>
    <FrontProtocol>customer-api-https-fsh</FrontProtocol>
    <StylePolicy>customer-api-policy</StylePolicy>
    <Type>static-backend</Type>
    <BackendUrl>http://backend.example.com</BackendUrl>
    <PropagateURI>true</PropagateURI>
</MultiProtocolGateway>
```

#### 3. Processing Policy

Includes actions for:
- **Rate Limiting** - Protect backend
- **OAuth Verification** - Token validation
- **Request Routing** - Backend selection
- **Response Transformation** - Format responses

#### 4. API Configuration (YAML)

```yaml
api:
  name: customer-api
  version: 1.0.0
  basePath: /v1/customers
  backend:
    url: http://backend.example.com
    timeout: 60
    retries: 3
  policies:
    rate_limit:
      enabled: true
      requests_per_minute: 100
    oauth:
      enabled: true
      provider: oauth-provider
    mtls:
      enabled: true
      client_cert_required: true
    pci_protection:
      enabled: true
      mask_card_numbers: true
      encrypt_at_rest: true
```

### Deployment Process

1. **Generate Configuration**
   - Creates ZIP package in `{project}/build/datapower/`
   - Includes MPGW, policy, and API config

2. **Upload to DataPower**
   - Uses REST API if credentials configured
   - Falls back to manual instructions

3. **Deploy to Dev Domain**
   - Imports configuration to `dev` domain
   - Enables Multi-Protocol Gateway

### Environment Variables

```bash
# Required for automated deployment
export DATAPOWER_HOST="https://datapower.example.com"
export DATAPOWER_USER="admin"
export DATAPOWER_PASS="your-password"

# Optional
export DATAPOWER_DOMAIN="dev"  # Default: dev
```

### Manual Deployment

If automated deployment is not configured:

1. **Extract Package**
   ```bash
   unzip customer-api-datapower.zip -d datapower-config
   ```

2. **Login to DataPower WebGUI**
   - Navigate to your DataPower instance
   - Login with admin credentials

3. **Navigate to Dev Domain**
   - Select domain: `dev`

4. **Import Configuration**
   - Import `customer-api-mpgw.xml`
   - Import `customer-api-policy.xml`

5. **Enable MPGW**
   - Find `customer-api-mpgw`
   - Change admin state to `enabled`
   - Save configuration

6. **Verify**
   - Check MPGW status
   - Test endpoint

### Testing Deployed API

```bash
# Test with OAuth token
curl -H "Authorization: Bearer your-token" \
     --cert client.crt \
     --key client.key \
     https://datapower.example.com:8443/v1/customers
```

---

## 🎨 Customizing Templates

### Apigee Template Customization

Templates are in `templates/apigee/`

#### Add Custom Policy

1. Create policy XML in `templates/apigee/policies/`

```xml
<!-- templates/apigee/policies/Custom-Policy.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="Custom-Policy">
    <DisplayName>Custom Policy</DisplayName>
    <Add>
        <Headers>
            <Header name="X-Custom-Header">Custom Value</Header>
        </Headers>
    </Add>
</AssignMessage>
```

2. Update `proxy_generator.py` to include it

```python
def _generate_apigee_policies(self, proxy_dir: Path, api_info: Dict[str, Any]):
    # ... existing policies ...
    
    # Add custom policy
    custom = """<?xml version="1.0" encoding="UTF-8"?>
    <AssignMessage name="Custom-Policy">
        ...
    </AssignMessage>"""
    
    with open(policies_dir / "Custom-Policy.xml", 'w') as f:
        f.write(custom)
```

### DataPower Template Customization

Templates are in `templates/datapower/`

#### Add Custom Processing Rule

Update `_generate_datapower_policy()`:

```python
def _generate_datapower_policy(self, api_info: Dict[str, Any]):
    # Add custom processing action
    custom_action = """
    <Actions>
        <Type>request</Type>
        <Rule class="StylePolicyAction">custom-rule</Rule>
    </Actions>
    """
    # Include in policy config
```

---

## 🔧 MCP Tool Usage

### Tool: `generate_and_deploy_proxy`

**Purpose:** Generate proxy bundle and deploy to dev environment

**Input:**
```json
{
  "session_id": "uuid-from-select-gateway",
  "confirmed": false
}
```

**Output (Confirmation Needed):**
```json
{
  "status": "confirmation_needed",
  "message": "Ready to generate APIGEE proxy bundle and deploy to dev environment.",
  "gateway": "apigee",
  "api_name": "Customer API",
  "next_steps": [
    "1. Generate APIGEE proxy bundle from seed template",
    "2. Deploy to APIGEE dev environment for testing",
    "3. Verify deployment and test API endpoints"
  ],
  "confirmation_required": true
}
```

**Input (Confirmed):**
```json
{
  "session_id": "uuid-from-select-gateway",
  "confirmed": true
}
```

**Output (Deployed):**
```json
{
  "status": "success",
  "gateway": "apigee",
  "message": "✅ Apigee proxy bundle generated and deployed to dev",
  "bundle_path": "/path/to/customer-api.zip",
  "proxy_name": "customer-api",
  "base_path": "/v1/customers",
  "test_url": "https://org-dev.apigee.net/v1/customers",
  "deployment": {
    "status": "deployed",
    "environment": "dev",
    "organization": "your-org",
    "revision": "1"
  },
  "next_steps": [
    "1. Test API at: https://org-dev.apigee.net/v1/customers",
    "2. Verify policies are working correctly",
    "3. Run integration tests",
    "4. Promote to test/prod when ready"
  ]
}
```

---

## 📝 Complete Example

### End-to-End Workflow

```python
#!/usr/bin/env python3
import asyncio
from server import GatewayGovernanceAgent
from modules.deployment import DeploymentManager
from modules.context_manager import ContextManager

async def complete_workflow():
    """Complete workflow: Select → Generate → Deploy"""
    
    # Initialize components
    agent = GatewayGovernanceAgent()
    deployment_mgr = DeploymentManager()
    context_mgr = ContextManager()
    
    print("🔍 Step 1: Analyzing API...")
    
    # Select gateway
    result = await agent.process_request("/path/to/api")
    
    # Handle questions
    if result['status'] == 'needs_input':
        print("\n❓ Answering questions...")
        result = await agent.answer_questions(
            result['session_id'],
            {
                "api_exposure": "external",
                "auth_type": "oauth"
            }
        )
    
    print(f"\n✅ Gateway Selected: {result['gateway'].upper()}")
    print(f"📝 Reason: {result['reason']}")
    
    session_id = result['session_id']
    context = context_mgr.get_context(session_id)
    
    # Request deployment confirmation
    print("\n🚀 Step 2: Request Deployment...")
    
    deploy_result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=context['project_dir'],
        api_name=context['oas_spec']['info']['title'],
        confirmed=False  # Request confirmation
    )
    
    print(f"\n{deploy_result['message']}")
    print("\nNext steps:")
    for step in deploy_result['next_steps']:
        print(f"  {step}")
    
    # Get user confirmation
    confirm = input("\n👤 Proceed with deployment? (y/n): ")
    
    if confirm.lower() != 'y':
        print("❌ Deployment cancelled")
        return
    
    # Deploy
    print("\n📦 Step 3: Generating and Deploying...")
    
    deploy_result = await deployment_mgr.generate_and_deploy(
        gateway=context['gateway'],
        oas_spec=context['oas_spec'],
        oas_file=context['oas_file'],
        project_dir=context['project_dir'],
        api_name=context['oas_spec']['info']['title'],
        confirmed=True  # Confirmed
    )
    
    # Display results
    print(f"\n{deploy_result['message']}")
    print(f"\n📦 Bundle: {deploy_result['bundle_path']}")
    print(f"🔗 Test URL: {deploy_result['test_url']}")
    
    print("\n📋 Next Steps:")
    for step in deploy_result['next_steps']:
        print(f"  {step}")
    
    print("\n✅ Deployment Complete!")

if __name__ == "__main__":
    asyncio.run(complete_workflow())
```

---

## 🔍 Troubleshooting

### Apigee Issues

**Problem:** `apigeecli not found`

**Solution:**
```bash
npm install -g apigeecli
```

**Problem:** `Authentication failed`

**Solution:**
```bash
# Get token from Apigee
gcloud auth print-access-token
export APIGEE_TOKEN="$(gcloud auth print-access-token)"
```

**Problem:** `Proxy already exists`

**Solution:**
```bash
# Delete existing proxy
apigeecli apis delete -o org -n api-name -t token

# Or use update instead of create
apigeecli apis update -o org -n api-name -p bundle.zip -t token
```

### DataPower Issues

**Problem:** `Connection refused`

**Solution:**
- Verify DataPower host is accessible
- Check firewall rules
- Verify credentials

**Problem:** `Configuration import failed`

**Solution:**
- Check domain exists
- Verify user has admin rights
- Review DataPower logs

**Problem:** `MPGW won't enable`

**Solution:**
- Check port 8443 is available
- Verify SSL cert configuration
- Review processing policy

---

## 📊 Deployment Comparison

| Feature | Apigee | DataPower |
|---------|--------|-----------|
| **Bundle Format** | ZIP | ZIP |
| **Deployment Tool** | apigeecli | REST API |
| **Default Policies** | 4 policies | 4 policies |
| **Dev Environment** | dev | dev domain |
| **Test Port** | 443 | 8443 |
| **Auth** | API Key | OAuth + mTLS |
| **Deployment Time** | ~30 seconds | ~60 seconds |

---

## 🎓 Best Practices

1. **Always Test in Dev First**
   - Never deploy directly to production
   - Verify all policies work
   - Run integration tests

2. **Review Generated Configuration**
   - Check policies match requirements
   - Verify backend URLs
   - Validate base paths

3. **Customize Templates**
   - Add organization-specific policies
   - Include custom headers
   - Set appropriate rate limits

4. **Version Control**
   - Commit generated bundles to git
   - Tag deployments
   - Track changes

5. **Monitor Deployments**
   - Check deployment logs
   - Verify API is accessible
   - Test with real traffic

---

**Happy Deploying! 🚀**

