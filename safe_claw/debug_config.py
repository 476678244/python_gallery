"""Debug configuration for DeepAgents logging"""

import logging
import os

def setup_deepagents_debug():
    """Enable debug logging for DeepAgents and related components"""
    
    # Set deepagents specific loggers to DEBUG level
    debug_loggers = [
        'deepagents',  # External deepagents library
        'deepagents.*',  # All submodules of external deepagents
        'safe_claw.core.deepagents',
        'safe_claw.core.deepagents.official_integration',
        'langchain',
        'langchain_community',
        'langchain_core',
        'langgraph',
        'safe_claw.services.llm_gateway'
    ]
    
    for logger_name in debug_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Add console handler if not already present
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            
            # Detailed formatter for debugging
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    # Also set root logger to DEBUG for comprehensive logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    print("✅ DeepAgents debug logging enabled")
    print("🔍 Monitoring the following loggers:")
    for logger_name in debug_loggers:
        print(f"   - {logger_name}")

def setup_context_length_debug():
    """Specific debugging for context length issues"""
    
    # Create a dedicated logger for context length monitoring
    ctx_logger = logging.getLogger('context_length_debug')
    ctx_logger.setLevel(logging.DEBUG)
    
    if not ctx_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '🔍 CTX: %(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        ctx_logger.addHandler(handler)
    
    ctx_logger.propagate = False
    return ctx_logger

if __name__ == "__main__":
    # Test the debug setup
    setup_deepagents_debug()
    ctx_logger = setup_context_length_debug()
    
    # Test logging
    ctx_logger.debug("Debug logging test - context length monitoring active")
