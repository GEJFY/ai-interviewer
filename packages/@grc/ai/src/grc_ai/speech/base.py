"""Speech service abstraction layer for STT and TTS."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncIterator, Protocol, runtime_checkable


class AudioFormat(str, Enum):
    """Supported audio formats."""

    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    PCM = "pcm"


class SpeechLanguage(str, Enum):
    """Supported languages for speech recognition/synthesis."""

    JA = "ja-JP"  # Japanese
    EN = "en-US"  # English (US)
    EN_GB = "en-GB"  # English (UK)
    ZH = "zh-CN"  # Chinese (Simplified)
    ZH_TW = "zh-TW"  # Chinese (Traditional)
    KO = "ko-KR"  # Korean
    DE = "de-DE"  # German
    FR = "fr-FR"  # French
    ES = "es-ES"  # Spanish


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""

    text: str
    confidence: float = 1.0
    language: str | None = None
    is_final: bool = True
    start_time_ms: int = 0
    end_time_ms: int = 0
    words: list[dict] = field(default_factory=list)  # Individual word timestamps


@dataclass
class SynthesisResult:
    """Result from text-to-speech synthesis."""

    audio_data: bytes
    format: AudioFormat
    sample_rate: int = 16000
    duration_ms: int = 0


@dataclass
class VoiceInfo:
    """Information about an available voice."""

    id: str
    name: str
    language: str
    gender: str  # "male", "female", "neutral"
    description: str = ""


@runtime_checkable
class SpeechToTextProvider(Protocol):
    """Protocol for Speech-to-Text (STT) providers."""

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes
            language: Language code for transcription
            format: Audio format
            sample_rate: Sample rate in Hz

        Returns:
            TranscriptionResult with transcribed text
        """
        ...

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionResult]:
        """Stream audio for real-time transcription.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code for transcription
            format: Audio format
            sample_rate: Sample rate in Hz

        Yields:
            TranscriptionResult with partial/final results
        """
        ...


@runtime_checkable
class TextToSpeechProvider(Protocol):
    """Protocol for Text-to-Speech (TTS) providers."""

    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            language: Language code
            voice_id: Specific voice to use (provider-specific)
            format: Output audio format
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            SynthesisResult with audio data
        """
        ...

    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech.

        Args:
            text: Text to synthesize
            language: Language code
            voice_id: Specific voice to use
            format: Output audio format
            speed: Speech speed multiplier

        Yields:
            Audio data chunks
        """
        ...

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """List available voices.

        Args:
            language: Filter by language (optional)

        Returns:
            List of available voices
        """
        ...


class BaseSpeechToText(ABC):
    """Base class for STT implementations."""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """Transcribe audio to text."""
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription."""
        pass


class BaseTextToSpeech(ABC):
    """Base class for TTS implementations."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to speech."""
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech."""
        pass

    @abstractmethod
    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """List available voices."""
        pass
