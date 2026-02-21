"""WebSocket endpoint for real-time interview sessions."""

import base64
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from grc_ai.dialogue import InterviewAgent, InterviewContext
from grc_ai.speech.base import AudioFormat, TranscriptionResult
from grc_backend.api.deps import get_ai_provider, get_db
from grc_backend.config import get_settings
from grc_core.enums import InterviewStatus, Speaker
from grc_core.repositories import (
    InterviewRepository,
    TaskRepository,
    TemplateRepository,
    UserRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.agents: dict[str, InterviewAgent] = {}

    async def connect(self, interview_id: str, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[interview_id] = websocket

    def disconnect(self, interview_id: str):
        """Remove a WebSocket connection."""
        self.active_connections.pop(interview_id, None)
        self.agents.pop(interview_id, None)

    async def send_message(self, interview_id: str, message: dict[str, Any]):
        """Send a message to a specific connection."""
        websocket = self.active_connections.get(interview_id)
        if websocket:
            await websocket.send_json(message)

    def get_agent(self, interview_id: str) -> InterviewAgent | None:
        """Get the interview agent for a session."""
        return self.agents.get(interview_id)

    def set_agent(self, interview_id: str, agent: InterviewAgent):
        """Set the interview agent for a session."""
        self.agents[interview_id] = agent


manager = ConnectionManager()


def _get_stt_provider(settings):
    """Get STT provider based on application settings.

    Returns None if no speech provider is configured.
    """
    try:
        from grc_ai.speech.factory import create_speech_to_text

        speech_provider = getattr(settings, "speech_provider", None)
        if not speech_provider:
            return None

        config = {}
        if speech_provider == "azure":
            config = {
                "subscription_key": getattr(settings, "azure_speech_key", ""),
                "region": getattr(settings, "azure_speech_region", "japaneast"),
            }
        elif speech_provider == "aws":
            config = {
                "region_name": getattr(settings, "aws_region", "ap-northeast-1"),
            }
        elif speech_provider == "gcp":
            config = {
                "project_id": getattr(settings, "gcp_project_id", ""),
            }
        else:
            return None

        return create_speech_to_text(speech_provider, **config)
    except Exception:
        logger.debug("STT provider not available", exc_info=True)
        return None


async def _authenticate_websocket(websocket: WebSocket, db: AsyncSession):
    """WebSocket接続時にJWTトークンを検証してユーザーを返す。

    クエリパラメータ ?token=xxx またはサブプロトコルからトークンを取得する。
    """
    settings = get_settings()

    # クエリパラメータからトークン取得
    token = websocket.query_params.get("token")

    if not token:
        # Sec-WebSocket-Protocol ヘッダーからの取得（ブラウザ対応）
        protocols = websocket.headers.get("sec-websocket-protocol", "")
        for proto in protocols.split(","):
            proto = proto.strip()
            if proto.startswith("access_token."):
                token = proto[len("access_token.") :]
                break

    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return None

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return None

        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return None

        user_repo = UserRepository(db)
        user = await user_repo.get(user_id)
        if not user:
            await websocket.close(code=4001, reason="User not found")
            return None

        return user

    except JWTError:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return None


@router.websocket("/{interview_id}/stream")
async def interview_websocket(
    websocket: WebSocket,
    interview_id: str,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for real-time interview interaction.

    Authentication: クエリパラメータ ?token=<JWT> でアクセストークンを渡す。

    Message format (client -> server):
    {
        "type": "message" | "audio_chunk" | "control",
        "payload": {
            "content": "text message",  // for type: message
            "audio": "base64 encoded",  // for type: audio_chunk
            "action": "pause" | "resume" | "end"  // for type: control
        }
    }

    Message format (server -> client):
    {
        "type": "ai_response" | "transcription" | "status" | "error" | "time_warning" | "coverage_update",
        "payload": { ... }
    }
    """
    # JWT認証
    current_user = await _authenticate_websocket(websocket, db)
    if current_user is None:
        return

    settings = get_settings()
    ai_provider = get_ai_provider(settings)

    # Verify interview exists
    interview_repo = InterviewRepository(db)
    interview = await interview_repo.get(interview_id)

    if not interview:
        await websocket.close(code=4004, reason="Interview not found")
        return

    # Connect
    await manager.connect(interview_id, websocket)

    try:
        # Get template questions
        task_repo = TaskRepository(db)
        task = await task_repo.get(interview.task_id)

        questions = []
        if task and task.template_id:
            template_repo = TemplateRepository(db)
            template = await template_repo.get(task.template_id)
            if template:
                questions = [q.get("question", "") for q in template.questions]

        # Read duration setting
        duration_minutes = (
            task.settings.get("duration_minutes", 30) if task and task.settings else 30
        )
        interview_start_time = time.time()

        # Create interview context
        org_name = getattr(current_user, "organization_name", None) or "Organization"
        context = InterviewContext(
            interview_id=interview_id,
            organization_name=org_name,
            use_case_type=task.use_case_type if task else "general",
            interview_purpose=task.description if task else "Interview",
            questions=questions or ["一般的なヒアリングを行います。"],
            is_anonymous=task.settings.get("anonymous_mode", False) if task else False,
            language=interview.language,
            metadata={"duration_minutes": duration_minutes},
        )

        # Create interview agent
        agent = InterviewAgent(ai_provider, context)
        manager.set_agent(interview_id, agent)

        # Load carry-over context from previous session if available
        if interview.extra_metadata and interview.extra_metadata.get("carry_over"):
            agent.load_carry_over(interview.extra_metadata["carry_over"])

        # Track which time warnings have been sent
        time_warnings_sent: set[str] = set()
        # Track user message count for periodic coverage assessment
        user_message_count = 0
        coverage_check_interval = 5

        # Send status with duration info
        await manager.send_message(
            interview_id,
            {
                "type": "status",
                "payload": {
                    "status": "connected",
                    "interview_id": interview_id,
                    "duration_minutes": duration_minutes,
                },
            },
        )

        # Start interview if not already started
        if interview.status == InterviewStatus.SCHEDULED:
            opening = await agent.start()

            # Update interview status
            await interview_repo.start(interview_id)

            # Save opening to transcript
            await interview_repo.add_transcript_entry(
                interview_id=interview_id,
                speaker=Speaker.AI,
                content=opening,
                timestamp_ms=agent.history[0].timestamp_ms,
            )

            await db.commit()

            # Send opening message
            await manager.send_message(
                interview_id, {"type": "ai_response", "payload": {"content": opening}}
            )

        # Main message loop
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            payload = data.get("payload", {})

            if msg_type == "message":
                # Text message from user
                user_content = payload.get("content", "")
                user_message_count += 1

                # Save user message to transcript
                timestamp = int(time.time() * 1000)

                await interview_repo.add_transcript_entry(
                    interview_id=interview_id,
                    speaker=Speaker.INTERVIEWEE,
                    content=user_content,
                    timestamp_ms=timestamp,
                )

                # Send transcription confirmation
                await manager.send_message(
                    interview_id,
                    {
                        "type": "transcription",
                        "payload": {
                            "speaker": "interviewee",
                            "text": user_content,
                            "timestamp": timestamp,
                            "isFinal": True,
                        },
                    },
                )

                # Get AI response (streaming)
                full_response = ""
                async for chunk in agent.respond_stream(user_content):
                    full_response += chunk
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "ai_response",
                            "payload": {
                                "content": chunk,
                                "isPartial": True,
                            },
                        },
                    )

                # Save AI response to transcript
                await interview_repo.add_transcript_entry(
                    interview_id=interview_id,
                    speaker=Speaker.AI,
                    content=full_response,
                    timestamp_ms=int(time.time() * 1000),
                )

                await db.commit()

                # Send completion signal
                await manager.send_message(
                    interview_id,
                    {
                        "type": "ai_response",
                        "payload": {
                            "content": "",
                            "isPartial": False,
                            "isFinal": True,
                        },
                    },
                )

                # Check time warnings after each AI response
                elapsed_seconds = time.time() - interview_start_time
                remaining_seconds = (duration_minutes * 60) - elapsed_seconds

                if remaining_seconds <= 0 and "exceeded" not in time_warnings_sent:
                    time_warnings_sent.add("exceeded")
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "time_warning",
                            "payload": {
                                "level": "exceeded",
                                "remaining_seconds": 0,
                                "message": "設定時間を超過しました。",
                            },
                        },
                    )
                elif remaining_seconds <= 120 and "2min" not in time_warnings_sent:
                    time_warnings_sent.add("2min")
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "time_warning",
                            "payload": {
                                "level": "critical",
                                "remaining_seconds": int(remaining_seconds),
                                "message": "残り約2分です。",
                            },
                        },
                    )
                elif remaining_seconds <= 300 and "5min" not in time_warnings_sent:
                    time_warnings_sent.add("5min")
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "time_warning",
                            "payload": {
                                "level": "warning",
                                "remaining_seconds": int(remaining_seconds),
                                "message": "残り約5分です。",
                            },
                        },
                    )

                # Periodic coverage assessment
                if user_message_count % coverage_check_interval == 0:
                    try:
                        coverage = await agent.assess_coverage()
                        await manager.send_message(
                            interview_id,
                            {
                                "type": "coverage_update",
                                "payload": coverage,
                            },
                        )
                        if coverage.get("suggest_end"):
                            await manager.send_message(
                                interview_id,
                                {
                                    "type": "status",
                                    "payload": {
                                        "status": "suggest_end",
                                        "message": "十分な情報が得られました。終了を検討してください。",
                                    },
                                },
                            )
                    except Exception:
                        logger.warning(
                            "Coverage assessment failed for %s", interview_id, exc_info=True
                        )

            elif msg_type == "control":
                action = payload.get("action")

                if action == "pause":
                    await interview_repo.pause(interview_id)
                    await db.commit()
                    await manager.send_message(
                        interview_id, {"type": "status", "payload": {"status": "paused"}}
                    )

                elif action == "resume":
                    await interview_repo.resume(interview_id)
                    await db.commit()
                    await manager.send_message(
                        interview_id, {"type": "status", "payload": {"status": "resumed"}}
                    )

                elif action == "end":
                    # End interview
                    closing = await agent.end()
                    summary = await agent.summarize()

                    # Save closing to transcript
                    await interview_repo.add_transcript_entry(
                        interview_id=interview_id,
                        speaker=Speaker.AI,
                        content=closing,
                        timestamp_ms=int(time.time() * 1000),
                    )

                    # Generate carry-over context for future sessions
                    try:
                        coverage = await agent.assess_coverage()
                        carry_over = agent.generate_carry_over(coverage)
                    except Exception:
                        logger.warning(
                            "Carry-over generation failed for %s",
                            interview_id,
                            exc_info=True,
                        )
                        coverage = None
                        carry_over = agent.generate_carry_over()

                    # Save carry-over and coverage to extra_metadata
                    interview.extra_metadata = {
                        **(interview.extra_metadata or {}),
                        "carry_over": carry_over,
                        "final_coverage": coverage,
                    }

                    # Complete interview
                    await interview_repo.complete(
                        interview_id,
                        summary=summary.get("summary"),
                        ai_analysis=summary,
                    )

                    # Update task status
                    if task:
                        await task_repo.update_status(task.id)

                    await db.commit()

                    await manager.send_message(
                        interview_id, {"type": "ai_response", "payload": {"content": closing}}
                    )

                    await manager.send_message(
                        interview_id,
                        {
                            "type": "status",
                            "payload": {
                                "status": "completed",
                                "summary": summary,
                                "coverage": coverage,
                                "carry_over": carry_over,
                            },
                        },
                    )

                    break

            elif msg_type == "audio_chunk":
                # Decode audio and transcribe via STT
                audio_b64 = payload.get("audio", "")
                if not audio_b64:
                    continue

                try:
                    audio_bytes = base64.b64decode(audio_b64)
                except Exception:
                    continue

                # Try to get STT provider
                stt_provider = _get_stt_provider(settings)
                if stt_provider is None:
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "error",
                            "payload": {"message": "Speech-to-text provider not configured"},
                        },
                    )
                    continue

                try:
                    result: TranscriptionResult = await stt_provider.transcribe(
                        audio_bytes,
                        language=interview.language or "ja-JP",
                        format=AudioFormat.WEBM,
                    )

                    if result.text.strip():
                        # Send interim transcription
                        await manager.send_message(
                            interview_id,
                            {
                                "type": "transcription",
                                "payload": {
                                    "speaker": "interviewee",
                                    "text": result.text,
                                    "isFinal": result.is_final,
                                    "confidence": result.confidence,
                                },
                            },
                        )

                        # If final, process as a normal message
                        if result.is_final:
                            user_message_count += 1
                            timestamp = int(time.time() * 1000)

                            await interview_repo.add_transcript_entry(
                                interview_id=interview_id,
                                speaker=Speaker.INTERVIEWEE,
                                content=result.text,
                                timestamp_ms=timestamp,
                            )

                            # Get AI response (streaming)
                            full_response = ""
                            async for chunk in agent.respond_stream(result.text):
                                full_response += chunk
                                await manager.send_message(
                                    interview_id,
                                    {
                                        "type": "ai_response",
                                        "payload": {
                                            "content": chunk,
                                            "isPartial": True,
                                        },
                                    },
                                )

                            await interview_repo.add_transcript_entry(
                                interview_id=interview_id,
                                speaker=Speaker.AI,
                                content=full_response,
                                timestamp_ms=int(time.time() * 1000),
                            )
                            await db.commit()

                            await manager.send_message(
                                interview_id,
                                {
                                    "type": "ai_response",
                                    "payload": {
                                        "content": "",
                                        "isPartial": False,
                                        "isFinal": True,
                                    },
                                },
                            )

                except Exception:
                    logger.warning(
                        "STT processing failed for %s",
                        interview_id,
                        exc_info=True,
                    )
                    await manager.send_message(
                        interview_id,
                        {
                            "type": "error",
                            "payload": {"message": "音声認識処理に失敗しました"},
                        },
                    )

    except WebSocketDisconnect:
        manager.disconnect(interview_id)

    except Exception as e:
        await manager.send_message(interview_id, {"type": "error", "payload": {"message": str(e)}})
        manager.disconnect(interview_id)

    finally:
        await ai_provider.close()
