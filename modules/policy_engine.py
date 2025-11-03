"""
Policy Rule Engine
Static, auditable rule engine for gateway selection decisions
NEVER uses LLM - only static policy rules
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PolicyEngine:
    """Static policy-based rule engine for gateway selection"""
    
    def __init__(self, policy_file: Optional[str] = None):
        """
        Initialize policy engine
        
        Args:
            policy_file: Path to policy YAML file (optional)
        """
        self.policy_file = policy_file or self._get_default_policy_file()
        self.rules = self._load_policy_rules()
    
    def _get_default_policy_file(self) -> str:
        """Get default policy file path"""
        return str(Path(__file__).parent.parent / "config" / "gateway-policy.yaml")
    
    def _load_policy_rules(self) -> list[Dict[str, Any]]:
        """
        Load policy rules from YAML file
        
        Returns:
            List of policy rules
        """
        policy_path = Path(self.policy_file)
        
        if not policy_path.exists():
            logger.warning(f"Policy file not found: {self.policy_file}, using default rules")
            return self._get_default_rules()
        
        try:
            with open(policy_path, 'r') as f:
                policy_config = yaml.safe_load(f)
            
            rules = policy_config.get('rules', [])
            logger.info(f"Loaded {len(rules)} policy rules from {self.policy_file}")
            return rules
            
        except Exception as e:
            logger.error(f"Error loading policy file: {str(e)}, using default rules")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> list[Dict[str, Any]]:
        """
        Get default hardcoded policy rules
        
        Returns:
            List of default policy rules
        """
        return [
            {
                "id": "rule_001",
                "name": "External PCI without Security - Escalate",
                "priority": 1,
                "conditions": {
                    "api_exposure": "external",
                    "has_pci": True,
                    "auth_type": "none"
                },
                "action": "escalate",
                "escalation_email": "ESGADEV@team.com",
                "reason": "External API with PCI data but no authentication - security escalation required"
            },
            {
                "id": "rule_002",
                "name": "External PCI with OAuth/mTLS - DataPower",
                "priority": 2,
                "conditions": {
                    "api_exposure": "external",
                    "has_pci": True,
                    "auth_type": ["oauth", "mtls", "both"]
                },
                "action": "route",
                "gateway": "datapower",
                "reason": "External API with PCI data and strong authentication → DataPower (PCI DSS compliant gateway)"
            },
            {
                "id": "rule_003",
                "name": "Internal PCI - DataPower",
                "priority": 3,
                "conditions": {
                    "api_exposure": "internal",
                    "has_pci": True
                },
                "action": "route",
                "gateway": "datapower",
                "reason": "Internal API with PCI data → DataPower (required for PCI compliance)"
            },
            {
                "id": "rule_004",
                "name": "External without PCI - Apigee",
                "priority": 4,
                "conditions": {
                    "api_exposure": "external",
                    "has_pci": False
                },
                "action": "route",
                "gateway": "apigee",
                "reason": "External API without PCI data → Apigee (modern cloud gateway)"
            },
            {
                "id": "rule_005",
                "name": "Internal without PCI - Apigee",
                "priority": 5,
                "conditions": {
                    "api_exposure": "internal",
                    "has_pci": False
                },
                "action": "route",
                "gateway": "apigee",
                "reason": "Internal API without PCI data → Apigee (lightweight option)"
            },
            {
                "id": "rule_default",
                "name": "Default - Apigee",
                "priority": 999,
                "conditions": {},
                "action": "route",
                "gateway": "apigee",
                "reason": "Default routing to Apigee (no specific conditions matched)"
            }
        ]
    
    def evaluate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate input against policy rules and return decision
        
        This method uses ONLY static rule matching - NO LLM involvement
        
        Args:
            input_data: Dictionary containing:
                - has_pci: bool
                - api_exposure: "external" or "internal"
                - auth_type: "oauth", "mtls", "both", or "none"
                
        Returns:
            Dictionary containing:
                - status: "success" or "escalation"
                - gateway: "apigee" or "datapower" (if routed)
                - reason: explanation of decision
                - rule_id: ID of matched rule
        """
        logger.info(f"Evaluating policy rules for input: {input_data}")
        
        # Sort rules by priority
        sorted_rules = sorted(self.rules, key=lambda r: r.get('priority', 999))
        
        # Evaluate rules in priority order
        for rule in sorted_rules:
            if self._matches_conditions(input_data, rule['conditions']):
                logger.info(f"Matched rule: {rule['id']} - {rule['name']}")
                return self._build_decision(rule, input_data)
        
        # This should never happen if there's a default rule
        logger.warning("No rules matched, using hardcoded default")
        return {
            "status": "success",
            "gateway": "apigee",
            "reason": "No matching rules - defaulting to Apigee",
            "rule_id": "hardcoded_default"
        }
    
    def _matches_conditions(self, input_data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """
        Check if input data matches rule conditions
        
        Args:
            input_data: Input data to check
            conditions: Rule conditions
            
        Returns:
            True if all conditions match, False otherwise
        """
        # Empty conditions match everything (default rule)
        if not conditions:
            return True
        
        for key, expected_value in conditions.items():
            actual_value = input_data.get(key)
            
            # Handle list of acceptable values
            if isinstance(expected_value, list):
                if actual_value not in expected_value:
                    return False
            else:
                if actual_value != expected_value:
                    return False
        
        return True
    
    def _build_decision(self, rule: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build decision response from matched rule
        
        Args:
            rule: Matched rule
            input_data: Original input data
            
        Returns:
            Decision dictionary
        """
        action = rule.get('action', 'route')
        
        if action == 'escalate':
            return {
                "status": "escalation",
                "escalation_email": rule.get('escalation_email', 'ESGADEV@team.com'),
                "reason": rule.get('reason', 'Security escalation required'),
                "rule_id": rule.get('id'),
                "rule_name": rule.get('name'),
                "input_data": input_data,
                "message": f"🚨 Security Escalation Required: {rule.get('reason')}\nPlease contact {rule.get('escalation_email')}"
            }
        else:  # action == 'route'
            gateway = rule.get('gateway', 'apigee')
            return {
                "status": "success",
                "gateway": gateway,
                "reason": rule.get('reason', f'Routing to {gateway}'),
                "rule_id": rule.get('id'),
                "rule_name": rule.get('name'),
                "input_data": input_data,
                "message": f"✅ Gateway Selected: {gateway.upper()}\nReason: {rule.get('reason')}"
            }
    
    def validate_policy(self) -> Dict[str, Any]:
        """
        Validate policy configuration
        
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        # Check for default rule
        has_default = any(not rule.get('conditions') for rule in self.rules)
        if not has_default:
            warnings.append("No default rule found (empty conditions)")
        
        # Check for duplicate priorities
        priorities = [rule.get('priority', 999) for rule in self.rules]
        if len(priorities) != len(set(priorities)):
            warnings.append("Duplicate priorities found in rules")
        
        # Validate each rule
        for i, rule in enumerate(self.rules):
            rule_id = rule.get('id', f'rule_{i}')
            
            if 'action' not in rule:
                errors.append(f"Rule {rule_id}: Missing 'action' field")
            
            action = rule.get('action')
            if action == 'route' and 'gateway' not in rule:
                errors.append(f"Rule {rule_id}: Missing 'gateway' for route action")
            
            if action == 'escalate' and 'escalation_email' not in rule:
                warnings.append(f"Rule {rule_id}: Missing 'escalation_email' for escalate action")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "rules_count": len(self.rules)
        }

