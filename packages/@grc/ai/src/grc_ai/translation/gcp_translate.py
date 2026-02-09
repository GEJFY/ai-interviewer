"""GCP Cloud Translation implementation.

Uses Google Cloud Translation API (v3) for text translation
and language detection.
"""

import asyncio
from dataclasses import dataclass
from functools import partial

from google.cloud import translate_v3 as translate
from google.oauth2 import service_account

from grc_ai.translation.base import (
    BaseTranslation,
    DetectionResult,
    TranslationLanguage,
    TranslationResult,
)


@dataclass
class GCPTranslateConfig:
    """Configuration for GCP Cloud Translation."""

    project_id: str
    location: str = "global"
    credentials_path: str | None = None


class GCPTranslate(BaseTranslation):
    """GCP Cloud Translation implementation.

    Uses Google Cloud Translation API v3.

    Example:
        >>> config = GCPTranslateConfig(
        ...     project_id="your-project-id"
        ... )
        >>> translator = GCPTranslate(config)
        >>> result = await translator.translate(
        ...     "Hello, world!",
        ...     TranslationLanguage.JA
        ... )
        >>> print(result.translated_text)
        'こんにちは、世界！'
    """

    # Language code mapping for GCP Translate
    LANGUAGE_MAP = {
        TranslationLanguage.JA: "ja",
        TranslationLanguage.EN: "en",
        TranslationLanguage.ZH: "zh-CN",
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
        config: GCPTranslateConfig,
        default_source: TranslationLanguage | None = None,
    ):
        """Initialize GCP Cloud Translation.

        Args:
            config: GCP configuration
            default_source: Default source language
        """
        super().__init__(default_source)
        self.config = config
        self._parent = f"projects/{config.project_id}/locations/{config.location}"

        if config.credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                config.credentials_path
            )
            self._client = translate.TranslationServiceClient(credentials=credentials)
        else:
            self._client = translate.TranslationServiceClient()

    async def translate(
        self,
        text: str,
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> TranslationResult:
        """Translate text using GCP Cloud Translation.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)

        Returns:
            TranslationResult with translated text
        """
        source = source_language or self.default_source
        target_code = self.LANGUAGE_MAP.get(target_language, target_language.value)

        request = translate.TranslateTextRequest(
            parent=self._parent,
            contents=[text],
            target_language_code=target_code,
            mime_type="text/plain",
        )

        if source:
            request.source_language_code = self.LANGUAGE_MAP.get(source, source.value)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(self._client.translate_text, request=request),
        )

        translation = response.translations[0]
        detected_lang = None
        if translation.detected_language_code:
            detected_lang = self._normalize_language_code(translation.detected_language_code)

        return TranslationResult(
            source_text=text,
            translated_text=translation.translated_text,
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
        """Translate multiple texts using GCP Cloud Translation.

        GCP Cloud Translation supports batch translation natively.

        Args:
            texts: List of texts to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)

        Returns:
            List of TranslationResults
        """
        if not texts:
            return []

        source = source_language or self.default_source
        target_code = self.LANGUAGE_MAP.get(target_language, target_language.value)

        # GCP supports up to 1024 texts per request
        results = []
        batch_size = 1024

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            request = translate.TranslateTextRequest(
                parent=self._parent,
                contents=batch,
                target_language_code=target_code,
                mime_type="text/plain",
            )

            if source:
                request.source_language_code = self.LANGUAGE_MAP.get(source, source.value)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                partial(self._client.translate_text, request=request),
            )

            for j, translation in enumerate(response.translations):
                detected_lang = None
                if translation.detected_language_code:
                    detected_lang = self._normalize_language_code(
                        translation.detected_language_code
                    )

                results.append(
                    TranslationResult(
                        source_text=batch[j],
                        translated_text=translation.translated_text,
                        source_language=source or detected_lang or TranslationLanguage.EN,
                        target_language=target_language,
                        detected_language=detected_lang,
                    )
                )

        return results

    async def detect_language(self, text: str) -> DetectionResult:
        """Detect language using GCP Cloud Translation.

        Args:
            text: Text to analyze

        Returns:
            DetectionResult with detected language
        """
        request = translate.DetectLanguageRequest(
            parent=self._parent,
            content=text,
            mime_type="text/plain",
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(self._client.detect_language, request=request),
        )

        languages = response.languages
        if not languages:
            return DetectionResult(
                detected_language=TranslationLanguage.EN,
                confidence=0.0,
            )

        # Sort by confidence
        languages = sorted(languages, key=lambda x: x.confidence, reverse=True)
        primary = languages[0]
        detected_lang = self._normalize_language_code(primary.language_code)

        alternatives = []
        for lang in languages[1:]:
            alt_lang = self._normalize_language_code(lang.language_code)
            if alt_lang:
                alternatives.append((alt_lang, lang.confidence))

        return DetectionResult(
            detected_language=detected_lang or TranslationLanguage.EN,
            confidence=primary.confidence,
            alternatives=alternatives,
        )

    async def get_supported_languages(self) -> list[TranslationLanguage]:
        """Get list of supported languages.

        Returns:
            List of supported TranslationLanguage values
        """
        request = translate.GetSupportedLanguagesRequest(
            parent=self._parent,
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            partial(self._client.get_supported_languages, request=request),
        )

        supported = []
        for lang in response.languages:
            lang_enum = self._normalize_language_code(lang.language_code)
            if lang_enum:
                supported.append(lang_enum)

        return supported
