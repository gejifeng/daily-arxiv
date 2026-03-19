"""工具函数模块"""
import os
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def load_env():
    """加载环境变量"""
    load_dotenv()


def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """设置日志
    
    Args:
        config: 配置字典
        
    Returns:
        Logger 对象
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建 logger
    logger = logging.getLogger('daily_arxiv')
    logger.setLevel(log_level)
    
    # 控制台处理器
    if log_config.get('console', True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(console_handler)
    
    # 文件处理器
    log_file = log_config.get('file')
    if log_file:
        # 确保日志目录存在
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    return logger


def save_json(data: Any, filepath: str):
    """保存 JSON 数据
    
    Args:
        data: 要保存的数据
        filepath: 文件路径
    """
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Any:
    """加载 JSON 数据
    
    Args:
        filepath: 文件路径
        
    Returns:
        加载的数据
    """
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_date_string(date: datetime = None) -> str:
    """获取日期字符串
    
    Args:
        date: datetime 对象，默认为当前日期
        
    Returns:
        格式化的日期字符串 YYYY-MM-DD
    """
    if date is None:
        date = datetime.now()
    return date.strftime('%Y-%m-%d')


def get_data_path(config: Dict[str, Any], subdir: str = 'papers') -> str:
    """获取数据存储路径
    
    Args:
        config: 配置字典
        subdir: 子目录名称
        
    Returns:
        数据路径
    """
    storage_config = config.get('storage', {})
    base_path = storage_config.get('json_path', 'data/papers')
    
    if subdir == 'summaries':
        return 'data/summaries'
    
    return base_path


def get_language(config: Dict[str, Any]) -> str:
    """Get deployment language.

    Returns:
        'en' for English mode, otherwise 'zh'
    """
    app_config = config.get('app', {}) if isinstance(config, dict) else {}
    language = str(app_config.get('language', 'zh')).strip().lower()
    return 'en' if language.startswith('en') else 'zh'


def pick_text(config: Dict[str, Any], zh_text: str, en_text: str) -> str:
    """Pick localized text using deployment language."""
    return en_text if get_language(config) == 'en' else zh_text
