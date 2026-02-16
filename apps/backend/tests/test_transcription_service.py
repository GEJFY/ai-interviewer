"""Unit tests for TranscriptionService."""

from uuid import uuid4

import pytest

from grc_ai.speech import SpeechLanguage, SpeechProviderType
from grc_backend.services.transcription_service import TranscriptionService, TranscriptionSession


class TestTranscriptionServiceInit:
    """Tests for service initialisation."""

    def test_default_provider(self):
        """Defaults to Azure provider."""
        service = TranscriptionService()
        assert service.provider_type == SpeechProviderType.AZURE

    def test_string_provider(self):
        """Accepts provider type as string."""
        service = TranscriptionService(provider_type="azure")
        assert service.provider_type == SpeechProviderType.AZURE

    def test_enum_provider(self):
        """Accepts provider type as enum."""
        service = TranscriptionService(provider_type=SpeechProviderType.AWS)
        assert service.provider_type == SpeechProviderType.AWS

    def test_extra_config_stored(self):
        """Extra kwargs are stored in provider_config."""
        service = TranscriptionService(region="ap-northeast-1")
        assert service.provider_config == {"region": "ap-northeast-1"}


class TestSessionLifecycle:
    """Tests for session start / stop / cleanup."""

    @pytest.fixture
    def service(self):
        return TranscriptionService()

    @pytest.mark.asyncio
    async def test_start_session_returns_uuid(self, service):
        interview_id = uuid4()
        session_id = await service.start_session(interview_id)
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_get_session(self, service):
        interview_id = uuid4()
        session_id = await service.start_session(interview_id)
        session = service.get_session(session_id)

        assert isinstance(session, TranscriptionSession)
        assert session.interview_id == interview_id
        assert session.is_active is True

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, service):
        assert service.get_session(uuid4()) is None

    @pytest.mark.asyncio
    async def test_get_active_sessions(self, service):
        id1 = uuid4()
        id2 = uuid4()
        await service.start_session(id1)
        await service.start_session(id2)
        assert len(service.get_active_sessions()) == 2

    @pytest.mark.asyncio
    async def test_stop_session_removes(self, service):
        session_id = await service.start_session(uuid4())
        await service.stop_session(session_id)

        assert service.get_session(session_id) is None
        assert len(service.get_active_sessions()) == 0

    @pytest.mark.asyncio
    async def test_stop_unknown_session_noop(self, service):
        """Stopping a non-existent session should not raise."""
        await service.stop_session(uuid4())

    @pytest.mark.asyncio
    async def test_cleanup_all(self, service):
        await service.start_session(uuid4())
        await service.start_session(uuid4())
        await service.start_session(uuid4())
        assert len(service.get_active_sessions()) == 3

        await service.cleanup()
        assert len(service.get_active_sessions()) == 0

    @pytest.mark.asyncio
    async def test_session_language(self, service):
        session_id = await service.start_session(uuid4(), language=SpeechLanguage.EN)
        session = service.get_session(session_id)
        assert session.language == SpeechLanguage.EN


class TestAudioChunks:
    """Tests for audio chunk queueing."""

    @pytest.fixture
    def service(self):
        return TranscriptionService()

    @pytest.mark.asyncio
    async def test_add_chunk_to_queue(self, service):
        session_id = await service.start_session(uuid4())
        await service.add_audio_chunk(session_id, b"\x00\x01\x02")

        session = service.get_session(session_id)
        assert session._audio_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_add_chunk_invalid_session(self, service):
        """Adding to a non-existent session should not raise."""
        await service.add_audio_chunk(uuid4(), b"\x00")

    @pytest.mark.asyncio
    async def test_add_chunk_after_stop(self, service):
        """Adding to a stopped session should not raise."""
        session_id = await service.start_session(uuid4())
        await service.stop_session(session_id)
        await service.add_audio_chunk(session_id, b"\x00")


class TestCallbacks:
    """Tests for transcription callback registration."""

    @pytest.fixture
    def service(self):
        return TranscriptionService()

    @pytest.mark.asyncio
    async def test_callback_registered(self, service):
        received = []
        session_id = await service.start_session(
            uuid4(),
            on_transcription=lambda r: received.append(r),
        )
        assert len(service._callbacks[session_id]) == 1

    @pytest.mark.asyncio
    async def test_no_callback(self, service):
        session_id = await service.start_session(uuid4())
        assert len(service._callbacks[session_id]) == 0
