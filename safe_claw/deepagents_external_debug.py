"""Debug configuration specifically for the external deepagents library"""

import logging
import os
import sys

def setup_external_deepagents_debug():
    """Enable debug logging specifically for the external deepagents library"""
    
    print("🔍 Setting up debug logging for external deepagents library...")
    
    # Method 1: Direct logger configuration
    debug_loggers = [
        'deepagents',  # Main external deepagents library
        'deepagents.core',  # Core modules
        'deepagents.agents',  # Agent modules
        'deepagents.tools',  # Tool modules
        'deepagents.skills',  # Skills modules
        'deepagents.middleware',  # Middleware modules
        'deepagents.graph',  # Graph modules
    ]
    
    for logger_name in debug_loggers:
        try:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            
            # Remove existing handlers to avoid duplicates
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Add detailed console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            
            # Detailed formatter for deepagents debugging
            formatter = logging.Formatter(
                '🔦 DEEPAGENTS: %(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Prevent propagation to avoid duplicate logs
            logger.propagate = False
            
            print(f"✅ Enabled debug for logger: {logger_name}")
            
        except Exception as e:
            print(f"⚠️ Could not enable debug for {logger_name}: {e}")

def setup_comprehensive_debug():
    """Enable comprehensive debug logging for all relevant libraries"""
    
    # Set root logging level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Configure all relevant loggers
    all_debug_loggers = [
        # External deepagents library
        'deepagents',
        'deepagents.core',
        'deepagents.agents',
        'deepagents.tools',
        'deepagents.skills',
        'deepagents.middleware',
        'deepagents.graph',
        
        # LangChain ecosystem
        'langchain',
        'langchain_community',
        'langchain_core',
        'langgraph',
        
        # SafeClaw integration
        'safe_claw.core.deepagents',
        'safe_claw.core.deepagents.official_integration',
        'safe_claw.services.llm_gateway',
    ]
    
    for logger_name in all_debug_loggers:
        try:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            
            # Only add handler if not already present
            if not logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                handler.setLevel(logging.DEBUG)
                
                formatter = logging.Formatter(
                    '🐛 %(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            
            logger.propagate = False
            
        except Exception as e:
            print(f"⚠️ Error setting up {logger_name}: {e}")

def quick_debug_enable():
    """Quick method to enable deepagents debug using environment variables"""
    
    # Set environment variables for deepagents logging
    os.environ['DEEPAGENTS_LOG_LEVEL'] = 'DEBUG'
    os.environ['DEEPAGENTS_VERBOSE'] = '1'
    os.environ['LANGCHAIN_VERBOSE'] = 'true'
    os.environ['LANGCHAIN_DEBUG'] = 'true'
    os.environ['LANGGRAPH_VERBOSE'] = 'true'
    
    print("🚀 Quick debug enabled via environment variables:")
    print("   - DEEPAGENTS_LOG_LEVEL=DEBUG")
    print("   - DEEPAGENTS_VERBOSE=1")
    print("   - LANGCHAIN_VERBOSE=true")
    print("   - LANGCHAIN_DEBUG=true")
    print("   - LANGGRAPH_VERBOSE=true")

if __name__ == "__main__":
    print("DeepAgents External Library Debug Configuration")
    print("=" * 50)
    
    # Test the debug setup
    setup_external_deepagents_debug()
    print()
    quick_debug_enable()
    
    # Test logging
    test_logger = logging.getLogger('deepagents')
    test_logger.debug("Test message - DeepAgents debug logging is working!")
