#!/usr/bin/env python3
"""
Gateway Governance Agent - MCP Server
Shift-Left API Gateway Selection and Deployment

This MCP server helps developers select and deploy APIs to the correct
API Gateway based on policy-driven decision-making.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from modules.oas_parser import OASParser
from modules.pci_detector import PCIDetector
from modules.policy_engine import PolicyEngine
from modules.audit_logger import AuditLogger
from modules.deployment import DeploymentManager
from modules.context_manager import ContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("gateway-governance-agent")

# Initialize components
oas_parser = OASParser()
pci_detector = PCIDetector()
policy_engine = PolicyEngine()
audit_logger = AuditLogger()
deployment_manager = DeploymentManager()
context_manager = ContextManager()


class GatewayGovernanceAgent:
    """Main agent orchestrator for gateway selection and deployment"""
    
    def __init__(self):
        self.context_manager = context_manager
        self.oas_parser = oas_parser
        self.pci_detector = pci_detector
        self.policy_engine = policy_engine
        self.audit_logger = audit_logger
        self.deployment_manager = deployment_manager
        
    async def process_request(self, project_dir: str, auto_deploy: bool = False) -> Dict[str, Any]:
        """
        Main orchestration method for gateway selection
        
        Args:
            project_dir: Path to the project directory
            auto_deploy: Whether to automatically trigger deployment
            
        Returns:
            Dict containing decision, reason, and next steps
        """
        project_path = Path(project_dir)
        session_id = self.context_manager.create_session(project_dir)
        
        logger.info(f"Starting gateway selection process for {project_dir}")
        
        try:
            # Step 1: Check for existing gateway-selection.json
            gateway_config_path = project_path / "gateway-selection.json"
            if gateway_config_path.exists():
                logger.info("Found existing gateway-selection.json")
                return await self._handle_existing_config(gateway_config_path, session_id)
            
            # Step 2: Search for OAS file
            oas_file = self.oas_parser.find_oas_file(project_path)
            if not oas_file:
                return {
                    "status": "error",
                    "message": "No OpenAPI Specification file found. Please create an OAS file (.yaml, .yml, or .json) with 'openapi' field.",
                    "action_required": "create_oas"
                }
            
            logger.info(f"Found OAS file: {oas_file}")
            
            # Step 3: Parse OAS file
            oas_spec = self.oas_parser.parse_oas_file(oas_file)
            if not oas_spec:
                return {
                    "status": "error",
                    "message": f"Invalid OpenAPI Specification in {oas_file}. Please ensure it contains 'openapi' field.",
                    "action_required": "fix_oas"
                }
            
            # Step 4: Detect PCI/sensitive data using LLM
            logger.info("Analyzing API for PCI/sensitive data...")
            pci_analysis = await self.pci_detector.analyze_oas_for_pci(oas_spec)
            
            # Store in context
            self.context_manager.update_context(session_id, {
                "oas_file": str(oas_file),
                "oas_spec": oas_spec,
                "pci_detected": pci_analysis["has_pci"],
                "pci_fields": pci_analysis.get("pci_fields", []),
                "pci_confidence": pci_analysis.get("confidence", 0)
            })
            
            # Step 5: Gather missing context (will be handled by Q&A in subsequent calls)
            context = self.context_manager.get_context(session_id)
            missing_info = self._identify_missing_info(context)
            
            if missing_info:
                return {
                    "status": "needs_input",
                    "session_id": session_id,
                    "message": "I need some additional information to make the gateway decision:",
                    "questions": missing_info,
                    "current_analysis": {
                        "pci_detected": pci_analysis["has_pci"],
                        "pci_fields": pci_analysis.get("pci_fields", [])
                    }
                }
            
            # Step 6: Apply policy rules
            decision = await self._make_gateway_decision(session_id)
            
            # Step 7: Log decision
            await self.audit_logger.log_decision(
                session_id=session_id,
                project_dir=project_dir,
                decision=decision,
                context=self.context_manager.get_context(session_id)
            )
            
            # Step 8: Optional deployment
            if auto_deploy and decision["status"] == "success":
                deployment_result = await self.deployment_manager.deploy(
                    gateway=decision["gateway"],
                    oas_file=str(oas_file),
                    project_dir=project_dir
                )
                decision["deployment"] = deployment_result
            
            return decision
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }
    
    async def _handle_existing_config(self, config_path: Path, session_id: str) -> Dict[str, Any]:
        """Handle existing gateway-selection.json"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            gateway = config.get("gateway")
            reason = config.get("reason", "Pre-configured in gateway-selection.json")
            
            # Update context
            self.context_manager.update_context(session_id, {
                "gateway": gateway,
                "reason": reason,
                "config_source": "existing_file"
            })
            
            # Log decision
            await self.audit_logger.log_decision(
                session_id=session_id,
                project_dir=str(config_path.parent),
                decision={
                    "gateway": gateway,
                    "reason": reason,
                    "source": "existing_config"
                },
                context=self.context_manager.get_context(session_id)
            )
            
            return {
                "status": "success",
                "gateway": gateway,
                "reason": reason,
                "source": "existing_config",
                "message": f"Using pre-configured gateway: {gateway}",
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"Error reading gateway-selection.json: {str(e)}")
            return {
                "status": "error",
                "message": f"Error reading gateway-selection.json: {str(e)}"
            }
    
    def _identify_missing_info(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify missing information needed for decision"""
        questions = []
        
        if "api_exposure" not in context:
            questions.append({
                "key": "api_exposure",
                "question": "Is this API exposed externally or used internally only?",
                "options": ["external", "internal"]
            })
        
        if "auth_type" not in context:
            questions.append({
                "key": "auth_type",
                "question": "What type of authentication is used for this API?",
                "options": ["oauth", "mtls", "both", "none"]
            })
        
        return questions
    
    async def _make_gateway_decision(self, session_id: str) -> Dict[str, Any]:
        """Apply policy rules to make gateway decision"""
        context = self.context_manager.get_context(session_id)
        
        # Build decision input
        decision_input = {
            "has_pci": context.get("pci_detected", False),
            "api_exposure": context.get("api_exposure"),
            "auth_type": context.get("auth_type"),
            "pci_fields": context.get("pci_fields", [])
        }
        
        # Apply static policy rules (NOT LLM-based)
        decision = self.policy_engine.evaluate(decision_input)
        
        # Update context with decision
        self.context_manager.update_context(session_id, {
            "gateway": decision["gateway"],
            "reason": decision["reason"],
            "rule_matched": decision.get("rule_id")
        })
        
        return decision
    
    async def answer_questions(self, session_id: str, answers: Dict[str, str]) -> Dict[str, Any]:
        """Process developer's answers to contextual questions"""
        # Update context with answers
        self.context_manager.update_context(session_id, answers)
        
        # Check if we have all needed info now
        context = self.context_manager.get_context(session_id)
        missing_info = self._identify_missing_info(context)
        
        if missing_info:
            return {
                "status": "needs_input",
                "session_id": session_id,
                "message": "Thank you. I still need:",
                "questions": missing_info
            }
        
        # We have all info, make decision
        decision = await self._make_gateway_decision(session_id)
        
        # Log decision
        project_dir = context.get("project_dir", "unknown")
        await self.audit_logger.log_decision(
            session_id=session_id,
            project_dir=project_dir,
            decision=decision,
            context=context
        )
        
        return decision


# Initialize agent
agent = GatewayGovernanceAgent()


# Define MCP Tools
@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the MCP server"""
    return [
        Tool(
            name="select_gateway",
            description=(
                "Select and optionally deploy API to the appropriate gateway. "
                "Analyzes OpenAPI spec, detects PCI data, applies policy rules, "
                "and returns gateway recommendation (Apigee or DataPower)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "project_dir": {
                        "type": "string",
                        "description": "Path to the project directory containing the API"
                    },
                    "auto_deploy": {
                        "type": "boolean",
                        "description": "Whether to automatically trigger deployment",
                        "default": False
                    }
                },
                "required": ["project_dir"]
            }
        ),
        Tool(
            name="answer_questions",
            description=(
                "Provide answers to contextual questions about the API "
                "(e.g., external/internal, authentication type) to complete gateway selection."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from previous select_gateway call"
                    },
                    "answers": {
                        "type": "object",
                        "description": "Answers to questions (e.g., {'api_exposure': 'external', 'auth_type': 'oauth'})",
                        "properties": {
                            "api_exposure": {
                                "type": "string",
                                "enum": ["external", "internal"]
                            },
                            "auth_type": {
                                "type": "string",
                                "enum": ["oauth", "mtls", "both", "none"]
                            }
                        }
                    }
                },
                "required": ["session_id", "answers"]
            }
        ),
        Tool(
            name="view_audit_log",
            description="View the audit log of gateway selection decisions",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent entries to retrieve",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="deploy_to_gateway",
            description="Deploy API to the selected gateway via CI/CD or GitOps",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from previous select_gateway call"
                    },
                    "gateway": {
                        "type": "string",
                        "description": "Gateway to deploy to (apigee or datapower)",
                        "enum": ["apigee", "datapower"]
                    },
                    "project_dir": {
                        "type": "string",
                        "description": "Path to the project directory"
                    }
                },
                "required": ["gateway", "project_dir"]
            }
        ),
        Tool(
            name="generate_and_deploy_proxy",
            description=(
                "Generate proxy bundle from seed template and deploy to dev environment. "
                "Creates Apigee proxy bundle or DataPower configuration from templates, "
                "then deploys to dev for testing. Requires user confirmation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID from previous select_gateway call"
                    },
                    "confirmed": {
                        "type": "boolean",
                        "description": "User confirmation to proceed with deployment",
                        "default": False
                    }
                },
                "required": ["session_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls from the MCP client"""
    
    try:
        if name == "select_gateway":
            project_dir = arguments.get("project_dir")
            auto_deploy = arguments.get("auto_deploy", False)
            
            result = await agent.process_request(project_dir, auto_deploy)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "answer_questions":
            session_id = arguments.get("session_id")
            answers = arguments.get("answers", {})
            
            result = await agent.answer_questions(session_id, answers)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "view_audit_log":
            limit = arguments.get("limit", 10)
            logs = await audit_logger.get_recent_logs(limit)
            
            return [TextContent(
                type="text",
                text=json.dumps(logs, indent=2)
            )]
        
        elif name == "deploy_to_gateway":
            session_id = arguments.get("session_id")
            gateway = arguments.get("gateway")
            project_dir = arguments.get("project_dir")
            
            # Get OAS file from context if session_id provided
            oas_file = None
            if session_id:
                context = context_manager.get_context(session_id)
                oas_file = context.get("oas_file")
            
            result = await deployment_manager.deploy(
                gateway=gateway,
                oas_file=oas_file,
                project_dir=project_dir
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "generate_and_deploy_proxy":
            session_id = arguments.get("session_id")
            confirmed = arguments.get("confirmed", False)
            
            if not session_id:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "session_id is required"
                    })
                )]
            
            # Get context from session
            context = context_manager.get_context(session_id)
            
            if not context:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Session not found: {session_id}"
                    })
                )]
            
            gateway = context.get("gateway")
            oas_file = context.get("oas_file")
            oas_spec = context.get("oas_spec")
            project_dir = context.get("project_dir")
            
            if not all([gateway, oas_spec, project_dir]):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Missing required context. Please run select_gateway first."
                    })
                )]
            
            # Extract API name
            api_name = oas_spec.get("info", {}).get("title", "api")
            
            # Generate and deploy
            result = await deployment_manager.generate_and_deploy(
                gateway=gateway,
                oas_spec=oas_spec,
                oas_file=oas_file,
                project_dir=project_dir,
                api_name=api_name,
                confirmed=confirmed
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unknown tool: {name}"
                })
            )]
    
    except Exception as e:
        logger.error(f"Error executing tool {name}: {str(e)}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            })
        )]


async def main():
    """Main entry point for the MCP server"""
    logger.info("Starting Gateway Governance Agent MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

