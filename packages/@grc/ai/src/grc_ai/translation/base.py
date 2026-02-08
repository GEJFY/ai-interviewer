"""Base classes and protocols for translation services.

Provides abstraction layer for multi-cloud translation services
supporting Azure Translator, AWS Translate, and GCP Cloud Translation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class TranslationLanguage(str, Enum):
    """Supported languages for translation."""

    JA = "ja"  # Japanese
    EN = "en"  # English
    ZH = "zh"  # Chinese (Simplified)
    ZH_TW = "zh-TW"  # Chinese (Traditional)
    KO = "ko"  # Korean
    ES = "es"  # Spanish
    FR = "fr"  # French
    DE = "de"  # German
    PT = "pt"  # Portuguese
    IT = "it"  # Italian
    RU = "ru"  # Russian
    AR = "ar"  # Arabic
    HI = "hi"  # Hindi
    TH = "th"  # Thai
    VI = "vi"  # Vietnamese
    ID = "id"  # Indonesian
    MS = "ms"  # Malay


@dataclass
class TranslationResult:
    """Result from translation operation."""

    source_text: str
    translated_text: str
    source_language: TranslationLanguage
    target_language: TranslationLanguage
    confidence: float | None = None
    detected_language: TranslationLanguage | None = None
    alternatives: list[str] = field(default_factory=list)


@dataclass
class DetectionResult:
    """Result from language detection."""

    detected_language: TranslationLanguage
    confidence: float
    alternatives: list[tuple[TranslationLanguage, float]] = field(default_factory=list)


@runtime_checkable
class TranslationProvider(Protocol):
    """Protocol for translation service providers."""

    async def translate(
        self,
        text: str,
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> TranslationResult:
        """Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (auto-detect if not specified)

        Returns:
            TranslationResult with translated text
        """
        ...

    async def translate_batch(
        self,
        texts: list[str],
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> list[TranslationResult]:
        """Translate multiple texts.

        Args:
            texts: List of texts to translate
            target_language: Target language
            source_language: Source language (auto-detect if not specified)

        Returns:
            List of TranslationResults
        """
        ...

    async def detect_language(self, text: str) -> DetectionResult:
        """Detect the language of text.

        Args:
            text: Text to analyze

        Returns:
            DetectionResult with detected language
        """
        ...

    async def get_supported_languages(self) -> list[TranslationLanguage]:
        """Get list of supported languages.

        Returns:
            List of supported TranslationLanguage values
        """
        ...


class BaseTranslation(ABC):
    """Abstract base class for translation providers.

    Provides common functionality and interface for translation services.
    """

    def __init__(self, default_source: TranslationLanguage | None = None):
        """Initialize translation provider.

        Args:
            default_source: Default source language (None for auto-detect)
        """
        self.default_source = default_source

    @abstractmethod
    async def translate(
        self,
        text: str,
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> TranslationResult:
        """Translate text to target language."""
        pass

    async def translate_batch(
        self,
        texts: list[str],
        target_language: TranslationLanguage,
        source_language: TranslationLanguage | None = None,
    ) -> list[TranslationResult]:
        """Translate multiple texts. Default implementation calls translate() in sequence."""
        results = []
        for text in texts:
            result = await self.translate(text, target_language, source_language)
            results.append(result)
        return results

    @abstractmethod
    async def detect_language(self, text: str) -> DetectionResult:
        """Detect the language of text."""
        pass

    @abstractmethod
    async def get_supported_languages(self) -> list[TranslationLanguage]:
        """Get list of supported languages."""
        pass

    def _normalize_language_code(self, code: str) -> TranslationLanguage | None:
        """Convert language code string to TranslationLanguage enum.

        Args:
            code: Language code (e.g., 'en', 'ja', 'zh-Hans')

        Returns:
            TranslationLanguage or None if not recognized
        """
        # Normalize common variants
        code_map = {
            "zh-hans": TranslationLanguage.ZH,
            "zh-hant": TranslationLanguage.ZH_TW,
            "zh-cn": TranslationLanguage.ZH,
            "zh-tw": TranslationLanguage.ZH_TW,
            "pt-br": TranslationLanguage.PT,
            "pt-pt": TranslationLanguage.PT,
        }

        normalized = code.lower()
        if normalized in code_map:
            return code_map[normalized]

        # Try direct match
        try:
            return TranslationLanguage(normalized.split("-")[0])
        except ValueError:
            return None


__all__ = [
    "TranslationLanguage",
    "TranslationResult",
    "DetectionResult",
    "TranslationProvider",
    "BaseTranslation",
]
