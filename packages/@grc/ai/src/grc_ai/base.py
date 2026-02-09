"""Base AI provider protocol and data classes."""

from abc import abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable


class MessageRole(StrEnum):
    """Chat message roles."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """A single chat message."""

    role: MessageRole
    content: str
    name: str | None = None


@dataclass
class ChatResponse:
    """Response from a chat completion."""

    content: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class ChatChunk:
    """A streaming chunk from chat completion."""

    content: str
    finish_reason: str | None = None
    is_final: bool = False


@dataclass
class EmbeddingResponse:
    """Response from an embedding request."""

    embedding: list[float]
    model: str
    usage: dict[str, int] = field(default_factory=dict)


@runtime_checkable
class AIProvider(Protocol):
    """Protocol for AI providers (Azure OpenAI, AWS Bedrock, GCP Vertex AI)."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ChatResponse:
        """Generate a chat completion.

        Args:
            messages: List of chat messages
            model: Model identifier (optional, uses default)
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific options

        Returns:
            ChatResponse with generated content
        """
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[ChatChunk]:
        """Stream a chat completion.

        Args:
            messages: List of chat messages
            model: Model identifier (optional, uses default)
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific options

        Yields:
            ChatChunk objects as they are generated
        """
        ...

    @abstractmethod
    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        **kwargs,
    ) -> EmbeddingResponse:
        """Generate an embedding for text.

        Args:
            text: Text to embed
            model: Embedding model identifier (optional)
            **kwargs: Additional provider-specific options

        Returns:
            EmbeddingResponse with embedding vector
        """
        ...

    @abstractmethod
    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        **kwargs,
    ) -> list[EmbeddingResponse]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            model: Embedding model identifier (optional)
            **kwargs: Additional provider-specific options

        Returns:
            List of EmbeddingResponse objects
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        ...
