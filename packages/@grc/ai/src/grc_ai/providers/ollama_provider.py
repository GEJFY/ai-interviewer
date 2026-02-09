"""Ollama (Local LLM) provider implementation."""

import logging
from collections.abc import AsyncIterator

from ollama import AsyncClient

from grc_ai.base import (
    AIProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
)
from grc_ai.config import OllamaConfig

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama local LLM provider.

    ローカルLLMを使用した開発・テスト向けプロバイダー。
    Ollama Python SDK経由でOllamaサーバーと通信する。
    """

    def __init__(self, config: OllamaConfig) -> None:
        """Initialize Ollama provider.

        Args:
            config: Ollama configuration
        """
        self.config = config
        self.client = AsyncClient(host=config.base_url)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ChatResponse:
        """Generate a chat completion using Ollama."""
        model_name = model or self.config.model_name

        ollama_messages = [{"role": msg.role.value, "content": msg.content} for msg in messages]

        response = await self.client.chat(
            model=model_name,
            messages=ollama_messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )

        # Ollama SDK返却値からデータ抽出
        content = response.get("message", {}).get("content", "")
        usage_info = response.get("eval_count", 0)
        prompt_count = response.get("prompt_eval_count", 0)

        return ChatResponse(
            content=content,
            model=response.get("model", model_name),
            finish_reason="stop" if response.get("done") else None,
            usage={
                "prompt_tokens": prompt_count,
                "completion_tokens": usage_info,
                "total_tokens": prompt_count + usage_info,
            },
        )

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[ChatChunk]:
        """Stream a chat completion using Ollama."""
        model_name = model or self.config.model_name

        ollama_messages = [{"role": msg.role.value, "content": msg.content} for msg in messages]

        stream = await self.client.chat(
            model=model_name,
            messages=ollama_messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            stream=True,
        )

        async for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            done = chunk.get("done", False)
            if content or done:
                yield ChatChunk(
                    content=content,
                    finish_reason="stop" if done else None,
                    is_final=done,
                )

    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        **kwargs,
    ) -> EmbeddingResponse:
        """Generate an embedding using Ollama."""
        embed_model = model or self.config.embedding_model

        response = await self.client.embed(
            model=embed_model,
            input=text,
        )

        embeddings = response.get("embeddings", [[]])
        embedding = embeddings[0] if embeddings else []

        return EmbeddingResponse(
            embedding=embedding,
            model=embed_model,
            usage={
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0),
            },
        )

    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        **kwargs,
    ) -> list[EmbeddingResponse]:
        """Generate embeddings for multiple texts using Ollama."""
        embed_model = model or self.config.embedding_model

        response = await self.client.embed(
            model=embed_model,
            input=texts,
        )

        embeddings = response.get("embeddings", [])
        total_tokens = response.get("prompt_eval_count", 0)

        return [
            EmbeddingResponse(
                embedding=emb,
                model=embed_model,
                usage={
                    "prompt_tokens": total_tokens,
                    "total_tokens": total_tokens,
                },
            )
            for emb in embeddings
        ]

    async def close(self) -> None:
        """Clean up resources."""
        # Ollama AsyncClientはexplicitなクローズ不要
        pass
