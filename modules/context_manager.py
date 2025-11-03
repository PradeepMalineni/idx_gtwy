"""
Context Manager
Manages session state and context across agent interactions
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context and state for gateway selection sessions"""
    
    def __init__(self):
        """Initialize context manager"""
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, project_dir: str) -> str:
        """
        Create a new session
        
        Args:
            project_dir: Project directory path
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            "session_id": session_id,
            "project_dir": project_dir,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        logger.info(f"Created session {session_id} for project {project_dir}")
        return session_id
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get context for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Context dictionary
        """
        context = self.sessions.get(session_id, {})
        
        if not context:
            logger.warning(f"Session not found: {session_id}")
        
        return context
    
    def update_context(self, session_id: str, updates: Dict[str, Any]) -> None:
        """
        Update context for a session
        
        Args:
            session_id: Session ID
            updates: Dictionary of updates to apply
        """
        if session_id not in self.sessions:
            logger.warning(f"Cannot update non-existent session: {session_id}")
            return
        
        self.sessions[session_id].update(updates)
        self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Updated session {session_id} with keys: {list(updates.keys())}")
    
    def close_session(self, session_id: str) -> None:
        """
        Close a session
        
        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "closed"
            self.sessions[session_id]["closed_at"] = datetime.utcnow().isoformat()
            logger.info(f"Closed session {session_id}")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Cleanup old sessions
        
        Args:
            max_age_hours: Maximum age of sessions to keep
            
        Returns:
            Number of sessions cleaned up
        """
        from datetime import timedelta
        
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=max_age_hours)
        
        sessions_to_remove = []
        for session_id, context in self.sessions.items():
            created_at = datetime.fromisoformat(context["created_at"])
            if created_at < cutoff:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
        return len(sessions_to_remove)
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all sessions
        
        Returns:
            Dictionary of all sessions
        """
        return self.sessions
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session exists, False otherwise
        """
        return session_id in self.sessions

