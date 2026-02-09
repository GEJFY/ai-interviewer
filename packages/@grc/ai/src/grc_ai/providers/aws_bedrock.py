"""AWS Bedrock provider implementation."""

import json
from collections.abc import AsyncIterator
from typing import Any

import boto3
from botocore.config import Config
from tenacity import retry, stop_after_attempt, wait_exponential

from grc_ai.base import (
    AIProvider,
    ChatChunk,
    ChatMessage,
    ChatResponse,
    EmbeddingResponse,
    MessageRole,
)
from grc_ai.config import AWSBedrockConfig


class AWSBedrockProvider(AIProvider):
    """AWS Bedrock API provider (supports Claude models)."""

    def __init__(self, config: AWSBedrockConfig) -> None:
        """Initialize AWS Bedrock provider.

        Args:
            config: AWS Bedrock configuration
        """
        self.config = config

        boto_config = Config(
            region_name=config.region,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        session_kwargs: dict[str, Any] = {}
        if config.access_key_id and config.secret_access_key:
            session_kwargs["aws_access_key_id"] = config.access_key_id
            session_kwargs["aws_secret_access_key"] = config.secret_access_key

        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime", config=boto_config)

    def _convert_messages_to_bedrock(
        self, messages: list[ChatMessage]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        """Convert ChatMessage list to Bedrock format."""
        system_prompt = None
        bedrock_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_prompt = msg.content
            else:
                bedrock_messages.append({
                    "role": msg.role.value,
                    "content": [{"type": "text", "text": msg.content}],
                })

        return system_prompt, bedrock_messages

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
        """Generate a chat completion using AWS Bedrock."""
        model_id = model or self.config.model_id
        system_prompt, bedrock_messages = self._convert_messages_to_bedrock(messages)

        request_body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": bedrock_messages,
            "temperature": temperature,
        }

        if system_prompt:
            request_body["system"] = system_prompt

        # Bedrock is synchronous, run in thread pool
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
            ),
        )

        response_body = json.loads(response["body"].read())

        content = ""
        if response_body.get("content"):
            content = response_body["content"][0].get("text", "")

        return ChatResponse(
            content=content,
            model=model_id,
            finish_reason=response_body.get("stop_reason"),
            usage={
                "prompt_tokens": response_body.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response_body.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    response_body.get("usage", {}).get("input_tokens", 0)
                    + response_body.get("usage", {}).get("output_tokens", 0)
                ),
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
        """Stream a chat completion using AWS Bedrock."""
        import asyncio

        model_id = model or self.config.model_id
        system_prompt, bedrock_messages = self._convert_messages_to_bedrock(messages)

        request_body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": bedrock_messages,
            "temperature": temperature,
        }

        if system_prompt:
            request_body["system"] = system_prompt

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(request_body),
            ),
        )

        stream = response.get("body")
        if stream:
            for event in stream:
                chunk = event.get("chunk")
                if chunk:
                    chunk_data = json.loads(chunk.get("bytes").decode())
                    if chunk_data.get("type") == "content_block_delta":
                        delta = chunk_data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield ChatChunk(
                                content=delta.get("text", ""),
                                finish_reason=None,
                                is_final=False,
                            )
                    elif chunk_data.get("type") == "message_stop":
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
        """Generate an embedding using AWS Bedrock (Titan)."""
        import asyncio

        model_id = model or self.config.embedding_model_id

        request_body = {
            "inputText": text,
        }

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body),
            ),
        )

        response_body = json.loads(response["body"].read())

        return EmbeddingResponse(
            embedding=response_body.get("embedding", []),
            model=model_id,
            usage={"total_tokens": response_body.get("inputTextTokenCount", 0)},
        )

    async def embed_batch(
        self,
        texts: list[str],
        *,
        model: str | None = None,
        **kwargs,
    ) -> list[EmbeddingResponse]:
        """Generate embeddings for multiple texts (sequential for Bedrock)."""
        return [await self.embed(text, model=model, **kwargs) for text in texts]

    async def close(self) -> None:
        """Clean up resources."""
        # Boto3 client doesn't need explicit cleanup
        pass
