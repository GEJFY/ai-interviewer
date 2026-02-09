"""SSOサービスのユニットテスト。

テスト対象: apps/backend/src/grc_backend/services/sso_service.py
"""

from urllib.parse import parse_qs, urlparse

import pytest

from grc_backend.services.sso_service import (
    AzureADProvider,
    OktaProvider,
    SSOConfig,
    SSOProvider,
    SSOService,
    SSOUser,
)


# --- データクラス / enum テスト ---


class TestSSODataClasses:
    """SSO関連データクラスのテスト。"""

    def test_sso_provider_values(self):
        """SSOProviderのenum値が正しいこと。"""
        assert SSOProvider.AZURE_AD == "azure_ad"
        assert SSOProvider.OKTA == "okta"
        assert SSOProvider.GOOGLE == "google"
        assert SSOProvider.OIDC == "oidc"

    def test_sso_user_creation(self):
        """SSOUserが正しく作成されること。"""
        user = SSOUser(
            provider=SSOProvider.AZURE_AD,
            external_id="ext-123",
            email="user@example.com",
            name="テストユーザー",
        )
        assert user.provider == SSOProvider.AZURE_AD
        assert user.email == "user@example.com"
        assert user.given_name is None
        assert user.groups is None

    def test_sso_user_with_optional_fields(self):
        """SSOUserのオプショナルフィールドが設定できること。"""
        user = SSOUser(
            provider=SSOProvider.OKTA,
            external_id="ext-456",
            email="user@example.com",
            name="テストユーザー",
            given_name="太郎",
            family_name="田中",
            groups=["admin", "users"],
            roles=["manager"],
        )
        assert user.given_name == "太郎"
        assert user.groups == ["admin", "users"]

    def test_sso_config_defaults(self):
        """SSOConfigのデフォルト値が正しいこと。"""
        config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client",
            client_secret="test-secret",
        )
        assert config.tenant_id is None
        assert config.issuer_url is None
        assert config.redirect_uri == ""
        assert config.scopes is None


# --- AzureADProvider テスト ---


class TestAzureADProvider:
    """AzureADProvider のテスト。"""

    @pytest.mark.asyncio
    async def test_authorization_url_format(self):
        """認証URLの形式が正しいこと。"""
        config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-secret",
            tenant_id="test-tenant-id",
            redirect_uri="http://localhost:3000/callback",
        )
        provider = AzureADProvider(config)

        url = await provider.get_authorization_url("test-state")
        parsed = urlparse(url)

        assert "login.microsoftonline.com" in parsed.netloc
        assert "test-tenant-id" in parsed.path
        assert "oauth2/v2.0/authorize" in parsed.path

        params = parse_qs(parsed.query)
        assert params["client_id"] == ["test-client-id"]
        assert params["response_type"] == ["code"]
        assert params["state"] == ["test-state"]

        await provider.close()

    @pytest.mark.asyncio
    async def test_default_tenant_id(self):
        """tenant_id未指定時にcommonが使われること。"""
        config = SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="test-client-id",
            client_secret="test-secret",
        )
        provider = AzureADProvider(config)
        assert provider.tenant_id == "common"
        await provider.close()


# --- OktaProvider テスト ---


class TestOktaProvider:
    """OktaProvider のテスト。"""

    @pytest.mark.asyncio
    async def test_authorization_url_format(self):
        """認証URLの形式が正しいこと。"""
        config = SSOConfig(
            provider=SSOProvider.OKTA,
            client_id="okta-client-id",
            client_secret="okta-secret",
            issuer_url="https://dev-example.okta.com/oauth2/default",
            redirect_uri="http://localhost:3000/callback",
        )
        provider = OktaProvider(config)

        url = await provider.get_authorization_url("test-state")
        parsed = urlparse(url)

        assert "okta.com" in parsed.netloc
        assert "/v1/authorize" in parsed.path

        params = parse_qs(parsed.query)
        assert params["client_id"] == ["okta-client-id"]
        assert params["state"] == ["test-state"]

        await provider.close()


# --- SSOService テスト ---


class TestSSOService:
    """SSOService のテスト。"""

    def _make_azure_config(self):
        """テスト用Azure AD設定。"""
        return SSOConfig(
            provider=SSOProvider.AZURE_AD,
            client_id="azure-client",
            client_secret="azure-secret",
            tenant_id="azure-tenant",
            redirect_uri="http://localhost:3000/callback",
        )

    def _make_okta_config(self):
        """テスト用Okta設定。"""
        return SSOConfig(
            provider=SSOProvider.OKTA,
            client_id="okta-client",
            client_secret="okta-secret",
            issuer_url="https://dev-example.okta.com/oauth2/default",
            redirect_uri="http://localhost:3000/callback",
        )

    def test_register_azure_provider(self):
        """Azure ADプロバイダーが登録できること。"""
        service = SSOService()
        service.register_provider("azure", self._make_azure_config())
        assert "azure" in service.get_provider_names()

    def test_register_okta_provider(self):
        """Oktaプロバイダーが登録できること。"""
        service = SSOService()
        service.register_provider("okta", self._make_okta_config())
        assert "okta" in service.get_provider_names()

    def test_register_unsupported_provider(self):
        """非対応プロバイダーでValueErrorが発生すること。"""
        service = SSOService()
        config = SSOConfig(
            provider=SSOProvider.GOOGLE,
            client_id="test",
            client_secret="test",
        )
        with pytest.raises(ValueError, match="Unsupported SSO provider"):
            service.register_provider("google", config)

    def test_get_provider_names(self):
        """登録済みプロバイダー名が取得できること。"""
        service = SSOService()
        service.register_provider("azure", self._make_azure_config())
        service.register_provider("okta", self._make_okta_config())
        names = service.get_provider_names()
        assert "azure" in names
        assert "okta" in names

    @pytest.mark.asyncio
    async def test_initiate_login_returns_url_and_state(self):
        """initiate_loginがURLとstateを返すこと。"""
        service = SSOService()
        service.register_provider("azure", self._make_azure_config())

        auth_url, state = await service.initiate_login("azure")
        assert auth_url.startswith("https://")
        assert len(state) > 10

    @pytest.mark.asyncio
    async def test_initiate_login_unknown_provider(self):
        """未登録プロバイダーでValueErrorが発生すること。"""
        service = SSOService()
        with pytest.raises(ValueError, match="Unknown SSO provider"):
            await service.initiate_login("nonexistent")

    @pytest.mark.asyncio
    async def test_handle_callback_invalid_state(self):
        """無効なstateでValueErrorが発生すること。"""
        service = SSOService()
        with pytest.raises(ValueError, match="Invalid or expired state"):
            await service.handle_callback(code="test-code", state="invalid-state")
