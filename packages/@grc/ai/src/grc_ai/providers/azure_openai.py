"""Azure OpenAI provider implementation."""

from collections.abc import AsyncIterator

from openai import AsyncAzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from grc_ai.base import (
    AIProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
)
from grc_ai.config import AzureOpenAIConfig


class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI API provider."""

    def __init__(self, config: AzureOpenAIConfig) -> None:
        """Initialize Azure OpenAI provider.

        Args:
            config: Azure OpenAI configuration
        """
        self.config = config
        self.client = AsyncAzureOpenAI(
            api_key=config.api_key,
            api_version=config.api_version,
            azure_endpoint=config.endpoint,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> ChatResponse:
        """Generate a chat completion using Azure OpenAI."""
        deployment = model or self.config.deployment_name

        response = await self.client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
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
        """Stream a chat completion using Azure OpenAI."""
        deployment = model or self.config.deployment_name

        stream = await self.client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices:
                choice = chunk.choices[0]
                delta = choice.delta
                if delta and delta.content:
                    yield ChatChunk(
                        content=delta.content,
                        finish_reason=choice.finish_reason,
                        is_final=choice.finish_reason is not None,
                    )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def embed(
        self,
        text: str,
        *,
        model: str | None = None,
        **kwargs,
    ) -> EmbeddingResponse:
        """Generate an embedding using Azure OpenAI."""
        deployment = model or self.config.embedding_deployment

        response = await self.client.embeddings.create(
            model=deployment,
            input=text,
            **kwargs,
        )

        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        )

    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        **kwargs,
    ) -> list[EmbeddingResponse]:
        """Generate embeddings for multiple texts."""
        deployment = model or self.config.embedding_deployment

        response = await self.client.embeddings.create(
            model=deployment,
            input=texts,
            **kwargs,
        )

        return [
            EmbeddingResponse(
                embedding=data.embedding,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )
            for data in response.data
        ]

    async def close(self) -> None:
        """Clean up resources."""
        await self.client.close()
