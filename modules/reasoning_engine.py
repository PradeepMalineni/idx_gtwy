"""
Reasoning Engine
Manages reasoning traces, stores them externally, and provides explainability
Part of the ReAct (Reasoning + Acting) framework
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Manages reasoning traces for transparent decision-making
    Stores all reasoning externally in JSON files for auditability
    """
    
    def __init__(self, reasoning_store_dir: Optional[str] = None):
        """
        Initialize reasoning engine
        
        Args:
            reasoning_store_dir: Directory to store reasoning traces
        """
        if reasoning_store_dir:
            self.store_dir = Path(reasoning_store_dir)
        else:
            self.store_dir = Path.home() / ".gateway-governance" / "reasoning-store"
        
        self.store_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Reasoning store initialized: {self.store_dir}")
        
        # Current reasoning trace
        self.current_trace: Optional[Dict[str, Any]] = None
    
    def start_reasoning_trace(self, session_id: str, task: str) -> str:
        """
        Start a new reasoning trace
        
        Args:
            session_id: Session identifier
            task: Description of the task
            
        Returns:
            Trace ID
        """
        trace_id = str(uuid.uuid4())
        
        self.current_trace = {
            "trace_id": trace_id,
            "session_id": session_id,
            "task": task,
            "started_at": datetime.utcnow().isoformat(),
            "status": "in_progress",
            "steps": [],
            "observations": [],
            "thoughts": [],
            "actions": [],
            "feedback": []
        }
        
        logger.info(f"Started reasoning trace: {trace_id} for task: {task}")
        return trace_id
    
    def add_observation(self, observation: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an observation (Sense phase)
        
        Args:
            observation: What was observed
            data: Associated data
        """
        if not self.current_trace:
            logger.warning("No active trace; starting one")
            self.start_reasoning_trace("unknown", "Unknown task")
        
        obs_entry = {
            "step": len(self.current_trace["steps"]) + 1,
            "type": "observation",
            "timestamp": datetime.utcnow().isoformat(),
            "observation": observation,
            "data": data or {}
        }
        
        self.current_trace["observations"].append(obs_entry)
        self.current_trace["steps"].append(obs_entry)
        
        logger.info(f"Observation: {observation}")
    
    def add_thought(
        self,
        thought: str,
        reasoning: str,
        confidence: float,
        alternatives_considered: Optional[List[str]] = None
    ) -> None:
        """
        Add a thought/reasoning step (Think phase)
        
        Args:
            thought: Summary of the thought
            reasoning: Detailed reasoning
            confidence: Confidence level (0.0-1.0)
            alternatives_considered: Alternative approaches considered
        """
        if not self.current_trace:
            logger.warning("No active trace")
            return
        
        thought_entry = {
            "step": len(self.current_trace["steps"]) + 1,
            "type": "thought",
            "timestamp": datetime.utcnow().isoformat(),
            "thought": thought,
            "reasoning": reasoning,
            "confidence": confidence,
            "alternatives_considered": alternatives_considered or [],
            "context_used": self._get_relevant_context()
        }
        
        self.current_trace["thoughts"].append(thought_entry)
        self.current_trace["steps"].append(thought_entry)
        
        logger.info(f"Thought: {thought} (confidence: {confidence})")
    
    def add_action(
        self,
        action: str,
        parameters: Dict[str, Any],
        expected_outcome: str,
        why_this_action: str
    ) -> str:
        """
        Add an action to be executed (Act phase)
        
        Args:
            action: Action name
            parameters: Action parameters
            expected_outcome: What we expect to happen
            why_this_action: Reasoning for this action
            
        Returns:
            Action ID
        """
        if not self.current_trace:
            logger.warning("No active trace")
            return "no-trace"
        
        action_id = str(uuid.uuid4())[:8]
        
        action_entry = {
            "step": len(self.current_trace["steps"]) + 1,
            "type": "action",
            "action_id": action_id,
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "parameters": parameters,
            "expected_outcome": expected_outcome,
            "why_this_action": why_this_action,
            "status": "pending",
            "result": None
        }
        
        self.current_trace["actions"].append(action_entry)
        self.current_trace["steps"].append(action_entry)
        
        logger.info(f"Action planned: {action} (ID: {action_id})")
        return action_id
    
    def record_action_result(
        self,
        action_id: str,
        status: str,
        result: Dict[str, Any],
        outcome_matches_expected: bool
    ) -> None:
        """
        Record the result of an executed action
        
        Args:
            action_id: Action identifier
            status: Execution status
            result: Action result
            outcome_matches_expected: Whether outcome matched expectations
        """
        if not self.current_trace:
            return
        
        # Find and update the action
        for action in self.current_trace["actions"]:
            if action.get("action_id") == action_id:
                action["status"] = status
                action["result"] = result
                action["outcome_matches_expected"] = outcome_matches_expected
                action["completed_at"] = datetime.utcnow().isoformat()
                break
        
        # Also update in steps
        for step in self.current_trace["steps"]:
            if step.get("type") == "action" and step.get("action_id") == action_id:
                step["status"] = status
                step["result"] = result
                step["outcome_matches_expected"] = outcome_matches_expected
                step["completed_at"] = datetime.utcnow().isoformat()
                break
    
    def add_self_reflection(
        self,
        reflection: str,
        learned: str,
        should_adjust: bool,
        adjustment: Optional[str] = None
    ) -> None:
        """
        Add self-reflection (internal feedback)
        
        Args:
            reflection: What the system reflects on
            learned: What was learned
            should_adjust: Whether to adjust approach
            adjustment: How to adjust
        """
        if not self.current_trace:
            return
        
        reflection_entry = {
            "step": len(self.current_trace["steps"]) + 1,
            "type": "self_reflection",
            "timestamp": datetime.utcnow().isoformat(),
            "reflection": reflection,
            "learned": learned,
            "should_adjust": should_adjust,
            "adjustment": adjustment
        }
        
        self.current_trace["steps"].append(reflection_entry)
        
        logger.info(f"Self-reflection: {reflection}")
    
    def add_human_feedback(
        self,
        feedback_type: str,
        feedback: str,
        rating: Optional[float] = None,
        corrections: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add human feedback (RLHF)
        
        Args:
            feedback_type: Type of feedback (approval, correction, suggestion)
            feedback: Feedback text
            rating: Rating (0.0-1.0)
            corrections: Corrections to apply
        """
        if not self.current_trace:
            return
        
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": feedback_type,
            "feedback": feedback,
            "rating": rating,
            "corrections": corrections or {}
        }
        
        self.current_trace["feedback"].append(feedback_entry)
        
        logger.info(f"Human feedback ({feedback_type}): {feedback}")
    
    def complete_trace(self, status: str, summary: str) -> str:
        """
        Complete the reasoning trace and save to disk
        
        Args:
            status: Final status (success, failure, partial)
            summary: Summary of the trace
            
        Returns:
            Path to saved trace file
        """
        if not self.current_trace:
            logger.warning("No active trace to complete")
            return ""
        
        self.current_trace["status"] = status
        self.current_trace["completed_at"] = datetime.utcnow().isoformat()
        self.current_trace["summary"] = summary
        
        # Calculate metrics
        self.current_trace["metrics"] = self._calculate_metrics()
        
        # Save to disk
        trace_file = self.store_dir / f"{self.current_trace['trace_id']}.json"
        with open(trace_file, 'w') as f:
            json.dump(self.current_trace, f, indent=2)
        
        logger.info(f"Reasoning trace completed and saved: {trace_file}")
        
        # Reset current trace
        trace_id = self.current_trace["trace_id"]
        self.current_trace = None
        
        return str(trace_file)
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current reasoning trace
        
        Returns:
            Summary dictionary
        """
        if not self.current_trace:
            return {"error": "No active reasoning trace"}
        
        return {
            "trace_id": self.current_trace["trace_id"],
            "task": self.current_trace["task"],
            "total_steps": len(self.current_trace["steps"]),
            "observations": len(self.current_trace["observations"]),
            "thoughts": len(self.current_trace["thoughts"]),
            "actions": len(self.current_trace["actions"]),
            "feedback_count": len(self.current_trace["feedback"]),
            "last_step": self.current_trace["steps"][-1] if self.current_trace["steps"] else None
        }
    
    def get_action_plan(self) -> List[Dict[str, Any]]:
        """
        Get the planned actions that are pending
        
        Returns:
            List of pending actions
        """
        if not self.current_trace:
            return []
        
        return [
            action for action in self.current_trace["actions"]
            if action["status"] == "pending"
        ]
    
    def load_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved reasoning trace
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Trace data or None
        """
        trace_file = self.store_dir / f"{trace_id}.json"
        
        if not trace_file.exists():
            logger.warning(f"Trace not found: {trace_id}")
            return None
        
        try:
            with open(trace_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load trace {trace_id}: {str(e)}")
            return None
    
    def search_traces(
        self,
        task_pattern: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search reasoning traces
        
        Args:
            task_pattern: Task pattern to match
            status: Status filter
            limit: Maximum results
            
        Returns:
            List of matching traces
        """
        traces = []
        
        for trace_file in sorted(self.store_dir.glob("*.json"), reverse=True):
            if len(traces) >= limit:
                break
            
            try:
                with open(trace_file, 'r') as f:
                    trace = json.load(f)
                
                # Apply filters
                if task_pattern and task_pattern.lower() not in trace.get("task", "").lower():
                    continue
                
                if status and trace.get("status") != status:
                    continue
                
                traces.append({
                    "trace_id": trace["trace_id"],
                    "task": trace["task"],
                    "status": trace["status"],
                    "started_at": trace["started_at"],
                    "completed_at": trace.get("completed_at"),
                    "steps_count": len(trace.get("steps", [])),
                    "feedback_count": len(trace.get("feedback", []))
                })
            except Exception as e:
                logger.error(f"Failed to read trace {trace_file}: {str(e)}")
        
        return traces
    
    def _get_relevant_context(self) -> Dict[str, Any]:
        """Get relevant context from current trace"""
        if not self.current_trace:
            return {}
        
        return {
            "recent_observations": self.current_trace["observations"][-3:],
            "recent_thoughts": self.current_trace["thoughts"][-2:],
            "pending_actions": [a for a in self.current_trace["actions"] if a["status"] == "pending"]
        }
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for the trace"""
        if not self.current_trace:
            return {}
        
        total_actions = len(self.current_trace["actions"])
        successful_actions = sum(
            1 for a in self.current_trace["actions"]
            if a.get("status") == "completed" and a.get("outcome_matches_expected", False)
        )
        
        avg_confidence = 0.0
        if self.current_trace["thoughts"]:
            avg_confidence = sum(t["confidence"] for t in self.current_trace["thoughts"]) / len(self.current_trace["thoughts"])
        
        return {
            "total_steps": len(self.current_trace["steps"]),
            "total_observations": len(self.current_trace["observations"]),
            "total_thoughts": len(self.current_trace["thoughts"]),
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "success_rate": successful_actions / total_actions if total_actions > 0 else 0.0,
            "average_confidence": avg_confidence,
            "feedback_provided": len(self.current_trace["feedback"]) > 0,
            "human_rating": self._get_average_human_rating()
        }
    
    def _get_average_human_rating(self) -> Optional[float]:
        """Get average human rating from feedback"""
        if not self.current_trace:
            return None
        
        ratings = [f["rating"] for f in self.current_trace["feedback"] if f.get("rating") is not None]
        
        if not ratings:
            return None
        
        return sum(ratings) / len(ratings)



