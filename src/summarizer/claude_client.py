"""
Anthropic Claude 客户端实现
"""
import os
import logging
from typing import List
from anthropic import Anthropic

from .base_llm_client import BaseLLMClient


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude 客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = logging.getLogger('daily_arxiv.llm.claude')
        self._lang = str(config.get('_language', 'zh')).strip().lower()
        self._text = lambda zh, en: en if self._lang.startswith('en') else zh
        
        # 获取 API Key / Read API key
        api_key = config.get('api_key') or os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(self._text(
                "Claude API Key 未设置！请在 .env 文件中设置 CLAUDE_API_KEY",
                "Claude API key is not set. Please set CLAUDE_API_KEY in .env"
            ))
        
        # 创建客户端 / Create client
        self.client = Anthropic(api_key=api_key)
        
        self.logger.info(self._text(
            f"Claude 客户端初始化成功，模型: {self.model}",
            f"Claude client initialized successfully, model: {self.model}"
        ))
    
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = None) -> str:
        """生成文本"""
        try:
            # 使用传入的 max_tokens 或默认值 / Use explicit or default max_tokens
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            # Claude 需要明确的 system 参数 / Claude needs explicit system field
            kwargs = {
                "model": self.model,
                "max_tokens": tokens,
                "temperature": self.temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            # Claude 的响应结构 / Claude response format
            return response.content[0].text.strip()
            
        except Exception as e:
            self.logger.error(self._text(f"Claude 生成失败: {str(e)}", f"Claude generation failed: {str(e)}"))
            raise
    
    def generate_batch(self, prompts: List[str], system_prompt: str = None) -> List[str]:
        """批量生成文本"""
        results = []
        for prompt in prompts:
            try:
                result = self.generate(prompt, system_prompt)
                results.append(result)
            except Exception as e:
                self.logger.error(self._text(f"批量生成失败: {str(e)}", f"Batch generation failed: {str(e)}"))
                results.append(f"Error: {str(e)}")
        return results
