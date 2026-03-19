"""
vLLM 客户端实现

vLLM 提供 OpenAI 兼容的 API 接口
"""
import os
import logging
from typing import List
from openai import OpenAI

from .base_llm_client import BaseLLMClient


class VLLMClient(BaseLLMClient):
    """vLLM 客户端（OpenAI 兼容）"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = logging.getLogger('daily_arxiv.llm.vllm')
        self._lang = str(config.get('_language', 'zh')).strip().lower()
        self._text = lambda zh, en: en if self._lang.startswith('en') else zh
        
        # 获取配置 / Read config
        api_key = config.get('api_key', 'EMPTY')  # vLLM 通常不需要真实的 API Key / vLLM usually does not require a real key
        base_url = config.get('base_url') or os.getenv('VLLM_BASE_URL', 'http://localhost:8000/v1')
        
        # 获取模型名称 / Read model name
        self.model = config.get('model') or os.getenv('VLLM_MODEL', 'default')
        
        # 创建客户端（使用 OpenAI SDK）/ Create client via OpenAI SDK
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        self.logger.info(self._text("vLLM 客户端初始化成功", "vLLM client initialized successfully"))
        self.logger.info(self._text(f"  - 端点: {base_url}", f"  - Endpoint: {base_url}"))
        self.logger.info(self._text(f"  - 模型: {self.model}", f"  - Model: {self.model}"))
    
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = None) -> str:
        """生成文本"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 使用传入的 max_tokens 或默认值 / Use explicit or default max_tokens
            tokens = max_tokens if max_tokens is not None else self.max_tokens
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=tokens,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(self._text(f"vLLM 生成失败: {str(e)}", f"vLLM generation failed: {str(e)}"))
            self.logger.error(self._text(
                f"请确保 vLLM 服务正在运行: {self.client.base_url}",
                f"Please ensure vLLM service is running: {self.client.base_url}"
            ))
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
