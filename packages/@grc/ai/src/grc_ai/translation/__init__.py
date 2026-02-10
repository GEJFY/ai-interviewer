"""Translation services abstraction layer.

Provides multi-cloud translation support for Azure Translator,
AWS Translate, and GCP Cloud Translation.
"""

from grc_ai.translation.base import (
    BaseTranslation,
    DetectionResult,
    TranslationLanguage,
    TranslationProvider,
    TranslationResult,
)
from grc_ai.translation.factory import (
    TranslationProviderType,
    create_translator,
)

__all__ = [
    # Base types
    "TranslationLanguage",
    "TranslationResult",
    "DetectionResult",
    # Protocols
    "TranslationProvider",
    # Base classes
    "BaseTranslation",
    # Factory
    "TranslationProviderType",
    "create_translator",
]
