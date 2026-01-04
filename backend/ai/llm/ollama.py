import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://127.0.0.1:11434"

# Model mappings for each agent type
OLLAMA_MODELS = {
    "sql": "qwen-text2sql:latest",
    "mongo": "qwen-text2mongo:latest",
    "pandas": "qwen-text2pandas:latest"
}


async def check_ollama_health() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        return False


async def generate_with_ollama(
    prompt: str,
    model_type: str,
    system_prompt: Optional[str] = None
) -> Optional[str]:
    """
    Generate text using Ollama with the specified model.
    
    Args:
        prompt: The user prompt
        model_type: One of 'sql', 'mongo', 'pandas'
        system_prompt: Optional system prompt for context
        
    Returns:
        Generated text or None if failed
    """
    model = OLLAMA_MODELS.get(model_type)
    if not model:
        logger.error(f"Unknown model type: {model_type}")
        return None
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,  # Low temperature for more deterministic outputs
            "top_p": 0.9,
            "num_predict": 512
        }
    }
    
    if system_prompt:
        payload["system"] = system_prompt
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama request failed: {response.status_code} - {response.text}")
                return None
                
    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        return None
    except Exception as e:
        logger.error(f"Ollama request failed: {e}")
        return None


async def generate_with_ollama_chat(
    messages: list,
    model_type: str
) -> Optional[str]:
    """
    Generate text using Ollama chat API with the specified model.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model_type: One of 'sql', 'mongo', 'pandas'
        
    Returns:
        Generated text or None if failed
    """
    model = OLLAMA_MODELS.get(model_type)
    if not model:
        logger.error(f"Unknown model type: {model_type}")
        return None
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 512
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
            else:
                logger.error(f"Ollama chat request failed: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Ollama chat request failed: {e}")
        return None
