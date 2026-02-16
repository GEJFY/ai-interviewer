"""Interview agent for conducting AI-powered interviews."""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from grc_ai.base import AIProvider, ChatMessage, MessageRole
from grc_ai.dialogue.prompts import PromptManager


class InterviewPhase(StrEnum):
    """Interview phase enum."""

    ICE_BREAKING = "ice_breaking"
    MAIN = "main"
    DEEP_DIVE = "deep_dive"
    CLOSING = "closing"


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

        # Phase tracking
        self.phase = InterviewPhase.ICE_BREAKING

        # State tracking
        self.current_question_index = 0
        self.is_started = False
        self.is_completed = False

    def _get_phase_hint(self) -> str:
        """Determine the current interview phase hint based on conversation progress.

        Returns:
            Phase hint string to inject into the system prompt
        """
        user_turns = sum(1 for t in self.history if t.role == "user")
        total_questions = len(self.context.questions)

        if user_turns == 0:
            self.phase = InterviewPhase.ICE_BREAKING
            return "フェーズ1: アイスブレイク（導入）— 自己紹介と挨拶から始めてください。場を和ませ、安心感を与えることが最優先です。"

        if user_turns <= 2:
            self.phase = InterviewPhase.ICE_BREAKING
            return "フェーズ1: アイスブレイク（導入）— まだ導入フェーズです。ラポール（信頼関係）の構築に努め、自然に本題へ遷移してください。"

        # Estimate question coverage based on conversation length
        coverage_ratio = min(user_turns / max(total_questions * 2, 1), 1.0)

        if coverage_ratio < 0.6:
            self.phase = InterviewPhase.MAIN
            return (
                f"フェーズ2: 本題（メイン質問）— 質問リストに沿って自然な会話で進めてください。"
                f"会話ターン数: {user_turns}, 質問数: {total_questions}"
            )

        if coverage_ratio < 0.85:
            self.phase = InterviewPhase.DEEP_DIVE
            return (
                f"フェーズ3: 深掘り（フォローアップ）— 重要な回答を掘り下げ、具体例やエピソードを引き出してください。"
                f"会話ターン数: {user_turns}, 質問数: {total_questions}"
            )

        self.phase = InterviewPhase.CLOSING
        return (
            "フェーズ4: クロージング（まとめ）— 要点を振り返り、追加コメントの機会を設けて、"
            "感謝を伝えて丁寧にインタビューを終了してください。"
        )

    def _get_time_hint(self) -> str:
        """Generate time management hint based on elapsed time and duration setting.

        Returns:
            Time hint string to inject into the system prompt
        """
        duration_minutes = self.context.metadata.get("duration_minutes", 30)
        total_questions = len(self.context.questions)

        if not self.is_started:
            return (
                f"インタビュー時間は{duration_minutes}分です。"
                f"質問数は{total_questions}問あるため、ペース配分に注意してください。"
            )

        # Calculate elapsed time from first history entry
        if not self.history:
            return f"インタビュー時間は{duration_minutes}分です。"

        start_ms = self.history[0].timestamp_ms
        elapsed_ms = self._get_timestamp() - start_ms
        elapsed_minutes = elapsed_ms / 60000
        remaining_minutes = duration_minutes - elapsed_minutes

        if remaining_minutes <= 0:
            return (
                "【時間超過】設定時間を超過しています。"
                "重要な未確認事項があれば簡潔に確認し、次回への持ち越しを提案してまとめに入ってください。"
            )

        if remaining_minutes <= 2:
            return (
                f"【残り約{int(remaining_minutes)}分】まもなく時間です。"
                "今すぐクロージング（要点の振り返り・感謝）に入ってください。"
            )

        if remaining_minutes <= 5:
            return (
                f"【残り約{int(remaining_minutes)}分】時間が残りわずかです。"
                "まとめに入る準備をしてください。重要な未確認事項を優先し、深掘りは控えてください。"
            )

        return (
            f"経過: 約{int(elapsed_minutes)}分 / 設定: {duration_minutes}分（残り約{int(remaining_minutes)}分）。"
            "ペース配分に注意して進めてください。"
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt with current phase and time hints."""
        return PromptManager.get_system_prompt(
            organization_name=self.context.organization_name,
            use_case_type=self.context.use_case_type,
            interview_purpose=self.context.interview_purpose,
            questions=self.context.questions,
            is_anonymous=self.context.is_anonymous,
            phase_hint=self._get_phase_hint(),
            time_hint=self._get_time_hint(),
        )

    def _build_messages(self) -> list[ChatMessage]:
        """Build message list for the AI provider."""
        system_prompt = self._build_system_prompt()
        messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]

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

        # Read duration from task settings if available
        duration_minutes = self.context.metadata.get("duration_minutes", 30)
        estimated_duration = f"約{duration_minutes}分"

        # Generate opening message
        opening_prompt = PromptManager.GENERATE_OPENING.format(
            interviewer_name="AI インタビュアー",
            purpose=self.context.interview_purpose,
            estimated_duration=estimated_duration,
            anonymity_note="このインタビューは匿名です。"
            if self.context.is_anonymous
            else "回答は記録されます。",
        )

        system_prompt = self._build_system_prompt()
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
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
            f"{'AI' if turn.role == 'ai' else '回答者'}: {turn.content}" for turn in self.history
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

    async def assess_coverage(self) -> dict[str, Any]:
        """Assess question coverage by asking the AI to analyze the conversation.

        Returns:
            Coverage assessment with per-question status and overall percentage
        """
        if not self.history:
            return {
                "overall_percentage": 0,
                "questions": [
                    {"question": q, "status": "unanswered", "percentage": 0}
                    for q in self.context.questions
                ],
                "suggest_end": False,
            }

        transcript_text = "\n".join(
            f"{'AI' if t.role == 'ai' else '回答者'}: {t.content}" for t in self.history
        )
        questions_text = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(self.context.questions))

        prompt = f"""以下のインタビュー記録と質問リストを分析し、各質問のカバレッジを評価してください。

## 質問リスト
{questions_text}

## インタビュー記録
{transcript_text}

## 出力形式（JSON）
{{
    "overall_percentage": 0-100の数値,
    "questions": [
        {{"question": "質問文", "status": "answered|partial|unanswered", "percentage": 0-100}}
    ],
    "suggest_end": true/false（90%以上でtrue）
}}
"""
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="JSONフォーマットで出力してください。"),
            ChatMessage(role=MessageRole.USER, content=prompt),
        ]

        response = await self.provider.chat(
            messages,
            temperature=0.2,
            max_tokens=2048,
        )

        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: estimate from conversation length
            user_turns = sum(1 for t in self.history if t.role == "user")
            total_q = len(self.context.questions)
            estimated = min(int((user_turns / max(total_q * 2, 1)) * 100), 100)
            return {
                "overall_percentage": estimated,
                "questions": [
                    {"question": q, "status": "unknown", "percentage": estimated}
                    for q in self.context.questions
                ],
                "suggest_end": estimated >= 90,
            }

    def generate_carry_over(self, coverage: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate carry-over context for the next interview session.

        Args:
            coverage: Optional coverage assessment from assess_coverage()

        Returns:
            Carry-over context to store in Interview.extra_metadata
        """
        # Collect key points from AI messages
        ai_messages = [t.content for t in self.history if t.role == "ai"]
        user_messages = [t.content for t in self.history if t.role == "user"]

        # Determine unanswered questions
        unanswered: list[str] = []
        if coverage and "questions" in coverage:
            unanswered = [
                q["question"]
                for q in coverage["questions"]
                if q.get("status") in ("unanswered", "partial")
            ]
        else:
            # Simple fallback: assume later questions are less covered
            user_turns = len(user_messages)
            total_q = len(self.context.questions)
            covered_count = min(user_turns, total_q)
            unanswered = self.context.questions[covered_count:]

        return {
            "carry_over": True,
            "previous_interview_id": self.context.interview_id,
            "coverage_percentage": coverage.get("overall_percentage", 0) if coverage else 0,
            "unanswered_questions": unanswered,
            "key_topics_discussed": ai_messages[:3] if ai_messages else [],
            "total_turns": len(self.history),
            "message": "前回のインタビューからの持ち越しコンテキストです。",
        }

    def load_carry_over(self, carry_over: dict[str, Any]) -> None:
        """Load carry-over context from a previous interview session.

        Injects previous context into the metadata so prompts can reference it.

        Args:
            carry_over: Carry-over context from previous session
        """
        self.context.metadata["carry_over"] = carry_over

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
