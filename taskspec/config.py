"""
Configuration management for taskspec.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config(BaseModel):
    """Configuration for taskspec."""
    
    # LLM settings
    llm_provider: str
    llm_model: str
    
    # API keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    brave_api_key: Optional[str] = None
    
    # Output settings
    output_directory: Path = Path("output")
    
    # Other settings
    max_search_results: int = 5
    template_path: Optional[Path] = None
    conventions_file: Optional[Path] = None
    multi_step_enabled: bool = True
    validation_enabled: bool = True
    max_validation_iterations: int = 3
    
    # Cache settings
    cache_enabled: bool = True
    cache_type: str = "disk"
    cache_ttl: int = 86400  # 24 hours in seconds
    cache_path: Optional[str] = None
    
    # Use model_config instead of class Config
    model_config = {
        "frozen": True
    }

def load_config(
    provider_override: Optional[str] = None, 
    model_override: Optional[str] = None,
    cache_enabled_override: Optional[bool] = None,
    cache_type_override: Optional[str] = None,
    cache_ttl_override: Optional[int] = None,
    conventions_file_override: Optional[Path] = None
) -> Config:
    """
    Load configuration from environment variables and optional overrides.
    
    Args:
        provider_override: Override for the LLM provider
        model_override: Override for the LLM model
        cache_enabled_override: Override for cache enabled setting
        cache_type_override: Override for cache type
        cache_ttl_override: Override for cache TTL
        conventions_file_override: Override for conventions file path
        
    Returns:
        Config: Configuration object
    """
    # Load API keys from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    cohere_api_key = os.getenv("COHERE_API_KEY")
    brave_api_key = os.getenv("BRAVE_API_KEY")
    
    # LLM provider and model with defaults
    llm_provider = provider_override or os.getenv("LLM_PROVIDER", "ollama")
    
    # Set default model based on provider
    default_model = "athene-v2"  # Default for ollama
    if llm_provider == "openai":
        default_model = "gpt-4o"
    elif llm_provider == "anthropic":
        default_model = "claude-3-opus-20240229"
    elif llm_provider == "cohere":
        default_model = "command-r"
    
    llm_model = model_override or os.getenv("LLM_MODEL", default_model)
    
    # Other settings
    max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    multi_step_enabled = os.getenv("MULTI_STEP_ENABLED", "1").lower() in ("1", "true", "yes", "on")
    validation_enabled = os.getenv("VALIDATION_ENABLED", "1").lower() in ("1", "true", "yes", "on")
    max_validation_iterations = int(os.getenv("MAX_VALIDATION_ITERATIONS", "3"))
    
    # Output directory
    output_directory = os.getenv("OUTPUT_DIRECTORY", "output")
    output_directory = Path(output_directory)
    
    # Cache settings
    cache_enabled = cache_enabled_override if cache_enabled_override is not None else \
                   os.getenv("CACHE_ENABLED", "1").lower() in ("1", "true", "yes", "on")
    cache_type = cache_type_override or os.getenv("CACHE_TYPE", "disk")
    cache_ttl = cache_ttl_override or int(os.getenv("CACHE_TTL", "86400"))
    cache_path = os.getenv("CACHE_PATH")
    
    # Get conventions file path from override or environment
    conventions_file = conventions_file_override or os.getenv("CONVENTIONS_FILE")
    if conventions_file and not isinstance(conventions_file, Path):
        conventions_file = Path(conventions_file)
        
    return Config(
        llm_provider=llm_provider,
        llm_model=llm_model,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        cohere_api_key=cohere_api_key,
        brave_api_key=brave_api_key,
        max_search_results=max_search_results,
        multi_step_enabled=multi_step_enabled,
        validation_enabled=validation_enabled,
        max_validation_iterations=max_validation_iterations,
        cache_enabled=cache_enabled,
        cache_type=cache_type,
        cache_ttl=cache_ttl,
        cache_path=cache_path,
        conventions_file=conventions_file,
        output_directory=output_directory,
    )