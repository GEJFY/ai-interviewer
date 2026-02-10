"""Factory functions for creating translation providers."""

from enum import StrEnum
from typing import Any

from grc_ai.translation.base import (
    TranslationLanguage,
    TranslationProvider,
)


class TranslationProviderType(StrEnum):
    """Supported translation provider types."""

    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"


def create_translator(
    provider: TranslationProviderType | str,
    **config: Any,
) -> TranslationProvider:
    """Create a translation provider instance.

    Args:
        provider: The provider type (azure, aws, gcp)
        **config: Provider-specific configuration

    Returns:
        A configured TranslationProvider instance

    Raises:
        ValueError: If the provider type is not supported

    Examples:
        >>> # Azure Translator
        >>> translator = create_translator(
        ...     "azure",
        ...     subscription_key="your-key",
        ...     region="japaneast",
        ... )

        >>> # AWS Translate
        >>> translator = create_translator(
        ...     "aws",
        ...     region_name="ap-northeast-1",
        ... )

        >>> # GCP Cloud Translation
        >>> translator = create_translator(
        ...     "gcp",
        ...     project_id="your-project",
        ... )
    """
    provider_type = TranslationProviderType(provider) if isinstance(provider, str) else provider

    match provider_type:
        case TranslationProviderType.AZURE:
            from grc_ai.translation.azure_translate import (
                AzureTranslator,
                AzureTranslatorConfig,
            )

            config_obj = AzureTranslatorConfig(
                subscription_key=config.get("subscription_key", ""),
                region=config.get("region", "japaneast"),
                endpoint=config.get("endpoint", "https://api.cognitive.microsofttranslator.com"),
            )
            default_source = config.get("default_source")
            if default_source and isinstance(default_source, str):
                default_source = TranslationLanguage(default_source)
            return AzureTranslator(config_obj, default_source)

        case TranslationProviderType.AWS:
            from grc_ai.translation.aws_translate import (
                AWSTranslate,
                AWSTranslateConfig,
            )

            config_obj = AWSTranslateConfig(
                region_name=config.get("region_name", "ap-northeast-1"),
                aws_access_key_id=config.get("aws_access_key_id"),
                aws_secret_access_key=config.get("aws_secret_access_key"),
            )
            default_source = config.get("default_source")
            if default_source and isinstance(default_source, str):
                default_source = TranslationLanguage(default_source)
            return AWSTranslate(config_obj, default_source)

        case TranslationProviderType.GCP:
            from grc_ai.translation.gcp_translate import (
                GCPTranslate,
                GCPTranslateConfig,
            )

            config_obj = GCPTranslateConfig(
                project_id=config.get("project_id", ""),
                location=config.get("location", "global"),
                credentials_path=config.get("credentials_path"),
            )
            default_source = config.get("default_source")
            if default_source and isinstance(default_source, str):
                default_source = TranslationLanguage(default_source)
            return GCPTranslate(config_obj, default_source)

        case _:
            raise ValueError(f"Unsupported translation provider: {provider}")


__all__ = [
    "TranslationProviderType",
    "create_translator",
]
