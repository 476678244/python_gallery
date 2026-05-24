"""Logging utility for SafeClaw"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

class SafeClawLogger:
    """Enhanced logger for SafeClaw with structured logging"""
    
    def __init__(self, name: str = "safe_claw", log_level: str = "INFO", 
                 log_file: Optional[str] = None, max_file_size: int = 10 * 1024 * 1024,
                 backup_count: int = 5):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_console_handler()
        if log_file:
            self._setup_file_handler()
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _setup_console_handler(self):
        """Setup console handler with formatting"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    def _setup_file_handler(self):
        """Setup rotating file handler"""
        log_path = Path(self.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        
        # Create detailed formatter for file
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional structured data"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data support"""
        if kwargs:
            # Add structured data as extra field
            extra = {'structured_data': kwargs}
            self.logger.log(level, message, extra=extra)
        else:
            self.logger.log(level, message)
    
    def log_structured(self, level: str, event: str, data: Dict[str, Any]):
        """Log structured event"""
        log_level = getattr(logging, level.upper())
        
        # Create structured message
        structured_message = {
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.logger.log(log_level, json.dumps(structured_message))
    
    def log_exception(self, message: str, exc_info=True):
        """Log exception with traceback"""
        self.logger.error(message, exc_info=exc_info)
    
    def set_level(self, level: str):
        """Change logging level"""
        self.log_level = getattr(logging, level.upper())
        self.logger.setLevel(self.log_level)
        
        # Update all handlers
        for handler in self.logger.handlers:
            handler.setLevel(self.log_level)
    
    def add_file_handler(self, file_path: str, level: str = None):
        """Add additional file handler"""
        log_path = Path(file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(file_path, encoding='utf-8')
        handler.setLevel(getattr(logging, level.upper()) if level else self.log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance"""
        return self.logger

class ContextLogger:
    """Context logger for adding automatic context to log messages"""
    
    def __init__(self, logger: SafeClawLogger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
    
    def debug(self, message: str, **kwargs):
        """Debug message with context"""
        merged_context = {**self.context, **kwargs}
        self.logger.debug(message, **merged_context)
    
    def info(self, message: str, **kwargs):
        """Info message with context"""
        merged_context = {**self.context, **kwargs}
        self.logger.info(message, **merged_context)
    
    def warning(self, message: str, **kwargs):
        """Warning message with context"""
        merged_context = {**self.context, **kwargs}
        self.logger.warning(message, **merged_context)
    
    def error(self, message: str, **kwargs):
        """Error message with context"""
        merged_context = {**self.context, **kwargs}
        self.logger.error(message, **merged_context)
    
    def critical(self, message: str, **kwargs):
        """Critical message with context"""
        merged_context = {**self.context, **kwargs}
        self.logger.critical(message, **merged_context)

def setup_logging(config: Dict[str, Any]) -> SafeClawLogger:
    """Setup logging from configuration"""
    log_config = config.get("logging", {})
    
    return SafeClawLogger(
        name=log_config.get("name", "safe_claw"),
        log_level=log_config.get("level", "INFO"),
        log_file=log_config.get("file"),
        max_file_size=log_config.get("max_file_size", 10 * 1024 * 1024),
        backup_count=log_config.get("backup_count", 5)
    )

def get_logger(name: str = "safe_claw") -> SafeClawLogger:
    """Get or create logger instance"""
    # Check if logger already exists with our custom handler
    logger = logging.getLogger(name)
    
    # If it has our custom attribute, return it
    if hasattr(logger, '_safe_claw_logger'):
        return logger._safe_claw_logger
    
    # Create new logger
    safe_claw_logger = SafeClawLogger(name)
    logger._safe_claw_logger = safe_claw_logger
    
    return safe_claw_logger

def with_context(logger: SafeClawLogger, **context) -> ContextLogger:
    """Create context logger with automatic context"""
    return ContextLogger(logger, context)

class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, logger: SafeClawLogger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self.start_times[operation] = datetime.now()
        self.logger.debug(f"Started operation: {operation}")
    
    def end_timer(self, operation: str, **context):
        """End timing an operation and log duration"""
        if operation not in self.start_times:
            self.logger.warning(f"No start time found for operation: {operation}")
            return
        
        start_time = self.start_times.pop(operation)
        duration = (datetime.now() - start_time).total_seconds()
        
        self.logger.info(
            f"Completed operation: {operation}",
            duration_seconds=duration,
            **context
        )
        
        return duration
    
    def time_operation(self, operation: str):
        """Context manager for timing operations"""
        from contextlib import contextmanager
        
        @contextmanager
        def timer():
            self.start_timer(operation)
            try:
                yield
            finally:
                self.end_timer(operation)
        
        return timer()

class AuditLogger:
    """Specialized logger for audit events"""
    
    def __init__(self, logger: SafeClawLogger):
        self.logger = logger
    
    def log_user_action(self, user_id: str, action: str, **details):
        """Log user action"""
        self.logger.info(
            f"User action: {action}",
            event_type="user_action",
            user_id=user_id,
            action=action,
            details=details
        )
    
    def log_security_event(self, event_type: str, severity: str, **details):
        """Log security event"""
        self.logger.warning(
            f"Security event: {event_type}",
            event_type="security",
            security_event=event_type,
            severity=severity,
            details=details
        )
    
    def log_system_event(self, component: str, event: str, **details):
        """Log system event"""
        self.logger.info(
            f"System event: {component} - {event}",
            event_type="system",
            component=component,
            system_event=event,
            details=details
        )
    
    def log_error_event(self, component: str, error: str, **details):
        """Log error event"""
        self.logger.error(
            f"Error in {component}: {error}",
            event_type="error",
            component=component,
            error=error,
            details=details
        )

# Global logger instance
_global_logger = None

def initialize_global_logging(config: Dict[str, Any] = None):
    """Initialize global logger"""
    global _global_logger
    
    if config:
        _global_logger = setup_logging(config)
    else:
        _global_logger = get_logger()

def get_global_logger() -> SafeClawLogger:
    """Get global logger instance"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = get_logger()
    
    return _global_logger
