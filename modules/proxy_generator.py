"""
Proxy Generator Module
Generates Apigee proxy bundles and DataPower configurations from seed templates
"""

import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import yaml

logger = logging.getLogger(__name__)


class ProxyGenerator:
    """Generates API Gateway proxy configurations from templates"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize proxy generator
        
        Args:
            templates_dir: Path to templates directory
        """
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).parent.parent / "templates"
        
        self.apigee_template_dir = self.templates_dir / "apigee"
        self.datapower_template_dir = self.templates_dir / "datapower"
        
        logger.info(f"Proxy generator initialized with templates: {self.templates_dir}")
    
    async def generate_apigee_proxy(
        self,
        api_name: str,
        oas_spec: Dict[str, Any],
        output_dir: str,
        base_path: Optional[str] = None,
        target_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Apigee proxy bundle from seed template
        
        Args:
            api_name: Name of the API proxy
            oas_spec: OpenAPI specification
            output_dir: Directory to output proxy bundle
            base_path: Base path for API (e.g., /v1/customers)
            target_url: Backend target URL
            
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Generating Apigee proxy bundle for {api_name}")
        
        try:
            # Create output directory
            output_path = Path(output_dir)
            proxy_dir = output_path / "apiproxy"
            proxy_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract info from OAS
            api_info = self._extract_api_info(oas_spec, api_name, base_path, target_url)
            
            # Copy seed template
            self._copy_apigee_template(proxy_dir)
            
            # Generate proxy configuration
            self._generate_apigee_proxy_xml(proxy_dir, api_info)
            
            # Generate proxy endpoint
            self._generate_apigee_proxy_endpoint(proxy_dir, api_info)
            
            # Generate target endpoint
            self._generate_apigee_target_endpoint(proxy_dir, api_info)
            
            # Add policies
            self._generate_apigee_policies(proxy_dir, api_info)
            
            # Create bundle ZIP
            bundle_path = self._create_apigee_bundle(output_path, api_info['name'])
            
            logger.info(f"Apigee proxy bundle created: {bundle_path}")
            
            return {
                "status": "success",
                "proxy_name": api_info['name'],
                "bundle_path": str(bundle_path),
                "proxy_dir": str(proxy_dir),
                "base_path": api_info['base_path'],
                "target_url": api_info['target_url']
            }
            
        except Exception as e:
            logger.error(f"Error generating Apigee proxy: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate Apigee proxy: {str(e)}"
            }
    
    async def generate_datapower_config(
        self,
        api_name: str,
        oas_spec: Dict[str, Any],
        output_dir: str,
        domain: str = "default",
        base_path: Optional[str] = None,
        target_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate DataPower configuration from seed template
        
        Args:
            api_name: Name of the API
            oas_spec: OpenAPI specification
            output_dir: Directory to output configuration
            domain: DataPower domain name
            base_path: Base path for API
            target_url: Backend target URL
            
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Generating DataPower configuration for {api_name}")
        
        try:
            # Create output directory
            output_path = Path(output_dir)
            config_dir = output_path / "datapower"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract info from OAS
            api_info = self._extract_api_info(oas_spec, api_name, base_path, target_url)
            
            # Copy seed template
            self._copy_datapower_template(config_dir)
            
            # Generate multi-protocol gateway config
            mpgw_config = self._generate_datapower_mpgw(api_info, domain)
            mpgw_path = config_dir / f"{api_info['name']}-mpgw.xml"
            with open(mpgw_path, 'w') as f:
                f.write(mpgw_config)
            
            # Generate processing policy
            policy_config = self._generate_datapower_policy(api_info)
            policy_path = config_dir / f"{api_info['name']}-policy.xml"
            with open(policy_path, 'w') as f:
                f.write(policy_config)
            
            # Generate API gateway config
            api_config = self._generate_datapower_api_config(api_info, oas_spec)
            api_path = config_dir / f"{api_info['name']}-api.yaml"
            with open(api_path, 'w') as f:
                yaml.dump(api_config, f, default_flow_style=False)
            
            # Create deployment package
            package_path = self._create_datapower_package(output_path, api_info['name'])
            
            logger.info(f"DataPower configuration created: {package_path}")
            
            return {
                "status": "success",
                "api_name": api_info['name'],
                "package_path": str(package_path),
                "config_dir": str(config_dir),
                "domain": domain,
                "base_path": api_info['base_path'],
                "target_url": api_info['target_url'],
                "files": {
                    "mpgw": str(mpgw_path),
                    "policy": str(policy_path),
                    "api_config": str(api_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating DataPower config: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to generate DataPower config: {str(e)}"
            }
    
    def _extract_api_info(
        self,
        oas_spec: Dict[str, Any],
        api_name: str,
        base_path: Optional[str],
        target_url: Optional[str]
    ) -> Dict[str, Any]:
        """Extract API information from OAS spec"""
        
        info = oas_spec.get('info', {})
        servers = oas_spec.get('servers', [])
        
        # Determine base path
        if not base_path:
            if servers:
                # Extract from first server URL
                server_url = servers[0].get('url', '')
                from urllib.parse import urlparse
                parsed = urlparse(server_url)
                base_path = parsed.path or f"/v1/{api_name.lower().replace(' ', '-')}"
            else:
                base_path = f"/v1/{api_name.lower().replace(' ', '-')}"
        
        # Determine target URL
        if not target_url:
            if servers:
                target_url = servers[0].get('url', 'http://backend.example.com')
            else:
                target_url = 'http://backend.example.com'
        
        # Sanitize API name
        sanitized_name = api_name.lower().replace(' ', '-').replace('_', '-')
        
        return {
            'name': sanitized_name,
            'display_name': info.get('title', api_name),
            'description': info.get('description', f'API proxy for {api_name}'),
            'version': info.get('version', '1.0.0'),
            'base_path': base_path,
            'target_url': target_url,
            'paths': list(oas_spec.get('paths', {}).keys()),
            'security': oas_spec.get('security', [])
        }
    
    def _copy_apigee_template(self, proxy_dir: Path) -> None:
        """Copy Apigee seed template to proxy directory"""
        # Create directory structure
        (proxy_dir / "proxies").mkdir(exist_ok=True)
        (proxy_dir / "targets").mkdir(exist_ok=True)
        (proxy_dir / "policies").mkdir(exist_ok=True)
        (proxy_dir / "resources" / "jsc").mkdir(parents=True, exist_ok=True)
        
        # Copy from template if exists
        if self.apigee_template_dir.exists():
            for item in self.apigee_template_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(self.apigee_template_dir)
                    target_path = proxy_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
    
    def _copy_datapower_template(self, config_dir: Path) -> None:
        """Copy DataPower seed template to config directory"""
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy from template if exists
        if self.datapower_template_dir.exists():
            for item in self.datapower_template_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(self.datapower_template_dir)
                    target_path = config_dir / relative_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
    
    def _generate_apigee_proxy_xml(self, proxy_dir: Path, api_info: Dict[str, Any]) -> None:
        """Generate main Apigee proxy XML file"""
        
        proxy_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy revision="1" name="{api_info['name']}">
    <ConfigurationVersion majorVersion="4" minorVersion="0"/>
    <CreatedAt>{int(datetime.now().timestamp() * 1000)}</CreatedAt>
    <CreatedBy>gateway-governance-agent</CreatedBy>
    <Description>{api_info['description']}</Description>
    <DisplayName>{api_info['display_name']}</DisplayName>
    <LastModifiedAt>{int(datetime.now().timestamp() * 1000)}</LastModifiedAt>
    <LastModifiedBy>gateway-governance-agent</LastModifiedBy>
    <Policies>
        <Policy>Spike-Arrest</Policy>
        <Policy>Verify-API-Key</Policy>
        <Policy>CORS</Policy>
        <Policy>Response-Cache</Policy>
    </Policies>
    <ProxyEndpoints>
        <ProxyEndpoint>default</ProxyEndpoint>
    </ProxyEndpoints>
    <Resources/>
    <Spec></Spec>
    <TargetServers/>
    <TargetEndpoints>
        <TargetEndpoint>default</TargetEndpoint>
    </TargetEndpoints>
</APIProxy>"""
        
        with open(proxy_dir / f"{api_info['name']}.xml", 'w') as f:
            f.write(proxy_xml)
    
    def _generate_apigee_proxy_endpoint(self, proxy_dir: Path, api_info: Dict[str, Any]) -> None:
        """Generate Apigee proxy endpoint"""
        
        endpoint_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxyEndpoint name="default">
    <Description>Default Proxy Endpoint</Description>
    <FaultRules/>
    <PreFlow name="PreFlow">
        <Request>
            <Step>
                <Name>Spike-Arrest</Name>
            </Step>
            <Step>
                <Name>Verify-API-Key</Name>
            </Step>
            <Step>
                <Name>CORS</Name>
            </Step>
        </Request>
        <Response>
            <Step>
                <Name>Response-Cache</Name>
            </Step>
        </Response>
    </PreFlow>
    <PostFlow name="PostFlow">
        <Request/>
        <Response/>
    </PostFlow>
    <Flows/>
    <HTTPProxyConnection>
        <BasePath>{api_info['base_path']}</BasePath>
        <Properties/>
        <VirtualHost>secure</VirtualHost>
    </HTTPProxyConnection>
    <RouteRule name="default">
        <TargetEndpoint>default</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>"""
        
        with open(proxy_dir / "proxies" / "default.xml", 'w') as f:
            f.write(endpoint_xml)
    
    def _generate_apigee_target_endpoint(self, proxy_dir: Path, api_info: Dict[str, Any]) -> None:
        """Generate Apigee target endpoint"""
        
        target_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<TargetEndpoint name="default">
    <Description>Default Target Endpoint</Description>
    <FaultRules/>
    <PreFlow name="PreFlow">
        <Request/>
        <Response/>
    </PreFlow>
    <PostFlow name="PostFlow">
        <Request/>
        <Response/>
    </PostFlow>
    <Flows/>
    <HTTPTargetConnection>
        <URL>{api_info['target_url']}</URL>
    </HTTPTargetConnection>
</TargetEndpoint>"""
        
        with open(proxy_dir / "targets" / "default.xml", 'w') as f:
            f.write(target_xml)
    
    def _generate_apigee_policies(self, proxy_dir: Path, api_info: Dict[str, Any]) -> None:
        """Generate Apigee policies"""
        
        policies_dir = proxy_dir / "policies"
        
        # Spike Arrest Policy
        spike_arrest = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<SpikeArrest async="false" continueOnError="false" enabled="true" name="Spike-Arrest">
    <DisplayName>Spike Arrest</DisplayName>
    <Rate>100pm</Rate>
    <Identifier ref="client_id"/>
    <MessageWeight ref="request.header.weight"/>
</SpikeArrest>"""
        
        with open(policies_dir / "Spike-Arrest.xml", 'w') as f:
            f.write(spike_arrest)
        
        # API Key Verification Policy
        verify_key = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<VerifyAPIKey async="false" continueOnError="false" enabled="true" name="Verify-API-Key">
    <DisplayName>Verify API Key</DisplayName>
    <APIKey ref="request.queryparam.apikey"/>
</VerifyAPIKey>"""
        
        with open(policies_dir / "Verify-API-Key.xml", 'w') as f:
            f.write(verify_key)
        
        # CORS Policy
        cors = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage async="false" continueOnError="false" enabled="true" name="CORS">
    <DisplayName>Add CORS</DisplayName>
    <Add>
        <Headers>
            <Header name="Access-Control-Allow-Origin">*</Header>
            <Header name="Access-Control-Allow-Headers">origin, x-requested-with, accept, content-type, authorization</Header>
            <Header name="Access-Control-Max-Age">3628800</Header>
            <Header name="Access-Control-Allow-Methods">GET, PUT, POST, DELETE</Header>
        </Headers>
    </Add>
    <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
    <AssignTo createNew="false" transport="http" type="response"/>
</AssignMessage>"""
        
        with open(policies_dir / "CORS.xml", 'w') as f:
            f.write(cors)
        
        # Response Cache Policy
        cache = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ResponseCache async="false" continueOnError="false" enabled="true" name="Response-Cache">
    <DisplayName>Response Cache</DisplayName>
    <CacheKey>
        <Prefix/>
        <KeyFragment ref="request.uri" type="string"/>
    </CacheKey>
    <ExpirySettings>
        <TimeoutInSec>300</TimeoutInSec>
    </ExpirySettings>
</ResponseCache>"""
        
        with open(policies_dir / "Response-Cache.xml", 'w') as f:
            f.write(cache)
    
    def _create_apigee_bundle(self, output_path: Path, api_name: str) -> Path:
        """Create Apigee proxy bundle ZIP file"""
        
        bundle_path = output_path / f"{api_name}.zip"
        
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            apiproxy_dir = output_path / "apiproxy"
            for file_path in apiproxy_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)
        
        return bundle_path
    
    def _generate_datapower_mpgw(self, api_info: Dict[str, Any], domain: str) -> str:
        """Generate DataPower Multi-Protocol Gateway configuration"""
        
        mpgw_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<datapower-configuration version="8">
    <configuration domain="{domain}">
        <MultiProtocolGateway name="{api_info['name']}-mpgw">
            <mAdminState>enabled</mAdminState>
            <LocalAddress>0.0.0.0</LocalAddress>
            <LocalPort>8443</LocalPort>
            <FrontProtocol class="HTTPSSourceProtocolHandler">{api_info['name']}-https-fsh</FrontProtocol>
            <XMLManager class="XMLManager">default</XMLManager>
            <StylePolicy class="StylePolicy">{api_info['name']}-policy</StylePolicy>
            <Type>static-backend</Type>
            <BackendUrl>{api_info['target_url']}</BackendUrl>
            <PropagateURI>true</PropagateURI>
            <Monitor>
                <AdminState>enabled</AdminState>
            </Monitor>
            <RequestType>preprocessor</RequestType>
            <ResponseType>response</ResponseType>
            <RequestAttachments>allow</RequestAttachments>
            <ResponseAttachments>allow</ResponseAttachments>
        </MultiProtocolGateway>
        
        <HTTPSSourceProtocolHandler name="{api_info['name']}-https-fsh">
            <mAdminState>enabled</mAdminState>
            <LocalAddress>0.0.0.0</LocalAddress>
            <LocalPort>8443</LocalPort>
            <HTTPVersion>HTTP/1.1</HTTPVersion>
            <AllowedFeatures>
                <HTTP-1.0>off</HTTP-1.0>
                <HTTP-1.1>on</HTTP-1.1>
                <HTTP-2.0>on</HTTP-2.0>
                <POST>on</POST>
                <GET>on</GET>
                <PUT>on</PUT>
                <DELETE>on</DELETE>
                <HEAD>on</HEAD>
                <OPTIONS>on</OPTIONS>
                <PATCH>on</PATCH>
            </AllowedFeatures>
            <PersistentConnections>on</PersistentConnections>
        </HTTPSSourceProtocolHandler>
    </configuration>
</datapower-configuration>"""
        
        return mpgw_config
    
    def _generate_datapower_policy(self, api_info: Dict[str, Any]) -> str:
        """Generate DataPower processing policy"""
        
        policy_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<datapower-configuration version="8">
    <configuration domain="default">
        <StylePolicy name="{api_info['name']}-policy">
            <mAdminState>enabled</mAdminState>
            <PolicyMaps>
                <Rule>
                    <InputFilters class="FilterAction">input-filter</InputFilters>
                    <OutputFilters class="FilterAction">output-filter</OutputFilters>
                    <Actions>
                        <Type>request</Type>
                        <Rule class="StylePolicyAction">rate-limit</Rule>
                    </Actions>
                    <Actions>
                        <Type>request</Type>
                        <Rule class="StylePolicyAction">verify-oauth</Rule>
                    </Actions>
                    <Actions>
                        <Type>request</Type>
                        <Rule class="StylePolicyAction">route-to-backend</Rule>
                    </Actions>
                    <Actions>
                        <Type>response</Type>
                        <Rule class="StylePolicyAction">response-transform</Rule>
                    </Actions>
                </Rule>
            </PolicyMaps>
        </StylePolicy>
    </configuration>
</datapower-configuration>"""
        
        return policy_config
    
    def _generate_datapower_api_config(self, api_info: Dict[str, Any], oas_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate DataPower API configuration"""
        
        return {
            "api": {
                "name": api_info['name'],
                "version": api_info['version'],
                "title": api_info['display_name'],
                "description": api_info['description'],
                "basePath": api_info['base_path'],
                "security": api_info['security'],
                "backend": {
                    "url": api_info['target_url'],
                    "timeout": 60,
                    "retries": 3
                },
                "policies": {
                    "rate_limit": {
                        "enabled": True,
                        "requests_per_minute": 100
                    },
                    "oauth": {
                        "enabled": True,
                        "provider": "oauth-provider"
                    },
                    "mtls": {
                        "enabled": True,
                        "client_cert_required": True
                    },
                    "pci_protection": {
                        "enabled": True,
                        "mask_card_numbers": True,
                        "encrypt_at_rest": True
                    }
                },
                "paths": api_info['paths']
            }
        }
    
    def _create_datapower_package(self, output_path: Path, api_name: str) -> Path:
        """Create DataPower deployment package"""
        
        package_path = output_path / f"{api_name}-datapower.zip"
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            datapower_dir = output_path / "datapower"
            for file_path in datapower_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)
        
        return package_path

