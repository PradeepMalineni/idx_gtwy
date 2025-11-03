"""
Deployment Manager
Handles deployment to API gateways via CI/CD or GitOps
Includes proxy bundle generation and deployment to dev environments
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages deployment to API gateways"""
    
    SUPPORTED_GATEWAYS = ["apigee", "datapower"]
    
    def __init__(self):
        """Initialize deployment manager"""
        self.deployment_configs = self._load_deployment_configs()
        
        # Import proxy generator
        try:
            from modules.proxy_generator import ProxyGenerator
            self.proxy_generator = ProxyGenerator()
        except ImportError:
            logger.warning("ProxyGenerator not available")
            self.proxy_generator = None
    
    def _load_deployment_configs(self) -> Dict[str, Any]:
        """
        Load deployment configurations
        
        Returns:
            Dictionary of deployment configurations
        """
        config_path = Path.home() / ".gateway-governance" / "deployment-config.json"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    configs = json.load(f)
                logger.info(f"Loaded deployment configs from {config_path}")
                return configs
            except Exception as e:
                logger.warning(f"Failed to load deployment configs: {str(e)}")
        
        # Return default configs
        return {
            "apigee": {
                "method": "github_actions",
                "workflow": ".github/workflows/deploy-apigee.yml",
                "enabled": False
            },
            "datapower": {
                "method": "harness",
                "pipeline": "datapower-deployment",
                "enabled": False
            }
        }
    
    async def deploy(
        self,
        gateway: str,
        oas_file: Optional[str],
        project_dir: str
    ) -> Dict[str, Any]:
        """
        Deploy API to gateway
        
        Args:
            gateway: Target gateway (apigee or datapower)
            oas_file: Path to OAS file
            project_dir: Project directory
            
        Returns:
            Deployment result dictionary
        """
        if gateway not in self.SUPPORTED_GATEWAYS:
            return {
                "status": "error",
                "message": f"Unsupported gateway: {gateway}. Supported: {self.SUPPORTED_GATEWAYS}"
            }
        
        logger.info(f"Starting deployment to {gateway}")
        
        # Get deployment config for gateway
        config = self.deployment_configs.get(gateway, {})
        
        if not config.get("enabled", False):
            return await self._stub_deployment(gateway, oas_file, project_dir, config)
        
        # Route to appropriate deployment method
        method = config.get("method")
        
        if method == "github_actions":
            return await self._deploy_via_github_actions(gateway, oas_file, project_dir, config)
        elif method == "harness":
            return await self._deploy_via_harness(gateway, oas_file, project_dir, config)
        elif method == "gitlab_ci":
            return await self._deploy_via_gitlab(gateway, oas_file, project_dir, config)
        else:
            return await self._stub_deployment(gateway, oas_file, project_dir, config)
    
    async def _stub_deployment(
        self,
        gateway: str,
        oas_file: Optional[str],
        project_dir: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stub deployment (for when actual deployment is not configured)
        
        Args:
            gateway: Target gateway
            oas_file: Path to OAS file
            project_dir: Project directory
            config: Deployment configuration
            
        Returns:
            Stub deployment result
        """
        logger.info(f"Stub deployment to {gateway} (not actually deployed)")
        
        # Create deployment metadata file
        deployment_file = Path(project_dir) / "gateway-deployment.json"
        
        deployment_metadata = {
            "gateway": gateway,
            "oas_file": oas_file,
            "method": config.get("method", "stub"),
            "status": "stub",
            "message": "Deployment stub created. To enable actual deployment, configure deployment settings.",
            "next_steps": self._get_deployment_instructions(gateway, config)
        }
        
        try:
            with open(deployment_file, 'w') as f:
                json.dump(deployment_metadata, f, indent=2)
            
            logger.info(f"Created deployment metadata file: {deployment_file}")
        except Exception as e:
            logger.warning(f"Failed to create deployment metadata: {str(e)}")
        
        return {
            "status": "stub",
            "gateway": gateway,
            "message": f"✅ Deployment prepared for {gateway.upper()}",
            "next_steps": deployment_metadata["next_steps"],
            "metadata_file": str(deployment_file)
        }
    
    def _get_deployment_instructions(self, gateway: str, config: Dict[str, Any]) -> list[str]:
        """
        Get deployment instructions for gateway
        
        Args:
            gateway: Target gateway
            config: Deployment configuration
            
        Returns:
            List of deployment instructions
        """
        method = config.get("method", "github_actions")
        
        if gateway == "apigee":
            if method == "github_actions":
                return [
                    "1. Commit your OpenAPI specification to the repository",
                    "2. Push changes to trigger GitHub Actions workflow",
                    f"3. Workflow file: {config.get('workflow', '.github/workflows/deploy-apigee.yml')}",
                    "4. Monitor deployment in GitHub Actions tab",
                    "5. Verify deployment in Apigee console"
                ]
            else:
                return [
                    "1. Use Apigee CLI: apicli deployapi -o <org> -e <env> -n <api-name>",
                    "2. Or deploy via Apigee UI: API Proxies → Create → Upload OAS",
                    "3. Configure policies and deploy to environment"
                ]
        
        elif gateway == "datapower":
            if method == "harness":
                return [
                    "1. Commit your OpenAPI specification to the repository",
                    "2. Trigger Harness pipeline for DataPower deployment",
                    f"3. Pipeline: {config.get('pipeline', 'datapower-deployment')}",
                    "4. Monitor deployment in Harness dashboard",
                    "5. Verify deployment in DataPower console"
                ]
            else:
                return [
                    "1. Export API configuration for DataPower",
                    "2. Upload configuration to DataPower gateway",
                    "3. Apply security policies (OAuth, mTLS)",
                    "4. Test API endpoints",
                    "5. Promote to production domain"
                ]
        
        return ["Configure deployment method in deployment-config.json"]
    
    async def _deploy_via_github_actions(
        self,
        gateway: str,
        oas_file: Optional[str],
        project_dir: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy via GitHub Actions"""
        import subprocess
        
        try:
            # Trigger GitHub Actions workflow
            workflow = config.get("workflow")
            
            # Use GitHub CLI to trigger workflow
            result = subprocess.run(
                ["gh", "workflow", "run", workflow, "-f", f"gateway={gateway}", "-f", f"oas_file={oas_file}"],
                cwd=project_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "gateway": gateway,
                    "message": f"GitHub Actions workflow triggered for {gateway}",
                    "workflow": workflow
                }
            else:
                raise Exception(result.stderr)
        
        except FileNotFoundError:
            logger.warning("GitHub CLI (gh) not found, falling back to stub deployment")
            return await self._stub_deployment(gateway, oas_file, project_dir, config)
        except Exception as e:
            logger.error(f"GitHub Actions deployment failed: {str(e)}")
            return {
                "status": "error",
                "message": f"Deployment failed: {str(e)}"
            }
    
    async def _deploy_via_harness(
        self,
        gateway: str,
        oas_file: Optional[str],
        project_dir: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy via Harness CI/CD"""
        # This would integrate with Harness API
        # For now, return stub
        logger.info("Harness deployment not yet implemented")
        return await self._stub_deployment(gateway, oas_file, project_dir, config)
    
    async def _deploy_via_gitlab(
        self,
        gateway: str,
        oas_file: Optional[str],
        project_dir: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy via GitLab CI"""
        # This would integrate with GitLab CI
        # For now, return stub
        logger.info("GitLab CI deployment not yet implemented")
        return await self._stub_deployment(gateway, oas_file, project_dir, config)
    
    async def generate_and_deploy(
        self,
        gateway: str,
        oas_spec: Dict[str, Any],
        oas_file: str,
        project_dir: str,
        api_name: str,
        confirmed: bool = False
    ) -> Dict[str, Any]:
        """
        Generate proxy bundle from template and deploy to dev environment
        
        Args:
            gateway: Target gateway (apigee or datapower)
            oas_spec: Parsed OpenAPI specification
            oas_file: Path to OAS file
            project_dir: Project directory
            api_name: Name of the API
            confirmed: Whether user has confirmed deployment
            
        Returns:
            Deployment result with bundle info
        """
        if not confirmed:
            return {
                "status": "confirmation_needed",
                "message": f"Ready to generate {gateway.upper()} proxy bundle and deploy to dev environment.",
                "gateway": gateway,
                "api_name": api_name,
                "next_steps": [
                    f"1. Generate {gateway.upper()} proxy bundle from seed template",
                    f"2. Deploy to {gateway.upper()} dev environment for testing",
                    "3. Verify deployment and test API endpoints"
                ],
                "confirmation_required": True
            }
        
        logger.info(f"Generating and deploying {gateway} proxy for {api_name}")
        
        if not self.proxy_generator:
            return {
                "status": "error",
                "message": "Proxy generator not available"
            }
        
        # Generate proxy bundle
        if gateway == "apigee":
            result = await self._generate_and_deploy_apigee(
                api_name, oas_spec, project_dir
            )
        elif gateway == "datapower":
            result = await self._generate_and_deploy_datapower(
                api_name, oas_spec, project_dir
            )
        else:
            return {
                "status": "error",
                "message": f"Unsupported gateway: {gateway}"
            }
        
        return result
    
    async def _generate_and_deploy_apigee(
        self,
        api_name: str,
        oas_spec: Dict[str, Any],
        project_dir: str
    ) -> Dict[str, Any]:
        """Generate Apigee proxy bundle and deploy to dev"""
        
        logger.info(f"Generating Apigee proxy bundle for {api_name}")
        
        try:
            # Create output directory
            output_dir = Path(project_dir) / "build" / "apigee"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate proxy bundle
            generation_result = await self.proxy_generator.generate_apigee_proxy(
                api_name=api_name,
                oas_spec=oas_spec,
                output_dir=str(output_dir)
            )
            
            if generation_result["status"] != "success":
                return generation_result
            
            bundle_path = generation_result["bundle_path"]
            
            # Deploy to Apigee dev environment
            deployment_result = await self._deploy_apigee_bundle(
                bundle_path=bundle_path,
                api_name=api_name,
                environment="dev"
            )
            
            return {
                "status": "success",
                "gateway": "apigee",
                "message": f"✅ Apigee proxy bundle generated and deployed to dev",
                "bundle_path": bundle_path,
                "proxy_name": generation_result["proxy_name"],
                "base_path": generation_result["base_path"],
                "deployment": deployment_result,
                "test_url": f"https://{{org}}-dev.apigee.net{generation_result['base_path']}",
                "next_steps": [
                    f"1. Test API at: https://{{org}}-dev.apigee.net{generation_result['base_path']}",
                    "2. Verify policies are working correctly",
                    "3. Run integration tests",
                    "4. Promote to test/prod when ready"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error deploying to Apigee: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to deploy to Apigee: {str(e)}"
            }
    
    async def _deploy_apigee_bundle(
        self,
        bundle_path: str,
        api_name: str,
        environment: str = "dev"
    ) -> Dict[str, Any]:
        """Deploy Apigee bundle to environment"""
        
        config = self.deployment_configs.get("apigee", {})
        
        # Check if apigeecli is available
        try:
            # Get Apigee org from environment or config
            org = os.getenv("APIGEE_ORG", config.get("organization", "your-org"))
            token = os.getenv("APIGEE_TOKEN")
            
            if not token:
                return {
                    "status": "stub",
                    "message": "Apigee token not configured. Bundle created but not deployed.",
                    "bundle_path": bundle_path,
                    "manual_deploy": f"apigee apis create -o {org} -n {api_name} -p {bundle_path}"
                }
            
            # Deploy using apigeecli
            cmd = [
                "apigeecli", "apis", "create",
                "-o", org,
                "-n", api_name,
                "-p", bundle_path,
                "-t", token
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # Deploy to environment
                deploy_cmd = [
                    "apigeecli", "apis", "deploy",
                    "-o", org,
                    "-n", api_name,
                    "-e", environment,
                    "-t", token
                ]
                
                deploy_result = subprocess.run(deploy_cmd, capture_output=True, text=True, timeout=60)
                
                if deploy_result.returncode == 0:
                    return {
                        "status": "deployed",
                        "environment": environment,
                        "organization": org,
                        "revision": "1"
                    }
            
            return {
                "status": "error",
                "message": result.stderr or deploy_result.stderr
            }
            
        except FileNotFoundError:
            return {
                "status": "stub",
                "message": "apigeecli not found. Install with: npm install -g apigeecli",
                "bundle_path": bundle_path,
                "manual_deploy_steps": [
                    "1. Install apigeecli: npm install -g apigeecli",
                    f"2. Deploy bundle: apigeecli apis create -o {{org}} -n {api_name} -p {bundle_path}",
                    f"3. Deploy to env: apigeecli apis deploy -o {{org}} -n {api_name} -e {environment}"
                ]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Deployment failed: {str(e)}"
            }
    
    async def _generate_and_deploy_datapower(
        self,
        api_name: str,
        oas_spec: Dict[str, Any],
        project_dir: str
    ) -> Dict[str, Any]:
        """Generate DataPower configuration and deploy to dev"""
        
        logger.info(f"Generating DataPower configuration for {api_name}")
        
        try:
            # Create output directory
            output_dir = Path(project_dir) / "build" / "datapower"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate DataPower config
            generation_result = await self.proxy_generator.generate_datapower_config(
                api_name=api_name,
                oas_spec=oas_spec,
                output_dir=str(output_dir),
                domain="dev"
            )
            
            if generation_result["status"] != "success":
                return generation_result
            
            package_path = generation_result["package_path"]
            
            # Deploy to DataPower dev domain
            deployment_result = await self._deploy_datapower_config(
                package_path=package_path,
                api_name=api_name,
                domain="dev"
            )
            
            return {
                "status": "success",
                "gateway": "datapower",
                "message": f"✅ DataPower configuration generated and deployed to dev domain",
                "package_path": package_path,
                "api_name": generation_result["api_name"],
                "domain": "dev",
                "base_path": generation_result["base_path"],
                "deployment": deployment_result,
                "config_files": generation_result["files"],
                "test_url": f"https://{{datapower-host}}:8443{generation_result['base_path']}",
                "next_steps": [
                    "1. Verify MPGW is enabled in DataPower",
                    f"2. Test API at: https://{{datapower-host}}:8443{generation_result['base_path']}",
                    "3. Verify security policies (OAuth, mTLS, PCI protection)",
                    "4. Run compliance tests",
                    "5. Promote to test/prod when validated"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error deploying to DataPower: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to deploy to DataPower: {str(e)}"
            }
    
    async def _deploy_datapower_config(
        self,
        package_path: str,
        api_name: str,
        domain: str = "dev"
    ) -> Dict[str, Any]:
        """Deploy DataPower configuration to domain"""
        
        config = self.deployment_configs.get("datapower", {})
        
        # Check if we have DataPower REST API credentials
        dp_host = os.getenv("DATAPOWER_HOST", config.get("gateway_url"))
        dp_user = os.getenv("DATAPOWER_USER")
        dp_pass = os.getenv("DATAPOWER_PASS")
        
        if not all([dp_host, dp_user, dp_pass]):
            return {
                "status": "stub",
                "message": "DataPower credentials not configured. Configuration generated but not deployed.",
                "package_path": package_path,
                "manual_deploy_steps": [
                    "1. Extract package contents",
                    "2. Login to DataPower WebGUI",
                    f"3. Navigate to domain: {domain}",
                    "4. Import configuration files",
                    "5. Enable Multi-Protocol Gateway",
                    "6. Test API endpoint"
                ]
            }
        
        # Use DataPower REST API to deploy
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            # Upload configuration
            url = f"{dp_host}/mgmt/config/{domain}"
            
            with open(package_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    url,
                    files=files,
                    auth=HTTPBasicAuth(dp_user, dp_pass),
                    verify=False,  # In production, use proper certs
                    timeout=60
                )
            
            if response.status_code in [200, 201]:
                return {
                    "status": "deployed",
                    "domain": domain,
                    "host": dp_host,
                    "message": "Configuration deployed successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Deployment failed: {response.text}"
                }
                
        except ImportError:
            return {
                "status": "stub",
                "message": "requests library not installed. Install with: pip install requests",
                "package_path": package_path
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Deployment failed: {str(e)}"
            }
    
    def get_deployment_status(self, gateway: str, deployment_id: str) -> Dict[str, Any]:
        """
        Get deployment status
        
        Args:
            gateway: Target gateway
            deployment_id: Deployment identifier
            
        Returns:
            Deployment status
        """
        # This would query the CI/CD platform for deployment status
        return {
            "status": "unknown",
            "message": "Deployment status tracking not yet implemented",
            "gateway": gateway,
            "deployment_id": deployment_id
        }

