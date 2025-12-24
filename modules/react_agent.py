"""
ReAct Agent (Reasoning + Acting)
Implements Sense → Think → Act → Feedback loop with explainability
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from modules.reasoning_engine import ReasoningEngine
from modules.oas_parser import OASParser
from modules.pci_detector import PCIDetector
from modules.policy_engine import PolicyEngine
from modules.context_manager import ContextManager
from modules.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class ReActAgent:
    """
    ReAct Agent implementing Sense → Think → Act → Feedback cycle
    
    This agent makes all decisions transparent by:
    - Observing the environment (Sense)
    - Reasoning about observations (Think)
    - Planning and executing actions (Act)
    - Collecting and learning from feedback (Feedback)
    """
    
    def __init__(self):
        """Initialize ReAct agent with all components"""
        self.reasoning_engine = ReasoningEngine()
        self.oas_parser = OASParser()
        self.pci_detector = PCIDetector()
        self.policy_engine = PolicyEngine()
        self.context_manager = ContextManager()
        self.audit_logger = AuditLogger()
        
        logger.info("ReAct Agent initialized")
    
    async def process_gateway_selection(
        self,
        project_dir: str,
        request_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point for gateway selection using ReAct cycle
        
        Args:
            project_dir: Project directory to analyze
            request_feedback: Whether to request human feedback
            
        Returns:
            Result with reasoning trace
        """
        # Create session
        session_id = self.context_manager.create_session(project_dir)
        
        # Start reasoning trace
        trace_id = self.reasoning_engine.start_reasoning_trace(
            session_id=session_id,
            task=f"Select appropriate API gateway for project: {project_dir}"
        )
        
        logger.info(f"Starting ReAct cycle for {project_dir} (trace: {trace_id})")
        
        try:
            # SENSE: Observe the environment
            observations = await self._sense_phase(project_dir, session_id)
            
            # Check if we can proceed
            if observations["status"] == "error":
                return self._complete_with_error(observations["message"], session_id, trace_id)
            
            if observations["status"] == "needs_input":
                return self._request_user_input(observations, session_id, trace_id)
            
            # THINK: Reason about observations
            reasoning = await self._think_phase(session_id, observations)
            
            # ACT: Plan and propose actions
            action_plan = await self._act_phase(session_id, reasoning)
            
            # Request feedback before executing
            if request_feedback:
                return self._request_feedback_on_plan(action_plan, session_id, trace_id)
            
            # Execute actions
            result = await self._execute_actions(action_plan, session_id)
            
            # Complete trace
            self.reasoning_engine.complete_trace(
                status="success",
                summary=f"Gateway selected: {result.get('gateway')}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in ReAct cycle: {str(e)}", exc_info=True)
            return self._complete_with_error(str(e), session_id, trace_id)
    
    async def _sense_phase(self, project_dir: str, session_id: str) -> Dict[str, Any]:
        """
        SENSE: Observe the environment and gather data
        
        Args:
            project_dir: Project directory
            session_id: Session identifier
            
        Returns:
            Observations dictionary
        """
        logger.info("🔍 SENSE PHASE: Observing environment...")
        
        project_path = Path(project_dir)
        observations = {
            "status": "observed",
            "project_dir": project_dir,
            "findings": []
        }
        
        # Observation 1: Check for pre-configured gateway
        self.reasoning_engine.add_observation(
            observation="Checking for pre-configured gateway selection",
            data={"file": "gateway-selection.json", "location": str(project_path)}
        )
        
        gateway_config_path = project_path / "gateway-selection.json"
        if gateway_config_path.exists():
            import json
            with open(gateway_config_path, 'r') as f:
                config = json.load(f)
            
            self.reasoning_engine.add_observation(
                observation="Found pre-configured gateway selection file",
                data={"config": config}
            )
            
            observations["pre_configured"] = True
            observations["gateway"] = config.get("gateway")
            observations["reason"] = config.get("reason")
            observations["findings"].append("gateway-selection.json exists")
            
            self.context_manager.update_context(session_id, {
                "gateway": config.get("gateway"),
                "reason": config.get("reason"),
                "config_source": "pre_configured"
            })
            
            return observations
        
        # Observation 2: Search for OpenAPI Specification
        self.reasoning_engine.add_observation(
            observation="Searching for OpenAPI Specification file",
            data={"search_patterns": OASParser.OAS_FILENAMES}
        )
        
        oas_file = self.oas_parser.find_oas_file(project_path)
        
        if not oas_file:
            self.reasoning_engine.add_observation(
                observation="No OpenAPI Specification found",
                data={"searched_extensions": OASParser.OAS_EXTENSIONS}
            )
            
            observations["status"] = "error"
            observations["message"] = "No OpenAPI Specification file found"
            observations["findings"].append("No OAS file")
            return observations
        
        self.reasoning_engine.add_observation(
            observation=f"Found OpenAPI Specification: {oas_file.name}",
            data={"file_path": str(oas_file), "file_size": oas_file.stat().st_size}
        )
        observations["findings"].append(f"OAS file: {oas_file.name}")
        
        # Observation 3: Parse OAS file
        self.reasoning_engine.add_observation(
            observation="Parsing OpenAPI Specification",
            data={"file": str(oas_file)}
        )
        
        oas_spec = self.oas_parser.parse_oas_file(oas_file)
        
        if not oas_spec:
            observations["status"] = "error"
            observations["message"] = "Invalid OpenAPI Specification"
            return observations
        
        api_title = oas_spec.get("info", {}).get("title", "Unknown API")
        api_version = oas_spec.get("info", {}).get("version", "Unknown")
        paths_count = len(oas_spec.get("paths", {}))
        
        self.reasoning_engine.add_observation(
            observation=f"Successfully parsed OAS: {api_title} v{api_version}",
            data={
                "title": api_title,
                "version": api_version,
                "paths_count": paths_count,
                "has_security": bool(oas_spec.get("security"))
            }
        )
        observations["findings"].extend([
            f"API: {api_title}",
            f"Paths: {paths_count}"
        ])
        
        # Store in context
        self.context_manager.update_context(session_id, {
            "oas_file": str(oas_file),
            "oas_spec": oas_spec,
            "api_title": api_title
        })
        
        # Observation 4: Detect PCI/sensitive data
        self.reasoning_engine.add_observation(
            observation="Analyzing API for PCI/sensitive data",
            data={"method": "LLM-based with pattern fallback"}
        )
        
        pci_analysis = await self.pci_detector.analyze_oas_for_pci(oas_spec)
        
        self.reasoning_engine.add_observation(
            observation=f"PCI analysis complete: {pci_analysis['has_pci']}",
            data={
                "pci_detected": pci_analysis["has_pci"],
                "pci_fields": pci_analysis.get("pci_fields", []),
                "confidence": pci_analysis.get("confidence", 0),
                "method": pci_analysis.get("method")
            }
        )
        
        if pci_analysis["has_pci"]:
            observations["findings"].append(
                f"⚠️ PCI data detected: {', '.join(pci_analysis.get('pci_fields', []))}"
            )
        else:
            observations["findings"].append("✅ No PCI data detected")
        
        # Store PCI analysis
        self.context_manager.update_context(session_id, {
            "pci_detected": pci_analysis["has_pci"],
            "pci_fields": pci_analysis.get("pci_fields", []),
            "pci_confidence": pci_analysis.get("confidence", 0)
        })
        
        observations["oas_spec"] = oas_spec
        observations["pci_analysis"] = pci_analysis
        
        # Observation 5: Check for missing context
        context = self.context_manager.get_context(session_id)
        missing_info = self._identify_missing_info(context)
        
        if missing_info:
            self.reasoning_engine.add_observation(
                observation="Missing contextual information",
                data={"missing": [q["key"] for q in missing_info]}
            )
            
            observations["status"] = "needs_input"
            observations["missing_info"] = missing_info
            observations["findings"].append("❓ Contextual questions needed")
        
        return observations
    
    async def _think_phase(self, session_id: str, observations: Dict[str, Any]) -> Dict[str, Any]:
        """
        THINK: Reason about observations and formulate decision logic
        
        Args:
            session_id: Session identifier
            observations: Observations from sense phase
            
        Returns:
            Reasoning dictionary
        """
        logger.info("🧠 THINK PHASE: Reasoning about observations...")
        
        context = self.context_manager.get_context(session_id)
        
        # Thought 1: Analyze API characteristics
        api_characteristics = {
            "has_pci": context.get("pci_detected", False),
            "pci_fields": context.get("pci_fields", []),
            "api_exposure": context.get("api_exposure"),
            "auth_type": context.get("auth_type")
        }
        
        self.reasoning_engine.add_thought(
            thought="Analyzing API security characteristics",
            reasoning=f"The API {'handles PCI data' if api_characteristics['has_pci'] else 'does not handle PCI data'}. "
                     f"Fields detected: {', '.join(api_characteristics['pci_fields']) if api_characteristics['pci_fields'] else 'none'}. "
                     f"This is critical for gateway selection as PCI data requires DataPower.",
            confidence=context.get("pci_confidence", 0.8),
            alternatives_considered=[]
        )
        
        # Thought 2: Consider policy rules
        decision_input = {
            "has_pci": api_characteristics["has_pci"],
            "api_exposure": api_characteristics["api_exposure"],
            "auth_type": api_characteristics["auth_type"],
            "pci_fields": api_characteristics["pci_fields"]
        }
        
        # Get all matching rules
        potential_rules = self._get_potential_rules(decision_input)
        
        rule_reasoning = f"Considering {len(potential_rules)} potential policy rules. "
        if potential_rules:
            rule_reasoning += f"Top rule: {potential_rules[0]['name']} - {potential_rules[0]['reason']}"
        
        self.reasoning_engine.add_thought(
            thought="Evaluating policy rules for gateway selection",
            reasoning=rule_reasoning,
            confidence=0.9,
            alternatives_considered=[r["name"] for r in potential_rules[1:3]]
        )
        
        # Thought 3: Consider security implications
        security_concerns = []
        
        if api_characteristics["has_pci"] and api_characteristics["auth_type"] == "none":
            security_concerns.append("⚠️ CRITICAL: PCI data with no authentication - requires escalation")
        
        if api_characteristics["api_exposure"] == "external" and not api_characteristics["auth_type"]:
            security_concerns.append("⚠️ External API without authentication")
        
        if api_characteristics["has_pci"]:
            security_concerns.append("ℹ️ PCI data requires DataPower for compliance")
        
        self.reasoning_engine.add_thought(
            thought="Assessing security implications",
            reasoning=f"Security concerns: {'; '.join(security_concerns) if security_concerns else 'None identified'}",
            confidence=1.0 if security_concerns else 0.95,
            alternatives_considered=[]
        )
        
        return {
            "api_characteristics": api_characteristics,
            "decision_input": decision_input,
            "potential_rules": potential_rules,
            "security_concerns": security_concerns
        }
    
    async def _act_phase(self, session_id: str, reasoning: Dict[str, Any]) -> Dict[str, Any]:
        """
        ACT: Plan actions based on reasoning
        
        Args:
            session_id: Session identifier
            reasoning: Reasoning from think phase
            
        Returns:
            Action plan
        """
        logger.info("⚡ ACT PHASE: Planning actions...")
        
        # Apply policy engine
        decision = self.policy_engine.evaluate(reasoning["decision_input"])
        
        # Plan action
        if decision["status"] == "escalation":
            action_id = self.reasoning_engine.add_action(
                action="escalate_to_security",
                parameters={
                    "email": decision.get("escalation_email"),
                    "reason": decision.get("reason")
                },
                expected_outcome="Security team notified; deployment blocked",
                why_this_action=f"Policy rule {decision['rule_id']} triggered escalation due to: {decision['reason']}"
            )
        else:
            action_id = self.reasoning_engine.add_action(
                action="select_gateway",
                parameters={
                    "gateway": decision.get("gateway"),
                    "rule_id": decision.get("rule_id")
                },
                expected_outcome=f"Gateway {decision.get('gateway')} selected and ready for deployment",
                why_this_action=f"Policy rule {decision['rule_id']} matched: {decision['reason']}"
            )
        
        # Store decision
        self.context_manager.update_context(session_id, {
            "gateway": decision.get("gateway"),
            "reason": decision.get("reason"),
            "rule_matched": decision.get("rule_id"),
            "decision_status": decision["status"]
        })
        
        return {
            "action_id": action_id,
            "decision": decision,
            "requires_confirmation": True
        }
    
    async def _execute_actions(
        self,
        action_plan: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Execute planned actions
        
        Args:
            action_plan: Action plan from act phase
            session_id: Session identifier
            
        Returns:
            Execution results
        """
        logger.info("✅ Executing actions...")
        
        decision = action_plan["decision"]
        action_id = action_plan["action_id"]
        
        # Record action execution
        self.reasoning_engine.record_action_result(
            action_id=action_id,
            status="completed",
            result=decision,
            outcome_matches_expected=True
        )
        
        # Log to audit
        context = self.context_manager.get_context(session_id)
        await self.audit_logger.log_decision(
            session_id=session_id,
            project_dir=context.get("project_dir"),
            decision=decision,
            context=context
        )
        
        # Self-reflection
        self.reasoning_engine.add_self_reflection(
            reflection="Action executed successfully",
            learned=f"Gateway selection completed using rule {decision.get('rule_id')}",
            should_adjust=False,
            adjustment=None
        )
        
        return decision
    
    async def provide_feedback(
        self,
        session_id: str,
        feedback_type: str,
        feedback: str,
        rating: Optional[float] = None,
        corrections: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process human feedback (RLHF)
        
        Args:
            session_id: Session identifier
            feedback_type: Type of feedback
            feedback: Feedback text
            rating: Rating (0.0-1.0)
            corrections: Corrections to apply
            
        Returns:
            Feedback processing result
        """
        logger.info(f"📝 Processing feedback: {feedback_type}")
        
        self.reasoning_engine.add_human_feedback(
            feedback_type=feedback_type,
            feedback=feedback,
            rating=rating,
            corrections=corrections
        )
        
        # If corrections provided, learn from them
        if corrections:
            self.reasoning_engine.add_self_reflection(
                reflection="Received corrective feedback from human",
                learned=f"Human suggested corrections: {corrections}",
                should_adjust=True,
                adjustment="Update reasoning based on human feedback"
            )
        
        return {
            "status": "feedback_recorded",
            "message": "Thank you for your feedback. It will improve future decisions.",
            "feedback_type": feedback_type,
            "rating": rating
        }
    
    def get_reasoning_trace(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get reasoning trace for inspection
        
        Args:
            trace_id: Trace identifier (current if None)
            
        Returns:
            Reasoning trace
        """
        if trace_id:
            return self.reasoning_engine.load_trace(trace_id) or {}
        else:
            return self.reasoning_engine.get_reasoning_summary()
    
    def _identify_missing_info(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify missing contextual information"""
        questions = []
        
        if "api_exposure" not in context:
            questions.append({
                "key": "api_exposure",
                "question": "Is this API exposed externally or used internally only?",
                "options": ["external", "internal"],
                "why_needed": "Determines security requirements and gateway capabilities needed"
            })
        
        if "auth_type" not in context:
            questions.append({
                "key": "auth_type",
                "question": "What type of authentication is used for this API?",
                "options": ["oauth", "mtls", "both", "none"],
                "why_needed": "Critical for security policy evaluation"
            })
        
        return questions
    
    def _get_potential_rules(self, decision_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get potential matching rules"""
        # This would evaluate which rules could match
        rules = self.policy_engine.rules
        
        potential = []
        for rule in rules:
            if self.policy_engine._matches_conditions(decision_input, rule.get("conditions", {})):
                potential.append({
                    "id": rule.get("id"),
                    "name": rule.get("name"),
                    "reason": rule.get("reason"),
                    "priority": rule.get("priority", 999)
                })
        
        return sorted(potential, key=lambda r: r["priority"])
    
    def _complete_with_error(self, message: str, session_id: str, trace_id: str) -> Dict[str, Any]:
        """Complete trace with error"""
        self.reasoning_engine.complete_trace(
            status="failure",
            summary=f"Error: {message}"
        )
        
        return {
            "status": "error",
            "message": message,
            "session_id": session_id,
            "trace_id": trace_id
        }
    
    def _request_user_input(
        self,
        observations: Dict[str, Any],
        session_id: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """Request user input"""
        return {
            "status": "needs_input",
            "message": "Additional information needed to complete reasoning",
            "questions": observations.get("missing_info", []),
            "observations": observations.get("findings", []),
            "session_id": session_id,
            "trace_id": trace_id
        }
    
    def _request_feedback_on_plan(
        self,
        action_plan: Dict[str, Any],
        session_id: str,
        trace_id: str
    ) -> Dict[str, Any]:
        """Request human feedback on action plan"""
        decision = action_plan["decision"]
        
        return {
            "status": "awaiting_feedback",
            "message": "Action plan ready. Please review and provide feedback.",
            "action_plan": {
                "action": "select_gateway" if decision["status"] != "escalation" else "escalate",
                "gateway": decision.get("gateway"),
                "reason": decision.get("reason"),
                "rule_id": decision.get("rule_id")
            },
            "reasoning_summary": self.reasoning_engine.get_reasoning_summary(),
            "session_id": session_id,
            "trace_id": trace_id,
            "feedback_options": {
                "approve": "Proceed with this gateway selection",
                "reject": "Reject and provide alternative",
                "suggest": "Suggest modifications"
            }
        }



