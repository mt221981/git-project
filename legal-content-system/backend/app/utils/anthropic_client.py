"""Anthropic Claude API client wrapper."""

from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from app.config import settings


class AnthropicClient:
    """
    Wrapper for Anthropic Claude API client.

    Provides convenience methods for common operations.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: Optional API key (defaults to settings.ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.client = Anthropic(api_key=self.api_key)
        self.default_model = "claude-sonnet-4-20250514"

    def create_message(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        Create a message completion.

        Args:
            prompt: User prompt
            system: Optional system prompt
            model: Model to use (defaults to claude-3-5-sonnet)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            **kwargs: Additional arguments to pass to API

        Returns:
            Response text from Claude

        Raises:
            Exception: If API call fails
        """
        messages = [{"role": "user", "content": prompt}]

        request_params = {
            "model": model or self.default_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            **kwargs
        }

        if system:
            request_params["system"] = system

        try:
            response = self.client.messages.create(**request_params)
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    def create_structured_message(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """
        Create a message with structured output expectation.

        Uses lower temperature for more consistent structured output.

        Args:
            prompt: User prompt
            system: Optional system prompt
            model: Model to use
            max_tokens: Maximum tokens to generate
            **kwargs: Additional arguments

        Returns:
            Response text from Claude
        """
        return self.create_message(
            prompt=prompt,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=0.3,  # Lower temp for structured output
            **kwargs
        )

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        This is a rough estimate (4 chars per token average).
        For exact count, use the official tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token on average
        return len(text) // 4


def get_anthropic_client() -> AnthropicClient:
    """
    Get Anthropic client instance.

    Returns:
        AnthropicClient instance
    """
    return AnthropicClient()
