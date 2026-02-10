"""AWS Translate implementation.

Uses Amazon Translate service for text translation
and Amazon Comprehend for language detection.
"""

import asyncio
from dataclasses import dataclass
from functools import partial

import boto3

from grc_ai.translation.base import (
    BaseTranslation,
    DetectionResult,
    TranslationLanguage,
    TranslationResult,
)


@dataclass
class AWSTranslateConfig:
    """Configuration for AWS Translate."""

    region_name: str = "ap-northeast-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None


class AWSTranslate(BaseTranslation):
    """AWS Translate implementation.

    Uses Amazon Translate for translation and Amazon Comprehend
    for language detection.

    Example:
        >>> config = AWSTranslateConfig(region_name="ap-northeast-1")
        >>> translator = AWSTranslate(config)
        >>> result = await translator.translate(
        ...     "Hello, world!",
        ...     TranslationLanguage.JA
        ... )
        >>> print(result.translated_text)
        'こんにちは、世界！'
    """

    # Language code mapping for AWS Translate
    LANGUAGE_MAP = {
        TranslationLanguage.JA: "ja",
        TranslationLanguage.EN: "en",
        TranslationLanguage.ZH: "zh",
        TranslationLanguage.ZH_TW: "zh-TW",
        TranslationLanguage.KO: "ko",
        TranslationLanguage.ES: "es",
        TranslationLanguage.FR: "fr",
        TranslationLanguage.DE: "de",
        TranslationLanguage.PT: "pt",
        TranslationLanguage.IT: "it",
        TranslationLanguage.RU: "ru",
        TranslationLanguage.AR: "ar",
        TranslationLanguage.HI: "hi",
        TranslationLanguage.TH: "th",
        TranslationLanguage.VI: "vi",
        TranslationLanguage.ID: "id",
        TranslationLanguage.MS: "ms",
    }

    def __init__(
        self,
        config: AWSTranslateConfig,
        default_source: TranslationLanguage | None = None,
    ):
        """Initialize AWS Translate.

        Args:
            config: AWS configuration
            default_source: Default source language
        """
        super().__init__(default_source)
        self.config = config

        session_kwargs = {"region_name": config.region_name}
        if config.aws_access_key_id and config.aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = config.aws_access_key_id
            session_kwargs["aws_secret_access_key"] = config.aws_secret_access_key

        session = boto3.Session(**session_kwargs)
        self._translate_client = session.client("translate")
        self._comprehend_client = session.client("comprehend")

    async def translate(
        self,
        text: str,
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> TranslationResult:
        """Translate text using AWS Translate.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)

        Returns:
            TranslationResult with translated text
        """
        source = source_language or self.default_source
        source_code = "auto" if not source else self.LANGUAGE_MAP.get(source, source.value)
        target_code = self.LANGUAGE_MAP.get(target_language, target_language.value)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(
                self._translate_client.translate_text,
                Text=text,
                SourceLanguageCode=source_code,
                TargetLanguageCode=target_code,
            ),
        )

        detected_lang = None
        if source_code == "auto":
            detected_lang = self._normalize_language_code(response.get("SourceLanguageCode", ""))

        return TranslationResult(
            source_text=text,
            translated_text=response["TranslatedText"],
            source_language=source or detected_lang or TranslationLanguage.EN,
            target_language=target_language,
            detected_language=detected_lang,
        )

    async def translate_batch(
        self,
        texts: list[str],
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> list[TranslationResult]:
        """Translate multiple texts using AWS Translate.

        AWS Translate doesn't support native batch translation for real-time,
        so we use parallel execution.

        Args:
            texts: List of texts to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)

        Returns:
            List of TranslationResults
        """
        if not texts:
            return []

        # Execute translations in parallel
        tasks = [self.translate(text, target_language, source_language) for text in texts]
        return await asyncio.gather(*tasks)

    async def detect_language(self, text: str) -> DetectionResult:
        """Detect language using Amazon Comprehend.

        Args:
            text: Text to analyze

        Returns:
            DetectionResult with detected language
        """
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(self._comprehend_client.detect_dominant_language, Text=text),
        )

        languages = response.get("Languages", [])
        if not languages:
            return DetectionResult(
                detected_language=TranslationLanguage.EN,
                confidence=0.0,
            )

        # Sort by confidence
        languages.sort(key=lambda x: x["Score"], reverse=True)
        primary = languages[0]
        detected_lang = self._normalize_language_code(primary["LanguageCode"])

        alternatives = []
        for lang in languages[1:]:
            alt_lang = self._normalize_language_code(lang["LanguageCode"])
            if alt_lang:
                alternatives.append((alt_lang, lang["Score"]))

        return DetectionResult(
            detected_language=detected_lang or TranslationLanguage.EN,
            confidence=primary["Score"],
            alternatives=alternatives,
        )

    async def get_supported_languages(self) -> list[TranslationLanguage]:
        """Get list of supported languages.

        Returns:
            List of supported TranslationLanguage values
        """
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, self._translate_client.list_languages)

        supported = []
        for lang in response.get("Languages", []):
            lang_enum = self._normalize_language_code(lang["LanguageCode"])
            if lang_enum:
                supported.append(lang_enum)

        return supported
