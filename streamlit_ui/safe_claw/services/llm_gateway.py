"""LLM Gateway service for SafeClaw"""

from abc import ABC, abstractmethod
from typing import Iterator, List, Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama

from streamlit_ui.safe_claw.models.config import LLMConfig

logger = logging.getLogger(__name__)


def _debug_prompt(messages: List, call_type: str = "Invoke"):
    """Debug function to log complete prompt content"""
    logger.info(f"🔍 DEBUG: === LLM Gateway {call_type} 开始 ===")
    logger.info(f"🔍 DEBUG: 消息数量: {len(messages)}")
    
    total_chars = 0
    for i, msg in enumerate(messages):
        msg_content = msg.content if hasattr(msg, 'content') else str(msg)
        msg_type = msg.__class__.__name__ if hasattr(msg, '__class__') else type(msg).__name__
        char_count = len(msg_content)
        total_chars += char_count
        
        logger.info(f"🔍 DEBUG: 消息 {i+1} ({msg_type}): {char_count} 字符")
        logger.info(f"🔍 DEBUG: 内容预览: {msg_content[:200]}...")
        
        # 如果是系统消息，记录完整内容
        if hasattr(msg, '__class__') and 'System' in msg_type:
            logger.info(f"🔍 DEBUG: 完整系统消息:\n{msg_content}")
    
    logger.info(f"🔍 DEBUG: 总字符数: {total_chars}")
    logger.info(f"🔍 DEBUG: 估算tokens: {total_chars // 4}")
    logger.info(f"🔍 DEBUG: === 开始{call_type}实际LLM ===")


class BaseLLMGateway(ABC):
    """Abstract base class for LLM gateways"""
    
    @abstractmethod
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream LLM response"""
        pass
    
    @abstractmethod
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM synchronously"""
        pass
    
    @abstractmethod
    async def astream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream LLM response asynchronously"""
        pass
    
    @abstractmethod
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM asynchronously"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass


class OpenAIGateway(BaseLLMGateway):
    """OpenAI LLM gateway"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            streaming=True
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """Convert message dicts to LangChain messages"""
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        return lc_messages
    
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream OpenAI response"""
        try:
            lc_messages = self._convert_messages(messages)
            
            # DEBUG: 记录完整的prompt内容
            _debug_prompt(lc_messages, "Stream")
            
            for chunk in self.llm.stream(lc_messages):
                if chunk.content:
                    yield chunk.content
                    
            logger.info("🔍 DEBUG: === LLM Stream 完成 ===")
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke OpenAI synchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            
            # DEBUG: 记录完整的prompt内容
            _debug_prompt(lc_messages, "Invoke")
            
            response = self.llm.invoke(lc_messages)
            
            logger.info("🔍 DEBUG: === LLM调用完成 ===")
            logger.info(f"🔍 DEBUG: 响应长度: {len(response.content)} 字符")
            
            return response.content
        except Exception as e:
            logger.error(f"OpenAI invoke error: {e}")
            return f"Error: {str(e)}"
    
    async def astream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream OpenAI response asynchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            async for chunk in self.llm.astream(lc_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"OpenAI async streaming error: {e}")
            yield f"Error: {str(e)}"
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke OpenAI asynchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            response = await self.llm.ainvoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"OpenAI async invoke error: {e}")
            return f"Error: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model info"""
        return {
            "provider": "openai",
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }


class AnthropicGateway(BaseLLMGateway):
    """Anthropic Claude gateway"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = ChatAnthropic(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            streaming=True
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """Convert message dicts to LangChain messages"""
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        return lc_messages
    
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream Anthropic response"""
        try:
            lc_messages = self._convert_messages(messages)
            for chunk in self.llm.stream(lc_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke Anthropic synchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            response = self.llm.invoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"Anthropic invoke error: {e}")
            return f"Error: {str(e)}"
    
    async def astream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream Anthropic response asynchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            async for chunk in self.llm.astream(lc_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Anthropic async streaming error: {e}")
            yield f"Error: {str(e)}"
    
    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke Anthropic asynchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            response = await self.llm.ainvoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"Anthropic async invoke error: {e}")
            return f"Error: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model info"""
        return {
            "provider": "anthropic",
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }


class OllamaGateway(BaseLLMGateway):
    """Ollama local LLM gateway"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = ChatOllama(
            model=config.model,
            base_url=config.base_url or "http://localhost:11434",
            temperature=config.temperature,
            streaming=True
        )
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """Convert message dicts to LangChain messages"""
        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
        return lc_messages
    
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream Ollama response"""
        try:
            lc_messages = self._convert_messages(messages)
            for chunk in self.llm.stream(lc_messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke Ollama synchronously"""
        try:
            lc_messages = self._convert_messages(messages)
            response = self.llm.invoke(lc_messages)
            return response.content
        except Exception as e:
            logger.error(f"Ollama invoke error: {e}")
            return f"Error: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model info"""
        return {
            "provider": "ollama",
            "model": self.config.model,
            "temperature": self.config.temperature,
            "base_url": self.config.base_url or "http://localhost:11434"
        }


class LLMGatewayFactory:
    """Factory for creating LLM gateways"""
    
    @staticmethod
    def create_gateway(config: LLMConfig) -> BaseLLMGateway:
        """Create appropriate gateway based on provider"""
        # Check for mock configuration first
        if config.api_key == "mock-key" or config.api_key == "lm-studio" and not config.base_url:
            return MockLLMGateway(config)
        
        try:
            if config.provider == "openai":
                return OpenAIGateway(config)
            elif config.provider == "anthropic":
                return AnthropicGateway(config)
            elif config.provider == "ollama":
                return OllamaGateway(config)
            else:
                raise ValueError(f"Unsupported LLM provider: {config.provider}")
        except Exception as e:
            # Fallback to mock gateway if real LLM fails to initialize
            logger.warning(f"Failed to create {config.provider} gateway: {e}. Falling back to mock.")
            return MockLLMGateway(config)


class MockLLMGateway(BaseLLMGateway):
    """Mock LLM gateway for testing"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.call_count = 0
    
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Mock streaming response"""
        self.call_count += 1
        response = "This is a mock response from SafeClaw AI assistant. The LLM service is running in demo mode."
        for word in response.split():
            yield word + " "
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Mock synchronous response"""
        self.call_count += 1
        return "This is a mock response from SafeClaw AI assistant. The LLM service is running in demo mode."
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get mock model information"""
        return {
            "provider": "mock",
            "model": "mock-gpt-3.5-turbo",
            "context_length": 4096,
            "call_count": self.call_count
        }


class LLMService:
    """Main LLM service"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.gateway = LLMGatewayFactory.create_gateway(config)
        logger.info(f"Initialized LLM service with {config.provider} - {config.model}")
    
    def stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        """Stream LLM response"""
        return self.gateway.stream(messages)
    
    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """Invoke LLM synchronously"""
        return self.gateway.invoke(messages)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return self.gateway.get_model_info()
    
    def update_config(self, config: LLMConfig):
        """Update LLM configuration"""
        self.config = config
        self.gateway = LLMGatewayFactory.create_gateway(config)
        logger.info(f"Updated LLM service to {config.provider} - {config.model}")
