"""Azure Speech Services implementation for STT and TTS."""

import asyncio
import io
from typing import AsyncIterator

from grc_ai.speech.base import (
    AudioFormat,
    BaseSpeechToText,
    BaseTextToSpeech,
    SynthesisResult,
    TranscriptionResult,
    VoiceInfo,
)


class AzureSpeechConfig:
    """Configuration for Azure Speech Services."""

    def __init__(
        self,
        subscription_key: str,
        region: str = "japaneast",
    ):
        self.subscription_key = subscription_key
        self.region = region


class AzureSpeechToText(BaseSpeechToText):
    """Azure Speech-to-Text implementation."""

    def __init__(self, config: AzureSpeechConfig):
        self.config = config
        self._speech_config = None

    def _get_speech_config(self):
        """Lazy initialization of Azure Speech SDK config."""
        if self._speech_config is None:
            try:
                import azure.cognitiveservices.speech as speechsdk

                self._speech_config = speechsdk.SpeechConfig(
                    subscription=self.config.subscription_key,
                    region=self.config.region,
                )
            except ImportError:
                raise ImportError(
                    "azure-cognitiveservices-speech is required for Azure Speech. "
                    "Install with: pip install azure-cognitiveservices-speech"
                )
        return self._speech_config

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """Transcribe audio using Azure Speech Services."""
        import azure.cognitiveservices.speech as speechsdk

        speech_config = self._get_speech_config()
        speech_config.speech_recognition_language = language

        # Create audio config from bytes
        audio_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

        # Create recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        # Push audio data
        audio_stream.write(audio_data)
        audio_stream.close()

        # Perform recognition
        result = await asyncio.get_event_loop().run_in_executor(
            None, recognizer.recognize_once
        )

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return TranscriptionResult(
                text=result.text,
                confidence=1.0,  # Azure doesn't provide confidence in basic mode
                language=language,
                is_final=True,
            )
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return TranscriptionResult(
                text="",
                confidence=0.0,
                language=language,
                is_final=True,
            )
        else:
            raise RuntimeError(f"Speech recognition failed: {result.reason}")

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription using Azure Speech Services."""
        import azure.cognitiveservices.speech as speechsdk

        speech_config = self._get_speech_config()
        speech_config.speech_recognition_language = language

        # Create push stream for audio input
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        # Queue for results
        result_queue: asyncio.Queue[TranscriptionResult | None] = asyncio.Queue()

        def on_recognizing(evt):
            """Handle partial recognition results."""
            asyncio.get_event_loop().call_soon_threadsafe(
                result_queue.put_nowait,
                TranscriptionResult(
                    text=evt.result.text,
                    confidence=0.8,
                    language=language,
                    is_final=False,
                ),
            )

        def on_recognized(evt):
            """Handle final recognition results."""
            asyncio.get_event_loop().call_soon_threadsafe(
                result_queue.put_nowait,
                TranscriptionResult(
                    text=evt.result.text,
                    confidence=1.0,
                    language=language,
                    is_final=True,
                ),
            )

        def on_session_stopped(evt):
            """Handle session end."""
            asyncio.get_event_loop().call_soon_threadsafe(
                result_queue.put_nowait, None
            )

        # Connect event handlers
        recognizer.recognizing.connect(on_recognizing)
        recognizer.recognized.connect(on_recognized)
        recognizer.session_stopped.connect(on_session_stopped)

        # Start continuous recognition
        recognizer.start_continuous_recognition()

        # Feed audio chunks
        async def feed_audio():
            async for chunk in audio_stream:
                push_stream.write(chunk)
            push_stream.close()

        asyncio.create_task(feed_audio())

        # Yield results
        while True:
            result = await result_queue.get()
            if result is None:
                break
            yield result

        recognizer.stop_continuous_recognition()


class AzureTextToSpeech(BaseTextToSpeech):
    """Azure Text-to-Speech implementation."""

    # Default voices for each language
    DEFAULT_VOICES = {
        "ja-JP": "ja-JP-NanamiNeural",
        "en-US": "en-US-JennyNeural",
        "en-GB": "en-GB-SoniaNeural",
        "zh-CN": "zh-CN-XiaoxiaoNeural",
        "ko-KR": "ko-KR-SunHiNeural",
        "de-DE": "de-DE-KatjaNeural",
        "fr-FR": "fr-FR-DeniseNeural",
        "es-ES": "es-ES-ElviraNeural",
    }

    def __init__(self, config: AzureSpeechConfig):
        self.config = config
        self._speech_config = None

    def _get_speech_config(self):
        """Lazy initialization of Azure Speech SDK config."""
        if self._speech_config is None:
            try:
                import azure.cognitiveservices.speech as speechsdk

                self._speech_config = speechsdk.SpeechConfig(
                    subscription=self.config.subscription_key,
                    region=self.config.region,
                )
            except ImportError:
                raise ImportError(
                    "azure-cognitiveservices-speech is required for Azure Speech. "
                    "Install with: pip install azure-cognitiveservices-speech"
                )
        return self._speech_config

    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to speech using Azure Speech Services."""
        import azure.cognitiveservices.speech as speechsdk

        speech_config = self._get_speech_config()

        # Set output format
        format_mapping = {
            AudioFormat.MP3: speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
            AudioFormat.WAV: speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
            AudioFormat.OGG: speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
        }
        speech_config.set_speech_synthesis_output_format(
            format_mapping.get(
                format, speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
            )
        )

        # Set voice
        voice = voice_id or self.DEFAULT_VOICES.get(language, self.DEFAULT_VOICES["ja-JP"])
        speech_config.speech_synthesis_voice_name = voice

        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None,  # No audio output, we want bytes
        )

        # Build SSML for speed control
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
            <voice name="{voice}">
                <prosody rate="{speed}">{text}</prosody>
            </voice>
        </speak>
        """

        # Perform synthesis
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: synthesizer.speak_ssml(ssml)
        )

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_data = result.audio_data
            duration_ms = int(result.audio_duration.total_seconds() * 1000)

            return SynthesisResult(
                audio_data=audio_data,
                format=format,
                sample_rate=16000,
                duration_ms=duration_ms,
            )
        else:
            raise RuntimeError(f"Speech synthesis failed: {result.reason}")

    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech."""
        # For simplicity, synthesize full audio and chunk it
        result = await self.synthesize(text, language, voice_id, format, speed)

        # Yield in chunks of 4KB
        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i : i + chunk_size]

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """List available Azure voices."""
        import azure.cognitiveservices.speech as speechsdk

        speech_config = self._get_speech_config()
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None,
        )

        result = await asyncio.get_event_loop().run_in_executor(
            None, synthesizer.get_voices_async().get
        )

        voices = []
        for voice in result.voices:
            if language is None or voice.locale.startswith(language.split("-")[0]):
                voices.append(
                    VoiceInfo(
                        id=voice.short_name,
                        name=voice.local_name,
                        language=voice.locale,
                        gender=voice.gender.name.lower(),
                        description=voice.voice_type.name,
                    )
                )

        return voices
