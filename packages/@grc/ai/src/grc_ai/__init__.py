"""GRC AI - Multi-cloud AI provider abstraction."""

from grc_ai.base import (
    AIProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
)
from grc_ai.config import AIConfig
from grc_ai.factory import AIProviderType, create_ai_provider

__version__ = "0.1.0"

__all__ = [
    "AIProvider",
    "ChatMessage",
    "ChatResponse",
    "ChatChunk",
    "EmbeddingResponse",
    "create_ai_provider",
    "AIProviderType",
    "AIConfig",
]
