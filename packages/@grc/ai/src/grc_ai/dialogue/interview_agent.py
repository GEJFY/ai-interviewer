"""Interview agent for conducting AI-powered interviews."""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from grc_ai.base import AIProvider, ChatMessage, MessageRole
from grc_ai.dialogue.prompts import PromptManager


@dataclass
class InterviewContext:
    """Context for an interview session."""

    interview_id: str
    organization_name: str
    use_case_type: str
    interview_purpose: str
    questions: list[str]
    is_anonymous: bool = False
    language: str = "ja"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogueTurn:
    """A single turn in the dialogue."""

    role: str  # "ai" or "user"
    content: str
    timestamp_ms: int


class InterviewAgent:
    """Agent for conducting AI-powered interviews."""

    def __init__(
        self,
        provider: AIProvider,
        context: InterviewContext,
        *,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        """Initialize interview agent.

        Args:
            provider: AI provider to use
            context: Interview context
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
        """
        self.provider = provider
        self.context = context
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Conversation history
        self.history: list[DialogueTurn] = []

        # System prompt
        self.system_prompt = PromptManager.get_system_prompt(
            organization_name=context.organization_name,
            use_case_type=context.use_case_type,
            interview_purpose=context.interview_purpose,
            questions=context.questions,
            is_anonymous=context.is_anonymous,
        )

        # State tracking
        self.current_question_index = 0
        self.is_started = False
        self.is_completed = False

    def _build_messages(self) -> list[ChatMessage]:
        """Build message list for the AI provider."""
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=self.system_prompt)
        ]

        for turn in self.history:
            role = MessageRole.ASSISTANT if turn.role == "ai" else MessageRole.USER
            messages.append(ChatMessage(role=role, content=turn.content))

        return messages

    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        import time
        return int(time.time() * 1000)

    async def start(self) -> str:
        """Start the interview with an opening message.

        Returns:
            Opening message from the AI
        """
        if self.is_started:
            raise RuntimeError("Interview already started")

        # Generate opening message
        opening_prompt = PromptManager.GENERATE_OPENING.format(
            interviewer_name="AI インタビュアー",
            purpose=self.context.interview_purpose,
            estimated_duration="約15-30分",
            anonymity_note="このインタビューは匿名です。" if self.context.is_anonymous else "回答は記録されます。",
        )

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=self.system_prompt),
            ChatMessage(role=MessageRole.USER, content=opening_prompt),
        ]

        response = await self.provider.chat(
            messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Record the turn
        self.history.append(
            DialogueTurn(
                role="ai",
                content=response.content,
                timestamp_ms=self._get_timestamp(),
            )
        )

        self.is_started = True
        return response.content

    async def respond(self, user_message: str) -> str:
        """Process user message and generate AI response.

        Args:
            user_message: Message from the user

        Returns:
            AI response
        """
        if not self.is_started:
            raise RuntimeError("Interview not started. Call start() first.")

        if self.is_completed:
            raise RuntimeError("Interview already completed")

        # Record user turn
        self.history.append(
            DialogueTurn(
                role="user",
                content=user_message,
                timestamp_ms=self._get_timestamp(),
            )
        )

        # Generate response
        messages = self._build_messages()
        response = await self.provider.chat(
            messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        # Record AI turn
        self.history.append(
            DialogueTurn(
                role="ai",
                content=response.content,
                timestamp_ms=self._get_timestamp(),
            )
        )

        return response.content

    async def respond_stream(self, user_message: str) -> AsyncIterator[str]:
        """Process user message and stream AI response.

        Args:
            user_message: Message from the user

        Yields:
            Chunks of AI response
        """
        if not self.is_started:
            raise RuntimeError("Interview not started. Call start() first.")

        if self.is_completed:
            raise RuntimeError("Interview already completed")

        # Record user turn
        self.history.append(
            DialogueTurn(
                role="user",
                content=user_message,
                timestamp_ms=self._get_timestamp(),
            )
        )

        # Stream response
        messages = self._build_messages()
        full_response = ""

        async for chunk in self.provider.stream_chat(
            messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ):
            full_response += chunk.content
            yield chunk.content

        # Record AI turn
        self.history.append(
            DialogueTurn(
                role="ai",
                content=full_response,
                timestamp_ms=self._get_timestamp(),
            )
        )

    async def end(self) -> str:
        """End the interview with a closing message.

        Returns:
            Closing message from the AI
        """
        if self.is_completed:
            raise RuntimeError("Interview already completed")

        # Generate summary first
        summary = await self.summarize()

        # Generate closing message
        closing_prompt = PromptManager.GENERATE_CLOSING.format(
            key_points="\n".join(f"- {f}" for f in summary.get("key_findings", [])),
            next_steps="分析結果は後日共有されます。",
        )

        messages = self._build_messages()
        messages.append(ChatMessage(role=MessageRole.USER, content=closing_prompt))

        response = await self.provider.chat(
            messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        self.is_completed = True
        return response.content

    async def summarize(self) -> dict[str, Any]:
        """Generate a summary of the interview.

        Returns:
            Summary dictionary with key findings, risks, and follow-ups
        """
        # Build transcript text
        transcript_text = "\n\n".join(
            f"{'AI' if turn.role == 'ai' else '回答者'}: {turn.content}"
            for turn in self.history
        )

        prompt = PromptManager.SUMMARIZE_INTERVIEW.format(
            purpose=self.context.interview_purpose,
            transcript=transcript_text,
        )

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="JSONフォーマットで出力してください。"),
            ChatMessage(role=MessageRole.USER, content=prompt),
        ]

        response = await self.provider.chat(
            messages,
            temperature=0.3,  # Lower temperature for structured output
            max_tokens=2048,
        )

        try:
            # Try to parse JSON from response
            content = response.content.strip()
            # Handle markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError:
            # Return a basic structure if parsing fails
            return {
                "summary": response.content[:200],
                "key_findings": [],
                "risks_identified": [],
                "follow_up_items": [],
                "sentiment": "neutral",
            }

    def get_transcript(self) -> list[dict[str, Any]]:
        """Get the full transcript of the interview.

        Returns:
            List of dialogue turns as dictionaries
        """
        return [
            {
                "role": turn.role,
                "content": turn.content,
                "timestamp_ms": turn.timestamp_ms,
            }
            for turn in self.history
        ]
