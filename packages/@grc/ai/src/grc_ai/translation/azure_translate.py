"""Azure Translator implementation.

Uses Azure Cognitive Services Translator API for text translation
and language detection.
"""

from dataclasses import dataclass
import httpx

from grc_ai.translation.base import (
    BaseTranslation,
    TranslationLanguage,
    TranslationResult,
    DetectionResult,
)


@dataclass
class AzureTranslatorConfig:
    """Configuration for Azure Translator."""

    subscription_key: str
    region: str = "japaneast"
    endpoint: str = "https://api.cognitive.microsofttranslator.com"
    api_version: str = "3.0"


class AzureTranslator(BaseTranslation):
    """Azure Translator implementation.

    Uses Azure Cognitive Services Translator API.

    Example:
        >>> config = AzureTranslatorConfig(
        ...     subscription_key="your-key",
        ...     region="japaneast"
        ... )
        >>> translator = AzureTranslator(config)
        >>> result = await translator.translate(
        ...     "Hello, world!",
        ...     TranslationLanguage.JA
        ... )
        >>> print(result.translated_text)
        'こんにちは、世界！'
    """

    # Language code mapping for Azure Translator
    LANGUAGE_MAP = {
        TranslationLanguage.JA: "ja",
        TranslationLanguage.EN: "en",
        TranslationLanguage.ZH: "zh-Hans",
        TranslationLanguage.ZH_TW: "zh-Hant",
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
        config: AzureTranslatorConfig,
        default_source: TranslationLanguage | None = None,
    ):
        """Initialize Azure Translator.

        Args:
            config: Azure Translator configuration
            default_source: Default source language
        """
        super().__init__(default_source)
        self.config = config
        self._client = httpx.AsyncClient(
            base_url=config.endpoint,
            headers={
                "Ocp-Apim-Subscription-Key": config.subscription_key,
                "Ocp-Apim-Subscription-Region": config.region,
                "Content-Type": "application/json",
            },
        )

    async def translate(
        self,
        text: str,
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> TranslationResult:
        """Translate text using Azure Translator.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if None)

        Returns:
            TranslationResult with translated text
        """
        source = source_language or self.default_source
        target_code = self.LANGUAGE_MAP.get(target_language, target_language.value)

        params = {
            "api-version": self.config.api_version,
            "to": target_code,
        }
        if source:
            params["from"] = self.LANGUAGE_MAP.get(source, source.value)

        response = await self._client.post(
            "/translate",
            params=params,
            json=[{"text": text}],
        )
        response.raise_for_status()
        data = response.json()

        result = data[0]
        translation = result["translations"][0]
        detected = result.get("detectedLanguage", {})

        detected_lang = None
        if detected:
            detected_lang = self._normalize_language_code(detected.get("language", ""))

        return TranslationResult(
            source_text=text,
            translated_text=translation["text"],
            source_language=source or detected_lang or TranslationLanguage.EN,
            target_language=target_language,
            confidence=detected.get("score"),
            detected_language=detected_lang,
        )

    async def translate_batch(
        self,
        texts: list[str],
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> list[TranslationResult]:
        """Translate multiple texts using Azure Translator.

        Azure Translator supports batch translation natively,
        so this is more efficient than the base implementation.

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

        params = {
            "api-version": self.config.api_version,
            "to": target_code,
        }
        if source:
            params["from"] = self.LANGUAGE_MAP.get(source, source.value)

        # Azure supports up to 100 texts per request
        results = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self._client.post(
                "/translate",
                params=params,
                json=[{"text": t} for t in batch],
            )
            response.raise_for_status()
            data = response.json()

            for j, item in enumerate(data):
                translation = item["translations"][0]
                detected = item.get("detectedLanguage", {})
                detected_lang = None
                if detected:
                    detected_lang = self._normalize_language_code(
                        detected.get("language", "")
                    )

                results.append(
                    TranslationResult(
                        source_text=batch[j],
                        translated_text=translation["text"],
                        source_language=source or detected_lang or TranslationLanguage.EN,
                        target_language=target_language,
                        confidence=detected.get("score"),
                        detected_language=detected_lang,
                    )
                )

        return results

    async def detect_language(self, text: str) -> DetectionResult:
        """Detect language using Azure Translator.

        Args:
            text: Text to analyze

        Returns:
            DetectionResult with detected language
        """
        response = await self._client.post(
            "/detect",
            params={"api-version": self.config.api_version},
            json=[{"text": text}],
        )
        response.raise_for_status()
        data = response.json()

        result = data[0]
        detected_lang = self._normalize_language_code(result["language"])

        alternatives = []
        for alt in result.get("alternatives", []):
            alt_lang = self._normalize_language_code(alt["language"])
            if alt_lang:
                alternatives.append((alt_lang, alt["score"]))

        return DetectionResult(
            detected_language=detected_lang or TranslationLanguage.EN,
            confidence=result["score"],
            alternatives=alternatives,
        )

    async def get_supported_languages(self) -> list[TranslationLanguage]:
        """Get list of supported languages.

        Returns:
            List of supported TranslationLanguage values
        """
        response = await self._client.get(
            "/languages",
            params={"api-version": self.config.api_version, "scope": "translation"},
        )
        response.raise_for_status()
        data = response.json()

        supported = []
        for code in data.get("translation", {}).keys():
            lang = self._normalize_language_code(code)
            if lang:
                supported.append(lang)

        return supported

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
