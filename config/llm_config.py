"""
LLM Configuration Management.

This module provides configuration loading and management for LLM providers.
"""

import os
import yaml
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class LLMConfig:
    """Configuration for LLM providers and models."""

    # Provider settings
    provider: str = "openai"

    # Writer model settings
    writer_model: str = "doubao-seed-1-6-lite-251015"
    writer_api_base: str = "https://ark.cn-beijing.volces.com/api/v3"
    writer_api_key: str = "a8509ac0-ea82-4d50-b284-8f826988677d"
    writer_temperature: float = 0.7
    writer_max_tokens: int = 8000
    writer_timeout: int = 180

    # Retry settings
    max_retries: int = 3
    retry_delay: int = 2


def get_default_config() -> LLMConfig:
    """
    Get default configuration.

    Returns:
        LLMConfig with default values
    """
    return LLMConfig()


def substitute_env_vars(value: str) -> str:
    """
    Substitute environment variables in configuration values.

    Supports ${VAR_NAME} syntax.

    Args:
        value: String that may contain environment variable references

    Returns:
        String with environment variables substituted
    """
    if not isinstance(value, str):
        return value

    import re
    pattern = r'\$\{([^}]+)\}'

    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(pattern, replace_var, value)


def load_config_from_yaml(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to YAML config file. If None, uses default location.

    Returns:
        Dictionary with configuration values
    """
    if config_path is None:
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config" / "llm_config.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
            return config_data or {}
    except Exception as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        return {}


def load_config(config_path: Optional[str] = None) -> LLMConfig:
    """
    Load configuration from YAML file with environment variable substitution.

    Args:
        config_path: Optional path to custom config file

    Returns:
        LLMConfig object with loaded settings
    """
    config = get_default_config()
    yaml_config = load_config_from_yaml(config_path)

    if not yaml_config:
        return config

    llm_config = yaml_config.get('llm', {})

    if 'provider' in llm_config:
        config.provider = llm_config['provider']

    writer = llm_config.get('writer', {})
    if 'model' in writer:
        config.writer_model = writer['model']
    if 'api_base' in writer:
        config.writer_api_base = substitute_env_vars(writer['api_base'])
    if 'api_key' in writer:
        config.writer_api_key = substitute_env_vars(writer['api_key'])
    if 'temperature' in writer:
        config.writer_temperature = float(writer['temperature'])
    if 'max_tokens' in writer:
        config.writer_max_tokens = int(writer['max_tokens'])
    if 'timeout' in writer:
        config.writer_timeout = int(writer['timeout'])

    retry = llm_config.get('retry', {})
    if 'max_retries' in retry:
        config.max_retries = int(retry['max_retries'])
    if 'retry_delay' in retry:
        config.retry_delay = int(retry['retry_delay'])

    return config
