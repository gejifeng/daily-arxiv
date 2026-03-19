"""
LLM 客户端工厂

根据配置创建对应的 LLM 客户端
"""
import logging
from typing import Dict, Any

from src.utils import pick_text
from .base_llm_client import BaseLLMClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .claude_client import ClaudeClient
from .deepseek_client import DeepSeekClient
from .vllm_client import VLLMClient


class LLMClientFactory:
    """LLM 客户端工厂"""
    
    # 支持的提供商映射
    PROVIDERS = {
        'openai': OpenAIClient,
        'gemini': GeminiClient,
        'claude': ClaudeClient,
        'deepseek': DeepSeekClient,
        'vllm': VLLMClient,
    }
    
    @classmethod
    def create_client(cls, config: Dict[str, Any]) -> BaseLLMClient:
        """创建 LLM 客户端
        
        Args:
            config: 完整配置字典
            
        Returns:
            LLM 客户端实例
            
        Raises:
            ValueError: 如果提供商不支持
        """
        logger = logging.getLogger('daily_arxiv.llm.factory')
        
        llm_config = config.get('llm', {})
        provider = llm_config.get('provider', 'openai').lower()
        text = lambda zh, en: pick_text(config, zh, en)
        
        if provider not in cls.PROVIDERS:
            raise ValueError(
                text(
                    f"不支持的 LLM 提供商: {provider}\n支持的提供商: {', '.join(cls.PROVIDERS.keys())}",
                    f"Unsupported LLM provider: {provider}\nSupported providers: {', '.join(cls.PROVIDERS.keys())}"
                )
            )
        
        # 获取特定提供商的配置 / Get provider-specific config
        provider_config = dict(llm_config.get(provider, {}))
        provider_config['_language'] = config.get('app', {}).get('language', 'zh')
        
        logger.info(text(f"创建 LLM 客户端: {provider}", f"Creating LLM client: {provider}"))
        
        try:
            client_class = cls.PROVIDERS[provider]
            client = client_class(provider_config)
            logger.info(text(f"✅ {provider.upper()} 客户端创建成功", f"✅ {provider.upper()} client created successfully"))
            return client
        except Exception as e:
            logger.error(text(f"❌ 创建 {provider} 客户端失败: {str(e)}", f"❌ Failed to create {provider} client: {str(e)}"))
            raise
    
    @classmethod
    def list_providers(cls) -> list:
        """列出所有支持的提供商
        
        Returns:
            提供商列表
        """
        return list(cls.PROVIDERS.keys())
