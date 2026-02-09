"""Text-to-speech synthesis service for interviews.

Handles audio generation for AI responses using the multi-cloud
speech abstraction layer.
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from grc_ai.speech import (
    AudioFormat,
    SpeechLanguage,
    SpeechProviderType,
    SynthesisResult,
    VoiceInfo,
    create_text_to_speech,
)

logger = logging.getLogger(__name__)


@dataclass
class VoiceSettings:
    """Voice configuration for synthesis."""

    voice_id: str | None = None
    language: SpeechLanguage = SpeechLanguage.JA
    speaking_rate: float = 1.0  # 0.5 to 2.0
    pitch: float = 0.0  # -20.0 to 20.0 semitones


class SynthesisService:
    """Service for text-to-speech synthesis.

    Provides audio generation capabilities using Azure, AWS, or GCP
    text-to-speech services.
    """

    def __init__(
        self,
        provider_type: SpeechProviderType | str = SpeechProviderType.AZURE,
        **provider_config,
    ):
        """Initialize the synthesis service.

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
        self._default_voices: dict[SpeechLanguage, str] = {}
        self._voice_cache: list[VoiceInfo] = []

    def _create_tts_provider(self, language: SpeechLanguage | None = None):
        """Create a text-to-speech provider instance."""
        return create_text_to_speech(
            self.provider_type,
            default_language=language,
            **self.provider_config,
        )

    async def synthesize(
        self,
        text: str,
        settings: VoiceSettings | None = None,
        output_format: AudioFormat = AudioFormat.MP3,
    ) -> SynthesisResult:
        """Synthesize speech from text.

        Args:
            text: The text to synthesize
            settings: Voice settings (uses defaults if not provided)
            output_format: The desired audio format

        Returns:
            SynthesisResult containing audio data
        """
        settings = settings or VoiceSettings()

        tts = self._create_tts_provider(settings.language)

        # Get voice ID, using default for language if not specified
        voice_id = settings.voice_id
        if not voice_id:
            voice_id = await self._get_default_voice(settings.language)

        result = await tts.synthesize(
            text=text,
            voice_id=voice_id,
            output_format=output_format,
            language=settings.language,
        )

        return result

    async def synthesize_stream(
        self,
        text: str,
        settings: VoiceSettings | None = None,
        output_format: AudioFormat = AudioFormat.MP3,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech as chunks.

        For long texts, this allows playback to start before
        the full synthesis is complete.

        Args:
            text: The text to synthesize
            settings: Voice settings
            output_format: The desired audio format

        Yields:
            Audio data chunks
        """
        settings = settings or VoiceSettings()

        tts = self._create_tts_provider(settings.language)

        voice_id = settings.voice_id
        if not voice_id:
            voice_id = await self._get_default_voice(settings.language)

        async for chunk in tts.synthesize_stream(
            text=text,
            voice_id=voice_id,
            output_format=output_format,
            language=settings.language,
        ):
            yield chunk

    async def list_voices(
        self,
        language: SpeechLanguage | None = None,
    ) -> list[VoiceInfo]:
        """List available voices.

        Args:
            language: Filter by language (optional)

        Returns:
            List of available voices
        """
        # Use cached voices if available
        if not self._voice_cache:
            tts = self._create_tts_provider()
            self._voice_cache = await tts.list_voices()

        if language:
            return [v for v in self._voice_cache if v.language == language]

        return self._voice_cache

    async def _get_default_voice(self, language: SpeechLanguage) -> str | None:
        """Get the default voice for a language.

        Args:
            language: The target language

        Returns:
            Voice ID or None
        """
        if language in self._default_voices:
            return self._default_voices[language]

        # Get available voices and pick a default
        voices = await self.list_voices(language)
        if voices:
            # Prefer neural/standard voices
            for voice in voices:
                if "neural" in voice.voice_id.lower():
                    self._default_voices[language] = voice.voice_id
                    return voice.voice_id

            # Fall back to first available
            self._default_voices[language] = voices[0].voice_id
            return voices[0].voice_id

        return None

    def set_default_voice(self, language: SpeechLanguage, voice_id: str) -> None:
        """Set the default voice for a language.

        Args:
            language: The target language
            voice_id: The voice ID to use as default
        """
        self._default_voices[language] = voice_id

    async def get_voice_info(self, voice_id: str) -> VoiceInfo | None:
        """Get information about a specific voice.

        Args:
            voice_id: The voice ID

        Returns:
            VoiceInfo or None if not found
        """
        voices = await self.list_voices()
        for voice in voices:
            if voice.voice_id == voice_id:
                return voice
        return None


# Singleton instance
_synthesis_service: SynthesisService | None = None


def get_synthesis_service() -> SynthesisService:
    """Get or create the synthesis service singleton."""
    global _synthesis_service
    if _synthesis_service is None:
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

        _synthesis_service = SynthesisService(
            provider_type=provider_type,
            **provider_config,
        )

    return _synthesis_service
