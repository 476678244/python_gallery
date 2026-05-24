"""Audit logging system for SafeClaw"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

# Configure logger for this module
logger = logging.getLogger(__name__)

class AuditLevel(Enum):
    """Audit log levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AuditEvent:
    """Audit event entry"""
    
    def __init__(self, level: AuditLevel, event_type: str, message: str, 
                 session_id: str, metadata: Dict[str, Any] = None):
        self.timestamp = datetime.now()
        self.level = level
        self.event_type = event_type
        self.message = message
        self.session_id = session_id
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "event_type": self.event_type,
            "message": self.message,
            "session_id": self.session_id,
            "metadata": self.metadata
        }

class AuditLogger:
    """Audit logging system"""
    
    def __init__(self, log_file: Optional[Path] = None, max_entries: int = 10000):
        self.log_file = log_file
        self.max_entries = max_entries
        self.events: List[AuditEvent] = []
        
        # Set up file logging if path provided
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Audit logger initialized with max {max_entries} entries")
    
    def log(self, level: AuditLevel, event_type: str, message: str, 
             session_id: str, metadata: Dict[str, Any] = None):
        """Log an audit event"""
        event = AuditEvent(level, event_type, message, session_id, metadata)
        self.events.append(event)
        
        # Trim if exceeding max entries
        if len(self.events) > self.max_entries:
            self.events = self.events[-self.max_entries:]
        
        # Write to file if configured
        if self.log_file:
            self._write_to_file(event)
        
        # Log to standard logger
        log_message = f"[{event_type}] {message}"
        if level == AuditLevel.INFO:
            logger.info(log_message)
        elif level == AuditLevel.WARNING:
            logger.warning(log_message)
        elif level == AuditLevel.ERROR:
            logger.error(log_message)
        elif level == AuditLevel.CRITICAL:
            logger.critical(log_message)
    
    def log_safety_check(self, session_id: str, user_input: str, 
                        safety_result: Dict[str, Any]):
        """Log safety check result"""
        level = AuditLevel.CRITICAL if not safety_result["safe"] else AuditLevel.WARNING if safety_result["requires_confirmation"] else AuditLevel.INFO
        
        self.log(
            level=level,
            event_type="safety_check",
            message=f"Safety check for user input: {'BLOCKED' if not safety_result['safe'] else 'CONFIRMATION' if safety_result['requires_confirmation'] else 'SAFE'}",
            session_id=session_id,
            metadata={
                "user_input": user_input[:200] + "..." if len(user_input) > 200 else user_input,
                "safe": safety_result["safe"],
                "risk_level": safety_result["risk_level"],
                "warnings": safety_result["warnings"],
                "requires_confirmation": safety_result["requires_confirmation"]
            }
        )
    
    def log_tool_call(self, session_id: str, tool_name: str, tool_args: Dict[str, Any],
                      safety_result: Dict[str, Any]):
        """Log tool call"""
        level = AuditLevel.CRITICAL if not safety_result["safe"] else AuditLevel.WARNING if safety_result["requires_confirmation"] else AuditLevel.INFO
        
        self.log(
            level=level,
            event_type="tool_call",
            message=f"Tool call: {tool_name} - {'BLOCKED' if not safety_result['safe'] else 'CONFIRMATION' if safety_result['requires_confirmation'] else 'SAFE'}",
            session_id=session_id,
            metadata={
                "tool_name": tool_name,
                "tool_args": tool_args,
                "safe": safety_result["safe"],
                "risk_level": safety_result["risk_level"],
                "warnings": safety_result["warnings"]
            }
        )
    
    def log_memory_operation(self, session_id: str, operation: str, memory_id: str,
                            details: Dict[str, Any] = None):
        """Log memory operation"""
        self.log(
            level=AuditLevel.INFO,
            event_type="memory_operation",
            message=f"Memory operation: {operation}",
            session_id=session_id,
            metadata={
                "operation": operation,
                "memory_id": memory_id,
                "details": details or {}
            }
        )
    
    def log_agent_execution(self, session_id: str, agent_name: str, 
                           execution_path: List[str], processing_time: float):
        """Log agent execution"""
        self.log(
            level=AuditLevel.INFO,
            event_type="agent_execution",
            message=f"Agent executed: {agent_name}",
            session_id=session_id,
            metadata={
                "agent_name": agent_name,
                "execution_path": execution_path,
                "processing_time": processing_time
            }
        )
    
    def log_error(self, session_id: str, error_type: str, error_message: str,
                  context: Dict[str, Any] = None):
        """Log error event"""
        self.log(
            level=AuditLevel.ERROR,
            event_type="error",
            message=f"Error: {error_type} - {error_message}",
            session_id=session_id,
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
        )
    
    def log_security_event(self, session_id: str, event_type: str, description: str,
                           severity: str, details: Dict[str, Any] = None):
        """Log security event"""
        level = AuditLevel.CRITICAL if severity == "critical" else AuditLevel.ERROR if severity == "high" else AuditLevel.WARNING
        
        self.log(
            level=level,
            event_type="security_event",
            message=f"Security event: {event_type} - {description}",
            session_id=session_id,
            metadata={
                "security_event_type": event_type,
                "description": description,
                "severity": severity,
                "details": details or {}
            }
        )
    
    def get_events(self, session_id: Optional[str] = None, level: Optional[AuditLevel] = None,
                   event_type: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
        """Get filtered audit events"""
        filtered_events = self.events
        
        # Apply filters
        if session_id:
            filtered_events = [e for e in filtered_events if e.session_id == session_id]
        
        if level:
            filtered_events = [e for e in filtered_events if e.level == level]
        
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]
        
        # Return most recent events
        return filtered_events[-limit:]
    
    def get_events_by_time_range(self, start_time: datetime, end_time: datetime) -> List[AuditEvent]:
        """Get events within time range"""
        return [e for e in self.events if start_time <= e.timestamp <= end_time]
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary for a specific session"""
        session_events = [e for e in self.events if e.session_id == session_id]
        
        if not session_events:
            return {"session_id": session_id, "event_count": 0}
        
        # Count by level
        level_counts = {}
        for level in AuditLevel:
            level_counts[level.value] = sum(1 for e in session_events if e.level == level)
        
        # Count by event type
        event_type_counts = {}
        for event in session_events:
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        
        # Time range
        timestamps = [e.timestamp for e in session_events]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        return {
            "session_id": session_id,
            "event_count": len(session_events),
            "level_distribution": level_counts,
            "event_type_distribution": event_type_counts,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        if not self.events:
            return {"total_events": 0}
        
        # Count by level
        level_counts = {}
        for level in AuditLevel:
            level_counts[level.value] = sum(1 for e in self.events if e.level == level)
        
        # Count by event type
        event_type_counts = {}
        for event in self.events:
            event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        
        # Count by session
        session_counts = {}
        for event in self.events:
            session_counts[event.session_id] = session_counts.get(event.session_id, 0) + 1
        
        # Time range
        timestamps = [e.timestamp for e in self.events]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        return {
            "total_events": len(self.events),
            "level_distribution": level_counts,
            "event_type_distribution": event_type_counts,
            "session_count": len(session_counts),
            "top_sessions": sorted(session_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_hours": (end_time - start_time).total_seconds() / 3600
        }
    
    def export_events(self, format: str = "json", session_id: Optional[str] = None) -> str:
        """Export events in specified format"""
        events = self.get_events(session_id=session_id, limit=10000)
        
        if format == "json":
            return json.dumps([event.to_dict() for event in events], indent=2, default=str)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if events:
                writer = csv.DictWriter(output, fieldnames=events[0].to_dict().keys())
                writer.writeheader()
                for event in events:
                    writer.writerow(event.to_dict())
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _write_to_file(self, event: AuditEvent):
        """Write event to file"""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event.to_dict(), default=str) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit event to file: {e}")
    
    def clear_events(self, session_id: Optional[str] = None):
        """Clear audit events"""
        if session_id:
            self.events = [e for e in self.events if e.session_id != session_id]
        else:
            self.events.clear()
        
        logger.info(f"Cleared audit events{' for session ' + session_id if session_id else ''}")
    
    def rotate_logs(self):
        """Rotate log files if configured"""
        if self.log_file and self.log_file.exists():
            # Create backup
            backup_file = self.log_file.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            self.log_file.rename(backup_file)
            logger.info(f"Rotated audit log to {backup_file}")
