"""GCP Vertex AI provider implementation."""

from collections.abc import AsyncIterator
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from grc_ai.base import (
    AIProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
    MessageRole,
)
from grc_ai.config import GCPVertexConfig


class GCPVertexProvider(AIProvider):
    """GCP Vertex AI provider (supports Gemini models)."""

    def __init__(self, config: GCPVertexConfig) -> None:
        """Initialize GCP Vertex AI provider.

        Args:
            config: GCP Vertex AI configuration
        """
        self.config = config
        self._initialized = False
        self._model = None
        self._embedding_model = None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of Vertex AI."""
        if self._initialized:
            return

        import vertexai
        from vertexai.generative_models import GenerativeModel
        from vertexai.language_models import TextEmbeddingModel

        vertexai.init(
            project=self.config.project_id,
            location=self.config.location,
        )

        self._model = GenerativeModel(self.config.model_name)
        self._embedding_model = TextEmbeddingModel.from_pretrained(
            self.config.embedding_model
        )
        self._initialized = True

    def _convert_messages_to_gemini(
        self, messages: list[ChatMessage]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert ChatMessage list to Gemini format."""
        from vertexai.generative_models import Content, Part

        system_instruction = None
        contents = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_instruction = msg.content
            else:
                role = "user" if msg.role == MessageRole.USER else "model"
                contents.append(
                    Content(role=role, parts=[Part.from_text(msg.content)])
                )

        return system_instruction, contents

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
        """Generate a chat completion using GCP Vertex AI."""
        import asyncio

        from vertexai.generative_models import GenerationConfig, GenerativeModel

        self._ensure_initialized()

        system_instruction, contents = self._convert_messages_to_gemini(messages)

        # Create model with system instruction if provided
        if model or system_instruction:
            model_instance = GenerativeModel(
                model or self.config.model_name,
                system_instruction=system_instruction,
            )
        else:
            model_instance = self._model

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model_instance.generate_content(
                contents,
                generation_config=generation_config,
            ),
        )

        return ChatResponse(
            content=response.text,
            model=model or self.config.model_name,
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else None,
            usage={
                "prompt_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "completion_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0,
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
        """Stream a chat completion using GCP Vertex AI."""
        import asyncio

        from vertexai.generative_models import GenerationConfig, GenerativeModel

        self._ensure_initialized()

        system_instruction, contents = self._convert_messages_to_gemini(messages)

        if model or system_instruction:
            model_instance = GenerativeModel(
                model or self.config.model_name,
                system_instruction=system_instruction,
            )
        else:
            model_instance = self._model

        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        loop = asyncio.get_event_loop()
        responses = await loop.run_in_executor(
            None,
            lambda: model_instance.generate_content(
                contents,
                generation_config=generation_config,
                stream=True,
            ),
        )

        for response in responses:
            if response.text:
                yield ChatChunk(
                    content=response.text,
                    finish_reason=None,
                    is_final=False,
                )

        yield ChatChunk(
            content="",
            finish_reason="stop",
            is_final=True,
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
        """Generate an embedding using GCP Vertex AI."""
        import asyncio

        from vertexai.language_models import TextEmbeddingModel

        self._ensure_initialized()

        if model:
            embedding_model = TextEmbeddingModel.from_pretrained(model)
        else:
            embedding_model = self._embedding_model

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: embedding_model.get_embeddings([text]),
        )

        return EmbeddingResponse(
            embedding=embeddings[0].values,
            model=model or self.config.embedding_model,
            usage={},
        )

    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        **kwargs,
    ) -> list[EmbeddingResponse]:
        """Generate embeddings for multiple texts."""
        import asyncio

        from vertexai.language_models import TextEmbeddingModel

        self._ensure_initialized()

        if model:
            embedding_model = TextEmbeddingModel.from_pretrained(model)
        else:
            embedding_model = self._embedding_model

        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: embedding_model.get_embeddings(texts),
        )

        return [
            EmbeddingResponse(
                embedding=emb.values,
                model=model or self.config.embedding_model,
                usage={},
            )
            for emb in embeddings
        ]

    async def close(self) -> None:
        """Clean up resources."""
        # Vertex AI doesn't need explicit cleanup
        pass
