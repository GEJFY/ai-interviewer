"""AWS Transcribe and Polly implementation for STT and TTS."""

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


class AWSSpeechConfig:
    """Configuration for AWS Speech Services."""

    def __init__(
        self,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        region: str = "ap-northeast-1",
    ):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region = region


class AWSSpeechToText(BaseSpeechToText):
    """AWS Transcribe implementation for Speech-to-Text."""

    # Language code mapping for AWS Transcribe
    LANGUAGE_MAPPING = {
        "ja-JP": "ja-JP",
        "en-US": "en-US",
        "en-GB": "en-GB",
        "zh-CN": "zh-CN",
        "ko-KR": "ko-KR",
        "de-DE": "de-DE",
        "fr-FR": "fr-FR",
        "es-ES": "es-ES",
    }

    def __init__(self, config: AWSSpeechConfig):
        self.config = config
        self._transcribe_client = None

    def _get_client(self):
        """Lazy initialization of boto3 client."""
        if self._transcribe_client is None:
            try:
                import boto3

                session_kwargs = {}
                if self.config.aws_access_key_id:
                    session_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
                if self.config.aws_secret_access_key:
                    session_kwargs["aws_secret_access_key"] = (
                        self.config.aws_secret_access_key
                    )

                session = boto3.Session(**session_kwargs)
                self._transcribe_client = session.client(
                    "transcribe", region_name=self.config.region
                )
            except ImportError:
                raise ImportError(
                    "boto3 is required for AWS services. Install with: pip install boto3"
                ) from None
        return self._transcribe_client

    async def transcribe(
        self,
        audio_data: bytes,
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """Transcribe audio using AWS Transcribe.

        Note: AWS Transcribe requires audio to be uploaded to S3 for batch processing,
        or use streaming for real-time. For simplicity, this uses streaming.
        """
        # For batch transcription, we'd need S3. Using streaming instead.
        async for result in self.transcribe_stream(
            self._bytes_to_async_iter(audio_data), language, format, sample_rate
        ):
            if result.is_final:
                return result

        return TranscriptionResult(text="", confidence=0.0, language=language)

    async def _bytes_to_async_iter(self, data: bytes) -> AsyncIterator[bytes]:
        """Convert bytes to async iterator."""
        chunk_size = 4096
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: str = "ja-JP",
        format: AudioFormat = AudioFormat.WAV,
        sample_rate: int = 16000,
    ) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription using AWS Transcribe Streaming."""
        try:
            from amazon_transcribe.client import TranscribeStreamingClient
            from amazon_transcribe.handlers import TranscriptResultStreamHandler
            from amazon_transcribe.model import TranscriptEvent
        except ImportError:
            raise ImportError(
                "amazon-transcribe is required for AWS Transcribe streaming. "
                "Install with: pip install amazon-transcribe"
            ) from None

        aws_language = self.LANGUAGE_MAPPING.get(language, "ja-JP")

        # Create client
        client = TranscribeStreamingClient(region=self.config.region)

        result_queue: asyncio.Queue[TranscriptionResult | None] = asyncio.Queue()

        class EventHandler(TranscriptResultStreamHandler):
            async def handle_transcript_event(self, transcript_event: TranscriptEvent):
                results = transcript_event.transcript.results
                for result in results:
                    if result.alternatives:
                        alt = result.alternatives[0]
                        await result_queue.put(
                            TranscriptionResult(
                                text=alt.transcript,
                                confidence=alt.confidence if hasattr(alt, "confidence") else 1.0,
                                language=language,
                                is_final=not result.is_partial,
                            )
                        )

        # Start streaming
        stream = await client.start_stream_transcription(
            language_code=aws_language,
            media_sample_rate_hz=sample_rate,
            media_encoding="pcm",
        )

        handler = EventHandler(stream.output_stream)

        async def feed_audio():
            async for chunk in audio_stream:
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await stream.input_stream.end_stream()
            await result_queue.put(None)

        # Run handler and feeder concurrently
        asyncio.create_task(feed_audio())
        asyncio.create_task(handler.handle_events())

        while True:
            result = await result_queue.get()
            if result is None:
                break
            yield result


class AWSTextToSpeech(BaseTextToSpeech):
    """AWS Polly implementation for Text-to-Speech."""

    # Default voices for each language
    DEFAULT_VOICES = {
        "ja-JP": "Mizuki",
        "en-US": "Joanna",
        "en-GB": "Amy",
        "zh-CN": "Zhiyu",
        "ko-KR": "Seoyeon",
        "de-DE": "Vicki",
        "fr-FR": "Celine",
        "es-ES": "Lucia",
    }

    # Language to engine mapping (neural voices)
    NEURAL_VOICES = {
        "ja-JP": "Kazuha",
        "en-US": "Danielle",
        "en-GB": "Amy",
        "zh-CN": "Zhiyu",
        "ko-KR": "Seoyeon",
        "de-DE": "Vicki",
        "fr-FR": "Lea",
        "es-ES": "Lucia",
    }

    def __init__(self, config: AWSSpeechConfig):
        self.config = config
        self._polly_client = None

    def _get_client(self):
        """Lazy initialization of boto3 Polly client."""
        if self._polly_client is None:
            try:
                import boto3

                session_kwargs = {}
                if self.config.aws_access_key_id:
                    session_kwargs["aws_access_key_id"] = self.config.aws_access_key_id
                if self.config.aws_secret_access_key:
                    session_kwargs["aws_secret_access_key"] = (
                        self.config.aws_secret_access_key
                    )

                session = boto3.Session(**session_kwargs)
                self._polly_client = session.client(
                    "polly", region_name=self.config.region
                )
            except ImportError:
                raise ImportError(
                    "boto3 is required for AWS services. Install with: pip install boto3"
                ) from None
        return self._polly_client

    async def synthesize(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> SynthesisResult:
        """Synthesize text to speech using AWS Polly."""
        client = self._get_client()

        # Set voice
        voice = voice_id or self.NEURAL_VOICES.get(language, self.DEFAULT_VOICES.get(language, "Joanna"))

        # Map format to Polly output format
        format_mapping = {
            AudioFormat.MP3: "mp3",
            AudioFormat.OGG: "ogg_vorbis",
            AudioFormat.PCM: "pcm",
        }
        output_format = format_mapping.get(format, "mp3")

        # Build SSML for speed control
        ssml_text = f"""
        <speak>
            <prosody rate="{int(speed * 100)}%">{text}</prosody>
        </speak>
        """

        # Call Polly
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.synthesize_speech(
                Engine="neural",
                OutputFormat=output_format,
                SampleRate="16000",
                Text=ssml_text,
                TextType="ssml",
                VoiceId=voice,
            ),
        )

        # Read audio data
        audio_data = response["AudioStream"].read()

        return SynthesisResult(
            audio_data=audio_data,
            format=format,
            sample_rate=16000,
            duration_ms=0,  # Polly doesn't return duration
        )

    async def synthesize_stream(
        self,
        text: str,
        language: str = "ja-JP",
        voice_id: str | None = None,
        format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
    ) -> AsyncIterator[bytes]:
        """Stream synthesized speech from AWS Polly."""
        # Polly supports streaming output
        result = await self.synthesize(text, language, voice_id, format, speed)

        # Yield in chunks
        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i : i + chunk_size]

    async def list_voices(self, language: str | None = None) -> list[VoiceInfo]:
        """List available AWS Polly voices."""
        client = self._get_client()

        kwargs = {}
        if language:
            # Map to AWS language code format
            kwargs["LanguageCode"] = language

        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.describe_voices(**kwargs)
        )

        voices = []
        for voice in response["Voices"]:
            voices.append(
                VoiceInfo(
                    id=voice["Id"],
                    name=voice["Name"],
                    language=voice["LanguageCode"],
                    gender=voice["Gender"].lower(),
                    description=", ".join(voice.get("SupportedEngines", [])),
                )
            )

        return voices
