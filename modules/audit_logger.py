"""
Audit Logger
Logs all gateway selection decisions for traceability and governance
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logger for gateway selection decisions"""
    
    def __init__(self, log_dir: str = None):
        """
        Initialize audit logger
        
        Args:
            log_dir: Directory to store audit logs
        """
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / ".gateway-governance" / "audit-logs"
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "gateway-decisions.jsonl"
        
        logger.info(f"Audit logger initialized: {self.log_file}")
    
    async def log_decision(
        self,
        session_id: str,
        project_dir: str,
        decision: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """
        Log a gateway selection decision
        
        Args:
            session_id: Session ID
            project_dir: Project directory
            decision: Decision details
            context: Full context of the decision
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Build audit entry
        audit_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "project_dir": project_dir,
            "decision": {
                "status": decision.get("status"),
                "gateway": decision.get("gateway"),
                "reason": decision.get("reason"),
                "rule_id": decision.get("rule_id"),
                "rule_name": decision.get("rule_name")
            },
            "context": {
                "pci_detected": context.get("pci_detected"),
                "pci_fields": context.get("pci_fields", []),
                "pci_confidence": context.get("pci_confidence"),
                "api_exposure": context.get("api_exposure"),
                "auth_type": context.get("auth_type"),
                "oas_file": context.get("oas_file")
            },
            "metadata": {
                "oas_file": context.get("oas_file"),
                "config_source": context.get("config_source"),
                "deployment_triggered": "deployment" in decision
            }
        }
        
        # Write to JSONL file (one JSON object per line)
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
            
            logger.info(f"Logged decision for session {session_id}: {decision.get('gateway')}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
    
    async def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent audit log entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries
        """
        if not self.log_file.exists():
            return []
        
        try:
            entries = []
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            
            # Get last N lines
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in audit log: {str(e)}")
            
            # Reverse to show most recent first
            entries.reverse()
            
            return entries
        except Exception as e:
            logger.error(f"Failed to read audit log: {str(e)}")
            return []
    
    async def get_logs_for_project(self, project_dir: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get audit logs for a specific project
        
        Args:
            project_dir: Project directory
            limit: Maximum number of entries to return
            
        Returns:
            List of audit log entries for the project
        """
        if not self.log_file.exists():
            return []
        
        try:
            entries = []
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("project_dir") == project_dir:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Return last N entries, most recent first
            entries.reverse()
            return entries[:limit]
        except Exception as e:
            logger.error(f"Failed to read audit log: {str(e)}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics
        
        Returns:
            Statistics about gateway decisions
        """
        if not self.log_file.exists():
            return {
                "total_decisions": 0,
                "gateways": {},
                "escalations": 0,
                "pci_detected_count": 0
            }
        
        try:
            total = 0
            gateways = {}
            escalations = 0
            pci_detected = 0
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        total += 1
                        
                        decision = entry.get("decision", {})
                        if decision.get("status") == "escalation":
                            escalations += 1
                        
                        gateway = decision.get("gateway")
                        if gateway:
                            gateways[gateway] = gateways.get(gateway, 0) + 1
                        
                        if entry.get("context", {}).get("pci_detected"):
                            pci_detected += 1
                    except json.JSONDecodeError:
                        continue
            
            return {
                "total_decisions": total,
                "gateways": gateways,
                "escalations": escalations,
                "pci_detected_count": pci_detected,
                "log_file": str(self.log_file)
            }
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {str(e)}")
            return {"error": str(e)}
    
    def export_logs(self, output_file: str, format: str = "json") -> bool:
        """
        Export audit logs to a file
        
        Args:
            output_file: Output file path
            format: Export format ("json" or "csv")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.log_file.exists():
            logger.warning("No audit logs to export")
            return False
        
        try:
            if format == "json":
                self._export_json(output_file)
            elif format == "csv":
                self._export_csv(output_file)
            else:
                logger.error(f"Unsupported export format: {format}")
                return False
            
            logger.info(f"Exported audit logs to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export logs: {str(e)}")
            return False
    
    def _export_json(self, output_file: str) -> None:
        """Export logs as JSON array"""
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        with open(output_file, 'w') as f:
            json.dump(entries, f, indent=2)
    
    def _export_csv(self, output_file: str) -> None:
        """Export logs as CSV"""
        import csv
        
        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        
        if not entries:
            return
        
        # Define CSV columns
        fieldnames = [
            "timestamp", "session_id", "project_dir",
            "status", "gateway", "reason", "rule_id",
            "pci_detected", "api_exposure", "auth_type"
        ]
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in entries:
                row = {
                    "timestamp": entry.get("timestamp"),
                    "session_id": entry.get("session_id"),
                    "project_dir": entry.get("project_dir"),
                    "status": entry.get("decision", {}).get("status"),
                    "gateway": entry.get("decision", {}).get("gateway"),
                    "reason": entry.get("decision", {}).get("reason"),
                    "rule_id": entry.get("decision", {}).get("rule_id"),
                    "pci_detected": entry.get("context", {}).get("pci_detected"),
                    "api_exposure": entry.get("context", {}).get("api_exposure"),
                    "auth_type": entry.get("context", {}).get("auth_type")
                }
                writer.writerow(row)

