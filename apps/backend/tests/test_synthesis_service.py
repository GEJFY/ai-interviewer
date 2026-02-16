"""Unit tests for SynthesisService."""

import pytest

from grc_ai.speech import SpeechLanguage, SpeechProviderType
from grc_backend.services.synthesis_service import SynthesisService, VoiceSettings


class TestSynthesisServiceInit:
    """Tests for service initialisation."""

    def test_default_provider(self):
        """Defaults to Azure provider."""
        service = SynthesisService()
        assert service.provider_type == SpeechProviderType.AZURE

    def test_string_provider(self):
        """Accepts provider type as string."""
        service = SynthesisService(provider_type="aws")
        assert service.provider_type == SpeechProviderType.AWS

    def test_enum_provider(self):
        service = SynthesisService(provider_type=SpeechProviderType.GCP)
        assert service.provider_type == SpeechProviderType.GCP

    def test_extra_config(self):
        service = SynthesisService(subscription_key="key123", region="japaneast")
        assert service.provider_config["subscription_key"] == "key123"
        assert service.provider_config["region"] == "japaneast"


class TestVoiceSettings:
    """Tests for VoiceSettings dataclass."""

    def test_defaults(self):
        s = VoiceSettings()
        assert s.voice_id is None
        assert s.language == SpeechLanguage.JA
        assert s.speaking_rate == 1.0
        assert s.pitch == 0.0

    def test_custom_values(self):
        s = VoiceSettings(
            voice_id="ja-JP-NanamiNeural",
            language=SpeechLanguage.EN,
            speaking_rate=1.5,
            pitch=2.0,
        )
        assert s.voice_id == "ja-JP-NanamiNeural"
        assert s.language == SpeechLanguage.EN
        assert s.speaking_rate == 1.5
        assert s.pitch == 2.0


class TestDefaultVoiceManagement:
    """Tests for default voice get/set."""

    @pytest.fixture
    def service(self):
        return SynthesisService()

    def test_set_default_voice(self, service):
        service.set_default_voice(SpeechLanguage.JA, "ja-JP-NanamiNeural")
        assert service._default_voices[SpeechLanguage.JA] == "ja-JP-NanamiNeural"

    def test_set_multiple_defaults(self, service):
        service.set_default_voice(SpeechLanguage.JA, "ja-voice")
        service.set_default_voice(SpeechLanguage.EN, "en-voice")
        assert service._default_voices[SpeechLanguage.JA] == "ja-voice"
        assert service._default_voices[SpeechLanguage.EN] == "en-voice"

    def test_override_default(self, service):
        service.set_default_voice(SpeechLanguage.JA, "voice-1")
        service.set_default_voice(SpeechLanguage.JA, "voice-2")
        assert service._default_voices[SpeechLanguage.JA] == "voice-2"


class TestVoiceCache:
    """Tests for voice cache."""

    def test_cache_initially_empty(self):
        service = SynthesisService()
        assert service._voice_cache == []
