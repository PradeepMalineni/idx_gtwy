"""
PCI Data Detector
Uses LLM to detect presence of PCI/cardholder data in API specifications
"""

import logging
import json
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PCIDetector:
    """Detector for PCI/sensitive cardholder data using LLM inference"""
    
    # Static PCI-related field patterns (for fallback when LLM unavailable)
    PCI_FIELD_PATTERNS = [
        'cardnumber', 'card_number', 'pan', 'primaryaccountnumber',
        'cvv', 'cvv2', 'cvc', 'cvc2', 'securitycode', 'card_security_code',
        'expirydate', 'expiry_date', 'expiration', 'exp_date', 'expdate',
        'cardholder', 'card_holder', 'name_on_card', 'nameoncard',
        'track', 'track1', 'track2', 'magneticstripe', 'magnetic_stripe',
        'pin', 'pinblock', 'pin_block'
    ]
    
    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize PCI detector
        
        Args:
            llm_provider: LLM provider to use (openai, anthropic, etc.)
        """
        self.llm_provider = llm_provider
        self._llm_available = self._check_llm_availability()
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM is available and configured"""
        if self.llm_provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif self.llm_provider == "anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        return False
    
    async def analyze_oas_for_pci(self, oas_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze OAS for PCI/sensitive cardholder data
        
        Args:
            oas_spec: Parsed OpenAPI specification
            
        Returns:
            Dictionary with analysis results:
            {
                "has_pci": bool,
                "pci_fields": List[str],
                "confidence": float,
                "method": str
            }
        """
        logger.info("Analyzing OAS for PCI/sensitive data...")
        
        # Extract all fields and schemas
        all_fields = self._extract_all_fields_with_context(oas_spec)
        
        if not all_fields:
            logger.info("No fields found in OAS")
            return {
                "has_pci": False,
                "pci_fields": [],
                "confidence": 1.0,
                "method": "no_fields"
            }
        
        # Try LLM-based detection if available
        if self._llm_available:
            try:
                return await self._llm_based_detection(all_fields, oas_spec)
            except Exception as e:
                logger.warning(f"LLM detection failed, falling back to pattern matching: {str(e)}")
        
        # Fallback to pattern-based detection
        return self._pattern_based_detection(all_fields)
    
    def _extract_all_fields_with_context(self, oas_spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all fields with their context (descriptions, types, etc.)
        
        Args:
            oas_spec: Parsed OpenAPI specification
            
        Returns:
            List of field information dictionaries
        """
        fields = []
        
        # Extract from schemas
        schemas = oas_spec.get('components', {}).get('schemas', {})
        if not schemas:
            schemas = oas_spec.get('definitions', {})
        
        for schema_name, schema_def in schemas.items():
            if isinstance(schema_def, dict) and 'properties' in schema_def:
                for field_name, field_def in schema_def['properties'].items():
                    fields.append({
                        'name': field_name,
                        'schema': schema_name,
                        'type': field_def.get('type', 'unknown'),
                        'description': field_def.get('description', ''),
                        'format': field_def.get('format', ''),
                        'pattern': field_def.get('pattern', '')
                    })
        
        # Extract from path parameters
        paths = oas_spec.get('paths', {})
        for path, path_def in paths.items():
            if isinstance(path_def, dict):
                for method, method_def in path_def.items():
                    if isinstance(method_def, dict) and 'parameters' in method_def:
                        for param in method_def['parameters']:
                            if isinstance(param, dict) and 'name' in param:
                                fields.append({
                                    'name': param['name'],
                                    'schema': f"{path}:{method}",
                                    'type': param.get('type', param.get('schema', {}).get('type', 'unknown')),
                                    'description': param.get('description', ''),
                                    'in': param.get('in', 'unknown')
                                })
        
        return fields
    
    async def _llm_based_detection(self, fields: List[Dict[str, Any]], oas_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to detect PCI data (INFERENCE ONLY - not decision making)
        
        Args:
            fields: List of field information
            oas_spec: Full OAS specification
            
        Returns:
            Analysis results
        """
        logger.info("Using LLM for PCI detection...")
        
        # Prepare prompt for LLM
        prompt = self._build_pci_detection_prompt(fields, oas_spec)
        
        # Call LLM based on provider
        if self.llm_provider == "openai":
            result = await self._call_openai(prompt)
        elif self.llm_provider == "anthropic":
            result = await self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        
        logger.info(f"LLM detection complete: {result}")
        return result
    
    def _build_pci_detection_prompt(self, fields: List[Dict[str, Any]], oas_spec: Dict[str, Any]) -> str:
        """Build prompt for LLM PCI detection"""
        
        api_info = {
            'title': oas_spec.get('info', {}).get('title', 'Unknown API'),
            'description': oas_spec.get('info', {}).get('description', ''),
            'version': oas_spec.get('info', {}).get('version', 'Unknown')
        }
        
        fields_summary = []
        for field in fields[:50]:  # Limit to first 50 fields to avoid token limits
            fields_summary.append({
                'name': field['name'],
                'type': field['type'],
                'description': field['description'],
                'schema': field['schema']
            })
        
        prompt = f"""You are a security analyst specializing in PCI DSS compliance. Analyze the following API specification to determine if it handles PCI/cardholder data.

API Information:
- Title: {api_info['title']}
- Description: {api_info['description']}
- Version: {api_info['version']}

Fields in API:
{json.dumps(fields_summary, indent=2)}

PCI/Cardholder Data includes:
- Primary Account Number (PAN) / Card Number
- Cardholder Name
- Card Expiration Date
- CVV/CVC/Security Code
- Track Data
- PIN/PIN Block

Task: Analyze the field names, types, and descriptions to determine if this API handles PCI/cardholder data.

Respond ONLY with a valid JSON object in this exact format:
{{
    "has_pci": true or false,
    "pci_fields": ["field1", "field2", ...],
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

Do not include any other text before or after the JSON."""

        return prompt
    
    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API for PCI detection"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a PCI DSS security analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            return {
                "has_pci": result.get("has_pci", False),
                "pci_fields": result.get("pci_fields", []),
                "confidence": result.get("confidence", 0.5),
                "method": "llm_openai",
                "reasoning": result.get("reasoning", "")
            }
            
        except ImportError:
            logger.error("OpenAI package not installed. Run: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise
    
    async def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Call Anthropic API for PCI detection"""
        try:
            import anthropic
            
            client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = message.content[0].text
            result = json.loads(result_text)
            
            return {
                "has_pci": result.get("has_pci", False),
                "pci_fields": result.get("pci_fields", []),
                "confidence": result.get("confidence", 0.5),
                "method": "llm_anthropic",
                "reasoning": result.get("reasoning", "")
            }
            
        except ImportError:
            logger.error("Anthropic package not installed. Run: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise
    
    def _pattern_based_detection(self, fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Fallback pattern-based PCI detection
        
        Args:
            fields: List of field information
            
        Returns:
            Analysis results
        """
        logger.info("Using pattern-based PCI detection (fallback)...")
        
        detected_fields = []
        
        for field in fields:
            field_name_lower = field['name'].lower().replace('-', '').replace('_', '')
            
            for pattern in self.PCI_FIELD_PATTERNS:
                pattern_normalized = pattern.replace('-', '').replace('_', '')
                if pattern_normalized in field_name_lower:
                    detected_fields.append(field['name'])
                    break
        
        has_pci = len(detected_fields) > 0
        
        # Calculate confidence based on number of matches
        confidence = 0.7 if has_pci else 0.8  # Lower confidence for pattern matching
        
        logger.info(f"Pattern-based detection: has_pci={has_pci}, fields={detected_fields}")
        
        return {
            "has_pci": has_pci,
            "pci_fields": detected_fields,
            "confidence": confidence,
            "method": "pattern_based"
        }

