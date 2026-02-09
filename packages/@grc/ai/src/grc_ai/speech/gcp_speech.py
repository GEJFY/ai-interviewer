"""GCP Speech-to-Text and Text-to-Speech implementation."""

import asyncio
from collections.abc import AsyncIterator

from grc_ai.speech.base import (
    AudioFormat,
    BaseSpeechToText,
    BaseTextToSpeech,
    SynthesisResult,
    TranscriptionResult,
    VoiceInfo,
)


class GCPSpeechConfig:
    """Configuration for GCP Speech Services."""

    def __init__(
        self,
        project_id: str,
        credentials_path: str | None = None,
    ):
        self.project_id = project_id
        self.credentials_path = credentials_path


class GCPSpeechToText(BaseSpeechToText):
    """GCP Speech-to-Text implementation."""

    # Language code mapping
    LANGUAGE_MAPPING = {
        "ja-JP": "ja-JP",
        "en-US": "en-US",
        "en-GB": "en-GB",
        "zh-CN": "zh-CN",
        "zh-TW": "zh-TW",
        "ko-KR": "ko-KR",
        "de-DE": "de-DE",
        "fr-FR": "fr-FR",
        "es-ES": "es-ES",
    }

    def __init__(self, config: GCPSpeechConfig):
        self.config = config
        self._client = None

    def _get_client(self):
        """Lazy initialization of GCP Speech client."""
        if self._client is None:
            try:
                from google.cloud import speech_v1 as speech

                if self.config.credentials_path:
                    self._client = speech.SpeechClient.from_service_account_json(
                        self.config.credentials_path
                    )
                else:
                    self._client = speech.SpeechClient()
            except ImportError:
                raise ImportError(
                    "google-cloud-speech is required for GCP Speech. "
                    "Install with: pip install google-cloud-speech"
                ) from None
        return self._client

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """Transcribe audio using GCP Speech-to-Text."""
        from google.cloud import speech_v1 as speech

        client = self._get_client()

        # Map audio format to GCP encoding
        encoding_map = {
            AudioFormat.WAV: speech.RecognitionConfig.AudioEncoding.LINEAR16,
            AudioFormat.MP3: speech.RecognitionConfig.AudioEncoding.MP3,
            AudioFormat.OGG: speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            AudioFormat.WEBM: speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        }

        config = speech.RecognitionConfig(
            encoding=encoding_map.get(format, speech.RecognitionConfig.AudioEncoding.LINEAR16),
            sample_rate_hertz=sample_rate,
            language_code=self.LANGUAGE_MAPPING.get(language, "ja-JP"),
            enable_automatic_punctuation=True,
            enable_word_time_offsets=True,
        )

        audio = speech.RecognitionAudio(content=audio_data)

        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.recognize(config=config, audio=audio)
        )

        if response.results:
            result = response.results[0]
            alternative = result.alternatives[0]

            words = []
            for word_info in alternative.words:
                words.append(
                    {
                        "word": word_info.word,
                        "start_time_ms": int(word_info.start_time.total_seconds() * 1000),
                        "end_time_ms": int(word_info.end_time.total_seconds() * 1000),
                    }
                )

            return TranscriptionResult(
                text=alternative.transcript,
                confidence=alternative.confidence,
                language=language,
                is_final=True,
                words=words,
            )

        return TranscriptionResult(text="", confidence=0.0, language=language)

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription using GCP Speech-to-Text Streaming."""
        from google.cloud import speech_v1 as speech

        client = self._get_client()

        # Map audio format to GCP encoding
        encoding_map = {
            AudioFormat.WAV: speech.RecognitionConfig.AudioEncoding.LINEAR16,
            AudioFormat.PCM: speech.RecognitionConfig.AudioEncoding.LINEAR16,
        }

        config = speech.RecognitionConfig(
            encoding=encoding_map.get(format, speech.RecognitionConfig.AudioEncoding.LINEAR16),
            sample_rate_hertz=sample_rate,
            language_code=self.LANGUAGE_MAPPING.get(language, "ja-JP"),
            enable_automatic_punctuation=True,
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
        )

        # Generator for streaming requests
        async def request_generator():
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
            async for chunk in audio_stream:
                yield speech.StreamingRecognizeRequest(audio_content=chunk)

        # Convert async generator to sync for GCP client
        requests = []
        async for req in request_generator():
            requests.append(req)

        responses = client.streaming_recognize(iter(requests))

        for response in responses:
            for result in response.results:
                if result.alternatives:
                    alternative = result.alternatives[0]
                    yield TranscriptionResult(
                        text=alternative.transcript,
                        confidence=alternative.confidence if result.is_final else 0.8,
                        language=language,
                        is_final=result.is_final,
                    )


class GCPTextToSpeech(BaseTextToSpeech):
    """GCP Text-to-Speech implementation."""

    # Default voices for each language (WaveNet voices for high quality)
    DEFAULT_VOICES = {
        "ja-JP": "ja-JP-Neural2-B",
        "en-US": "en-US-Neural2-F",
        "en-GB": "en-GB-Neural2-A",
        "zh-CN": "cmn-CN-Wavenet-A",
        "ko-KR": "ko-KR-Neural2-A",
        "de-DE": "de-DE-Neural2-A",
        "fr-FR": "fr-FR-Neural2-A",
        "es-ES": "es-ES-Neural2-A",
    }

    def __init__(self, config: GCPSpeechConfig):
        self.config = config
        self._client = None

    def _get_client(self):
        """Lazy initialization of GCP TTS client."""
        if self._client is None:
            try:
                from google.cloud import texttospeech

                if self.config.credentials_path:
                    self._client = texttospeech.TextToSpeechClient.from_service_account_json(
                        self.config.credentials_path
                    )
                else:
                    self._client = texttospeech.TextToSpeechClient()
            except ImportError:
                raise ImportError(
                    "google-cloud-texttospeech is required for GCP TTS. "
                    "Install with: pip install google-cloud-texttospeech"
                ) from None
        return self._client

    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to speech using GCP Text-to-Speech."""
        from google.cloud import texttospeech

        client = self._get_client()

        # Set up synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Set up voice
        voice_name = voice_id or self.DEFAULT_VOICES.get(language, "ja-JP-Neural2-B")
        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            name=voice_name,
        )

        # Set up audio config
        encoding_map = {
            AudioFormat.MP3: texttospeech.AudioEncoding.MP3,
            AudioFormat.WAV: texttospeech.AudioEncoding.LINEAR16,
            AudioFormat.OGG: texttospeech.AudioEncoding.OGG_OPUS,
        }

        audio_config = texttospeech.AudioConfig(
            audio_encoding=encoding_map.get(format, texttospeech.AudioEncoding.MP3),
            speaking_rate=speed,
            sample_rate_hertz=16000,
        )

        # Perform synthesis
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            ),
        )

        return SynthesisResult(
            audio_data=response.audio_content,
            format=format,
            sample_rate=16000,
            duration_ms=0,  # Calculate from audio if needed
        )

    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech from GCP TTS."""
        # GCP TTS doesn't have true streaming, so we chunk the result
        result = await self.synthesize(text, language, voice_id, format, speed)

        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i : i + chunk_size]

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """List available GCP TTS voices."""
        from google.cloud import texttospeech

        client = self._get_client()

        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.list_voices(language_code=language)
        )

        voices = []
        for voice in response.voices:
            for lang_code in voice.language_codes:
                if language is None or lang_code.startswith(language.split("-")[0]):
                    gender_map = {
                        texttospeech.SsmlVoiceGender.MALE: "male",
                        texttospeech.SsmlVoiceGender.FEMALE: "female",
                        texttospeech.SsmlVoiceGender.NEUTRAL: "neutral",
                    }
                    voices.append(
                        VoiceInfo(
                            id=voice.name,
                            name=voice.name,
                            language=lang_code,
                            gender=gender_map.get(voice.ssml_gender, "neutral"),
                            description=f"Sample rate: {voice.natural_sample_rate_hertz}Hz",
                        )
                    )

        return voices
