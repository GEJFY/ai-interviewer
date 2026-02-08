"""Speech services abstraction layer for STT and TTS."""

from grc_ai.speech.base import (
    AudioFormat,
    BaseSpeechToText,
    BaseTextToSpeech,
    SpeechLanguage,
    SpeechToTextProvider,
    SynthesisResult,
    TextToSpeechProvider,
    TranscriptionResult,
    VoiceInfo,
)
from grc_ai.speech.factory import (
    create_speech_to_text,
    create_text_to_speech,
    SpeechProviderType,
)

__all__ = [
    # Base types
    "AudioFormat",
    "SpeechLanguage",
    "TranscriptionResult",
    "SynthesisResult",
    "VoiceInfo",
    # Protocols
    "SpeechToTextProvider",
    "TextToSpeechProvider",
    # Base classes
    "BaseSpeechToText",
    "BaseTextToSpeech",
    # Factory
    "create_speech_to_text",
    "create_text_to_speech",
    "SpeechProviderType",
]
