"""
OpenAPI Specification Parser
Handles detection and parsing of OAS files
"""

import json
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OASParser:
    """Parser for OpenAPI Specification files"""
    
    OAS_EXTENSIONS = ['.yaml', '.yml', '.json']
    OAS_FILENAMES = [
        'openapi.yaml', 'openapi.yml', 'openapi.json',
        'api.yaml', 'api.yml', 'api.json',
        'swagger.yaml', 'swagger.yml', 'swagger.json'
    ]
    
    def find_oas_file(self, project_path: Path) -> Optional[Path]:
        """
        Search for OpenAPI Specification file in project directory
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Path to OAS file if found, None otherwise
        """
        if not project_path.exists():
            logger.warning(f"Project path does not exist: {project_path}")
            return None
        
        # First, check for common OAS filenames
        for filename in self.OAS_FILENAMES:
            oas_path = project_path / filename
            if oas_path.exists() and self._is_valid_oas(oas_path):
                logger.info(f"Found OAS file: {oas_path}")
                return oas_path
        
        # Search for any file with OAS extension
        for ext in self.OAS_EXTENSIONS:
            for oas_file in project_path.glob(f"*{ext}"):
                if self._is_valid_oas(oas_file):
                    logger.info(f"Found OAS file: {oas_file}")
                    return oas_file
        
        # Search in common subdirectories
        for subdir in ['api', 'specs', 'swagger', 'openapi', 'docs']:
            subdir_path = project_path / subdir
            if subdir_path.exists():
                for ext in self.OAS_EXTENSIONS:
                    for oas_file in subdir_path.glob(f"*{ext}"):
                        if self._is_valid_oas(oas_file):
                            logger.info(f"Found OAS file: {oas_file}")
                            return oas_file
        
        logger.warning(f"No valid OAS file found in {project_path}")
        return None
    
    def _is_valid_oas(self, file_path: Path) -> bool:
        """
        Check if file is a valid OpenAPI Specification
        
        Args:
            file_path: Path to potential OAS file
            
        Returns:
            True if valid OAS, False otherwise
        """
        try:
            spec = self.parse_oas_file(file_path)
            return spec is not None and 'openapi' in spec
        except Exception as e:
            logger.debug(f"File {file_path} is not a valid OAS: {str(e)}")
            return False
    
    def parse_oas_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse OpenAPI Specification file
        
        Args:
            file_path: Path to OAS file
            
        Returns:
            Parsed OAS as dictionary, or None if invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                elif file_path.suffix == '.json':
                    spec = json.load(f)
                else:
                    logger.error(f"Unsupported file extension: {file_path.suffix}")
                    return None
            
            # Validate it's an OAS file
            if not isinstance(spec, dict):
                logger.error(f"OAS file is not a dictionary: {file_path}")
                return None
            
            if 'openapi' not in spec and 'swagger' not in spec:
                logger.error(f"Missing 'openapi' or 'swagger' field in {file_path}")
                return None
            
            # Normalize swagger to openapi
            if 'swagger' in spec and 'openapi' not in spec:
                spec['openapi'] = '2.0'
            
            logger.info(f"Successfully parsed OAS file: {file_path}")
            return spec
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing OAS file {file_path}: {str(e)}")
            return None
    
    def extract_schemas(self, oas_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract schema definitions from OAS
        
        Args:
            oas_spec: Parsed OAS specification
            
        Returns:
            Dictionary of schemas
        """
        schemas = {}
        
        # OpenAPI 3.x
        if 'components' in oas_spec and 'schemas' in oas_spec['components']:
            schemas.update(oas_spec['components']['schemas'])
        
        # Swagger 2.0
        if 'definitions' in oas_spec:
            schemas.update(oas_spec['definitions'])
        
        return schemas
    
    def extract_paths(self, oas_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract API paths from OAS
        
        Args:
            oas_spec: Parsed OAS specification
            
        Returns:
            Dictionary of paths
        """
        return oas_spec.get('paths', {})
    
    def extract_all_fields(self, oas_spec: Dict[str, Any]) -> list[str]:
        """
        Extract all field names from schemas and paths
        
        Args:
            oas_spec: Parsed OAS specification
            
        Returns:
            List of all field names
        """
        fields = []
        
        # Extract from schemas
        schemas = self.extract_schemas(oas_spec)
        for schema_name, schema_def in schemas.items():
            if isinstance(schema_def, dict) and 'properties' in schema_def:
                fields.extend(schema_def['properties'].keys())
        
        # Extract from path parameters
        paths = self.extract_paths(oas_spec)
        for path, path_def in paths.items():
            if isinstance(path_def, dict):
                for method, method_def in path_def.items():
                    if isinstance(method_def, dict):
                        # Parameters
                        if 'parameters' in method_def:
                            for param in method_def['parameters']:
                                if isinstance(param, dict) and 'name' in param:
                                    fields.append(param['name'])
                        
                        # Request body
                        if 'requestBody' in method_def:
                            req_body = method_def['requestBody']
                            if isinstance(req_body, dict) and 'content' in req_body:
                                for content_type, content_def in req_body['content'].items():
                                    if 'schema' in content_def and 'properties' in content_def['schema']:
                                        fields.extend(content_def['schema']['properties'].keys())
        
        return list(set(fields))  # Remove duplicates

