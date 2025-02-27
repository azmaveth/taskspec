"""
LLM client implementation using litellm.
"""

import os
import litellm
from typing import Dict, Any, Optional, List
from taskspec.config import Config
from rich.console import Console

console = Console()

def setup_llm_client(config: Config, cache_manager: Optional[Any] = None) -> Dict[str, Any]:
    """
    Set up the LLM client based on configuration.
    
    Args:
        config: Configuration object
        cache_manager: Optional cache manager
        
    Returns:
        LLM client interface
    """
    # Set API keys for various providers
    if config.openai_api_key:
        os.environ["OPENAI_API_KEY"] = config.openai_api_key
    if config.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = config.anthropic_api_key
    if config.cohere_api_key:
        os.environ["COHERE_API_KEY"] = config.cohere_api_key
    
    # Return the configuration for executing LLM calls
    return {
        "provider": config.llm_provider,
        "model": config.llm_model,
        "cache": cache_manager
    }

def complete(
    llm_config: Dict[str, Any],
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 4000,
) -> str:
    """
    Send a completion request to the LLM.
    
    Args:
        llm_config: LLM configuration
        prompt: The user prompt
        system_prompt: Optional system prompt
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        
    Returns:
        str: The LLM response
    """
    messages = []
    
    # Add system prompt if provided
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # Add user prompt
    messages.append({"role": "user", "content": prompt})
    
    model_string = f"{llm_config['provider']}/{llm_config['model']}"
    
    # Check cache if available
    cache_manager = llm_config.get('cache')
    if cache_manager:
        cache_key = cache_manager.generate_key(
            prompt=str(messages), 
            model=model_string, 
            temperature=temperature
        )
        cached_response = cache_manager.get(cache_key)
        if cached_response:
            return cached_response
    
    try:
        response = litellm.completion(
            model=model_string,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        result = response.choices[0].message.content
        
        # Store in cache if available
        if cache_manager:
            cache_manager.set(cache_key, result)
        
        return result
    except Exception as e:
        console.print(f"[bold red]Error communicating with LLM:[/bold red] {str(e)}")
        raise RuntimeError(f"Failed to get response from LLM: {str(e)}")

def chat_with_history(
    llm_config: Dict[str, Any],
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 4000,
) -> str:
    """
    Send a chat completion request with message history.
    
    Args:
        llm_config: LLM configuration
        messages: List of message dictionaries with role and content
        temperature: Temperature for generation
        max_tokens: Maximum tokens to generate
        
    Returns:
        str: The LLM response
    """
    model_string = f"{llm_config['provider']}/{llm_config['model']}"
    
    # Check cache if available
    cache_manager = llm_config.get('cache')
    if cache_manager:
        cache_key = cache_manager.generate_key(
            prompt=str(messages), 
            model=model_string, 
            temperature=temperature
        )
        cached_response = cache_manager.get(cache_key)
        if cached_response:
            return cached_response
    
    try:
        response = litellm.completion(
            model=model_string,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        result = response.choices[0].message.content
        
        # Store in cache if available
        if cache_manager:
            cache_manager.set(cache_key, result)
        
        return result
    except Exception as e:
        console.print(f"[bold red]Error communicating with LLM:[/bold red] {str(e)}")
        raise RuntimeError(f"Failed to get response from LLM: {str(e)}")
