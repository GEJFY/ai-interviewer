"""Real-time transcription service for interviews.

Handles audio streaming from WebSocket connections and integrates
with the speech abstraction layer for multi-cloud STT support.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, Callable
from uuid import UUID, uuid4

from grc_ai.speech import (
    AudioFormat,
    SpeechLanguage,
    TranscriptionResult,
    create_speech_to_text,
    SpeechProviderType,
)

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSession:
    """Represents an active transcription session."""

    session_id: UUID
    interview_id: UUID
    language: SpeechLanguage
    provider_type: SpeechProviderType
    started_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    _audio_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    _transcription_task: asyncio.Task | None = None


class TranscriptionService:
    """Service for managing real-time transcription sessions.

    Supports multiple concurrent transcription sessions and integrates
    with Azure, AWS, and GCP speech-to-text services.
    """

    def __init__(
        self,
        provider_type: SpeechProviderType | str = SpeechProviderType.AZURE,
        **provider_config,
    ):
        """Initialize the transcription service.

        Args:
            provider_type: The speech provider to use
            **provider_config: Provider-specific configuration
        """
        self.provider_type = (
            SpeechProviderType(provider_type)
            if isinstance(provider_type, str)
            else provider_type
        )
        self.provider_config = provider_config
        self._sessions: dict[UUID, TranscriptionSession] = {}
        self._callbacks: dict[UUID, list[Callable]] = {}

    def _create_stt_provider(self, language: SpeechLanguage):
        """Create a speech-to-text provider instance."""
        return create_speech_to_text(
            self.provider_type,
            default_language=language,
            **self.provider_config,
        )

    async def start_session(
        self,
        interview_id: UUID,
        language: SpeechLanguage = SpeechLanguage.JA,
        on_transcription: Callable[[TranscriptionResult], None] | None = None,
    ) -> UUID:
        """Start a new transcription session.

        Args:
            interview_id: The interview ID this session belongs to
            language: The primary language for transcription
            on_transcription: Callback for transcription results

        Returns:
            The session ID
        """
        session_id = uuid4()
        session = TranscriptionSession(
            session_id=session_id,
            interview_id=interview_id,
            language=language,
            provider_type=self.provider_type,
        )
        self._sessions[session_id] = session
        self._callbacks[session_id] = []

        if on_transcription:
            self._callbacks[session_id].append(on_transcription)

        logger.info(
            f"Started transcription session {session_id} for interview {interview_id}"
        )
        return session_id

    async def add_audio_chunk(
        self,
        session_id: UUID,
        audio_data: bytes,
        audio_format: AudioFormat = AudioFormat.WAV,
    ) -> None:
        """Add an audio chunk to the transcription queue.

        Args:
            session_id: The session ID
            audio_data: Raw audio bytes
            audio_format: The audio format
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_active:
            logger.warning(f"Invalid or inactive session: {session_id}")
            return

        await session._audio_queue.put((audio_data, audio_format))

    async def process_audio_stream(
        self,
        session_id: UUID,
    ) -> AsyncIterator[TranscriptionResult]:
        """Process the audio queue and yield transcription results.

        This is a generator that continuously processes audio chunks
        and yields transcription results as they become available.

        Args:
            session_id: The session ID

        Yields:
            TranscriptionResult objects as audio is processed
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return

        stt = self._create_stt_provider(session.language)

        while session.is_active:
            try:
                # Wait for audio chunk with timeout
                audio_data, audio_format = await asyncio.wait_for(
                    session._audio_queue.get(),
                    timeout=1.0,
                )

                # Process audio through STT provider
                result = await stt.transcribe(
                    audio_data=audio_data,
                    audio_format=audio_format,
                    language=session.language,
                )

                # Notify callbacks
                for callback in self._callbacks.get(session_id, []):
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                yield result

            except asyncio.TimeoutError:
                # No audio data, continue waiting
                continue
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                continue

    async def transcribe_single(
        self,
        session_id: UUID,
        audio_data: bytes,
        audio_format: AudioFormat = AudioFormat.WAV,
    ) -> TranscriptionResult | None:
        """Transcribe a single audio chunk immediately.

        This is a convenience method for non-streaming transcription.

        Args:
            session_id: The session ID
            audio_data: Raw audio bytes
            audio_format: The audio format

        Returns:
            TranscriptionResult or None if failed
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return None

        try:
            stt = self._create_stt_provider(session.language)
            result = await stt.transcribe(
                audio_data=audio_data,
                audio_format=audio_format,
                language=session.language,
            )

            # Notify callbacks
            for callback in self._callbacks.get(session_id, []):
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

            return result

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    async def stop_session(self, session_id: UUID) -> None:
        """Stop a transcription session.

        Args:
            session_id: The session ID to stop
        """
        session = self._sessions.get(session_id)
        if not session:
            return

        session.is_active = False

        # Cancel transcription task if running
        if session._transcription_task:
            session._transcription_task.cancel()
            try:
                await session._transcription_task
            except asyncio.CancelledError:
                pass

        del self._sessions[session_id]
        self._callbacks.pop(session_id, None)

        logger.info(f"Stopped transcription session {session_id}")

    def get_session(self, session_id: UUID) -> TranscriptionSession | None:
        """Get a transcription session by ID."""
        return self._sessions.get(session_id)

    def get_active_sessions(self) -> list[TranscriptionSession]:
        """Get all active transcription sessions."""
        return [s for s in self._sessions.values() if s.is_active]

    async def cleanup(self) -> None:
        """Clean up all sessions."""
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            await self.stop_session(session_id)
        logger.info("Cleaned up all transcription sessions")


# Singleton instance (configure via environment)
_transcription_service: TranscriptionService | None = None


def get_transcription_service() -> TranscriptionService:
    """Get or create the transcription service singleton."""
    global _transcription_service
    if _transcription_service is None:
        # TODO: Load configuration from environment/settings
        from grc_backend.config import settings

        provider_config = {}
        provider_type = SpeechProviderType.AZURE

        if hasattr(settings, "SPEECH_PROVIDER"):
            provider_type = SpeechProviderType(settings.SPEECH_PROVIDER)

        if provider_type == SpeechProviderType.AZURE:
            provider_config = {
                "subscription_key": getattr(settings, "AZURE_SPEECH_KEY", ""),
                "region": getattr(settings, "AZURE_SPEECH_REGION", "japaneast"),
            }
        elif provider_type == SpeechProviderType.AWS:
            provider_config = {
                "region_name": getattr(settings, "AWS_REGION", "ap-northeast-1"),
            }
        elif provider_type == SpeechProviderType.GCP:
            provider_config = {
                "project_id": getattr(settings, "GCP_PROJECT_ID", ""),
            }

        _transcription_service = TranscriptionService(
            provider_type=provider_type,
            **provider_config,
        )

    return _transcription_service
