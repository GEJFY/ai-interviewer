"""Factory functions for creating speech providers."""

from enum import StrEnum
from typing import Any

from grc_ai.speech.base import (
    SpeechToTextProvider,
    TextToSpeechProvider,
)


class SpeechProviderType(StrEnum):
    """Supported speech provider types."""

    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"


def create_speech_to_text(
    provider: SpeechProviderType | str,
    **config: Any,
) -> SpeechToTextProvider:
    """Create a speech-to-text provider instance.

    Args:
        provider: The provider type (azure, aws, gcp)
        **config: Provider-specific configuration

    Returns:
        A configured SpeechToTextProvider instance

    Raises:
        ValueError: If the provider type is not supported

    Examples:
        >>> # Azure Speech
        >>> stt = create_speech_to_text(
        ...     "azure",
        ...     subscription_key="your-key",
        ...     region="japaneast",
        ... )

        >>> # AWS Transcribe
        >>> stt = create_speech_to_text(
        ...     "aws",
        ...     region_name="ap-northeast-1",
        ... )

        >>> # GCP Speech-to-Text
        >>> stt = create_speech_to_text(
        ...     "gcp",
        ...     project_id="your-project",
        ... )
    """
    provider_type = SpeechProviderType(provider) if isinstance(provider, str) else provider

    match provider_type:
        case SpeechProviderType.AZURE:
            from grc_ai.speech.azure_speech import AzureSpeechConfig, AzureSpeechToText

            config_obj = AzureSpeechConfig(
                subscription_key=config.get("subscription_key", ""),
                region=config.get("region", "japaneast"),
                default_language=config.get("default_language"),
            )
            return AzureSpeechToText(config_obj)

        case SpeechProviderType.AWS:
            from grc_ai.speech.aws_speech import AWSSpeechConfig, AWSSpeechToText

            config_obj = AWSSpeechConfig(
                region_name=config.get("region_name", "ap-northeast-1"),
                aws_access_key_id=config.get("aws_access_key_id"),
                aws_secret_access_key=config.get("aws_secret_access_key"),
                s3_bucket=config.get("s3_bucket"),
                default_language=config.get("default_language"),
            )
            return AWSSpeechToText(config_obj)

        case SpeechProviderType.GCP:
            from grc_ai.speech.gcp_speech import GCPSpeechConfig, GCPSpeechToText

            config_obj = GCPSpeechConfig(
                project_id=config.get("project_id"),
                credentials_path=config.get("credentials_path"),
                default_language=config.get("default_language"),
            )
            return GCPSpeechToText(config_obj)

        case _:
            raise ValueError(f"Unsupported speech provider: {provider}")


def create_text_to_speech(
    provider: SpeechProviderType | str,
    **config: Any,
) -> TextToSpeechProvider:
    """Create a text-to-speech provider instance.

    Args:
        provider: The provider type (azure, aws, gcp)
        **config: Provider-specific configuration

    Returns:
        A configured TextToSpeechProvider instance

    Raises:
        ValueError: If the provider type is not supported

    Examples:
        >>> # Azure Speech
        >>> tts = create_text_to_speech(
        ...     "azure",
        ...     subscription_key="your-key",
        ...     region="japaneast",
        ... )

        >>> # AWS Polly
        >>> tts = create_text_to_speech(
        ...     "aws",
        ...     region_name="ap-northeast-1",
        ... )

        >>> # GCP Text-to-Speech
        >>> tts = create_text_to_speech(
        ...     "gcp",
        ...     project_id="your-project",
        ... )
    """
    provider_type = SpeechProviderType(provider) if isinstance(provider, str) else provider

    match provider_type:
        case SpeechProviderType.AZURE:
            from grc_ai.speech.azure_speech import AzureSpeechConfig, AzureTextToSpeech

            config_obj = AzureSpeechConfig(
                subscription_key=config.get("subscription_key", ""),
                region=config.get("region", "japaneast"),
                default_language=config.get("default_language"),
            )
            return AzureTextToSpeech(config_obj)

        case SpeechProviderType.AWS:
            from grc_ai.speech.aws_speech import AWSSpeechConfig, AWSTextToSpeech

            config_obj = AWSSpeechConfig(
                region_name=config.get("region_name", "ap-northeast-1"),
                aws_access_key_id=config.get("aws_access_key_id"),
                aws_secret_access_key=config.get("aws_secret_access_key"),
                s3_bucket=config.get("s3_bucket"),
                default_language=config.get("default_language"),
            )
            return AWSTextToSpeech(config_obj)

        case SpeechProviderType.GCP:
            from grc_ai.speech.gcp_speech import GCPSpeechConfig, GCPTextToSpeech

            config_obj = GCPSpeechConfig(
                project_id=config.get("project_id"),
                credentials_path=config.get("credentials_path"),
                default_language=config.get("default_language"),
            )
            return GCPTextToSpeech(config_obj)

        case _:
            raise ValueError(f"Unsupported speech provider: {provider}")


__all__ = [
    "SpeechProviderType",
    "create_speech_to_text",
    "create_text_to_speech",
]
