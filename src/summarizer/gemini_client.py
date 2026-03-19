"""
Google Gemini 客户端实现
"""
import os
import logging
from typing import List
import google.generativeai as genai

from .base_llm_client import BaseLLMClient


class GeminiClient(BaseLLMClient):
    """Google Gemini 客户端"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = logging.getLogger('daily_arxiv.llm.gemini')
        self._lang = str(config.get('_language', 'zh')).strip().lower()
        self._text = lambda zh, en: en if self._lang.startswith('en') else zh
        
        # 获取 API Key / Read API key
        api_key = config.get('api_key') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(self._text(
                "Gemini API Key 未设置！请在 .env 文件中设置 GEMINI_API_KEY",
                "Gemini API key is not set. Please set GEMINI_API_KEY in .env"
            ))
        
        # 配置 API / Configure API
        genai.configure(api_key=api_key)
        
        # 创建模型 / Create model
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        self.model_instance = genai.GenerativeModel(
            model_name=self.model,
            generation_config=generation_config
        )
        
        self.logger.info(self._text(
            f"Gemini 客户端初始化成功，模型: {self.model}",
            f"Gemini client initialized successfully, model: {self.model}"
        ))
    
    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = None) -> str:
        """生成文本"""
        try:
            # Gemini 将 system prompt 和 user prompt 组合 / Merge system + user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # 如果指定了 max_tokens，需要更新配置 / Rebuild generation config for max_tokens override
            if max_tokens is not None and max_tokens != self.max_tokens:
                import google.generativeai as genai
                generation_config = genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=max_tokens
                )
                response = self.model_instance.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            else:
                response = self.model_instance.generate_content(full_prompt)
            
            # 检查响应 / Validate response
            if not response.text:
                self.logger.warning(self._text("Gemini 返回空响应", "Gemini returned an empty response"))
                return ""
            
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(self._text(f"Gemini 生成失败: {str(e)}", f"Gemini generation failed: {str(e)}"))
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
