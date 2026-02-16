"""SSO (Single Sign-On) authentication service.

Supports multiple identity providers:
- Azure AD (Microsoft Entra ID)
- Okta
"""

import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


class SSOProvider(StrEnum):
    """Supported SSO providers."""

    AZURE_AD = "azure_ad"
    OKTA = "okta"


@dataclass
class SSOUser:
    """User information from SSO provider."""

    provider: SSOProvider
    external_id: str
    email: str
    name: str
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    groups: list[str] | None = None
    roles: list[str] | None = None
    raw_claims: dict[str, Any] | None = None


@dataclass
class SSOConfig:
    """Configuration for SSO provider."""

    provider: SSOProvider
    client_id: str
    client_secret: str
    tenant_id: str | None = None  # For Azure AD
    issuer_url: str | None = None  # For Okta/OIDC
    redirect_uri: str = ""
    scopes: list[str] | None = None


class BaseSSOProvider(ABC):
    """Base class for SSO providers."""

    def __init__(self, config: SSOConfig):
        self.config = config
        self._http_client = httpx.AsyncClient()

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """Get the authorization URL for SSO login."""
        pass

    @abstractmethod
    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens."""
        pass

    @abstractmethod
    async def get_user_info(self, access_token: str) -> SSOUser:
        """Get user information from the provider."""
        pass

    async def close(self):
        """Close HTTP client."""
        await self._http_client.aclose()


class AzureADProvider(BaseSSOProvider):
    """Azure AD (Microsoft Entra ID) SSO provider."""

    def __init__(self, config: SSOConfig):
        super().__init__(config)
        self.tenant_id = config.tenant_id or "common"
        self.base_url = f"https://login.microsoftonline.com/{self.tenant_id}"

    async def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "response_mode": "query",
            "scope": " ".join(self.config.scopes or ["openid", "profile", "email"]),
            "state": state,
        }
        return f"{self.base_url}/oauth2/v2.0/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        response = await self._http_client.post(
            f"{self.base_url}/oauth2/v2.0/token",
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_user_info(self, access_token: str) -> SSOUser:
        response = await self._http_client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

        # Get group memberships
        groups = []
        try:
            groups_response = await self._http_client.get(
                "https://graph.microsoft.com/v1.0/me/memberOf",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if groups_response.status_code == 200:
                groups_data = groups_response.json()
                groups = [
                    g.get("displayName")
                    for g in groups_data.get("value", [])
                    if g.get("@odata.type") == "#microsoft.graph.group"
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch groups: {e}")

        return SSOUser(
            provider=SSOProvider.AZURE_AD,
            external_id=data["id"],
            email=data.get("mail") or data.get("userPrincipalName", ""),
            name=data.get("displayName", ""),
            given_name=data.get("givenName"),
            family_name=data.get("surname"),
            groups=groups,
            raw_claims=data,
        )


class OktaProvider(BaseSSOProvider):
    """Okta SSO provider."""

    def __init__(self, config: SSOConfig):
        super().__init__(config)
        self.issuer_url = config.issuer_url or ""

    async def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes or ["openid", "profile", "email", "groups"]),
            "state": state,
        }
        return f"{self.issuer_url}/v1/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        response = await self._http_client.post(
            f"{self.issuer_url}/v1/token",
            data={
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "redirect_uri": self.config.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_user_info(self, access_token: str) -> SSOUser:
        response = await self._http_client.get(
            f"{self.issuer_url}/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        data = response.json()

        return SSOUser(
            provider=SSOProvider.OKTA,
            external_id=data["sub"],
            email=data.get("email", ""),
            name=data.get("name", ""),
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            picture=data.get("picture"),
            groups=data.get("groups", []),
            raw_claims=data,
        )


class SSOService:
    """Service for managing SSO authentication.

    Provides unified interface for multiple SSO providers
    with session management and user provisioning.
    """

    def __init__(self):
        self._providers: dict[str, BaseSSOProvider] = {}
        self._states: dict[str, dict[str, Any]] = {}  # state -> metadata

    def register_provider(self, name: str, config: SSOConfig) -> None:
        """Register an SSO provider.

        Args:
            name: Unique name for this provider configuration
            config: Provider configuration
        """
        match config.provider:
            case SSOProvider.AZURE_AD:
                provider = AzureADProvider(config)
            case SSOProvider.OKTA:
                provider = OktaProvider(config)
            case _:
                raise ValueError(f"Unsupported SSO provider: {config.provider}")

        self._providers[name] = provider
        logger.info(f"Registered SSO provider: {name} ({config.provider.value})")

    async def initiate_login(
        self,
        provider_name: str,
        return_url: str | None = None,
    ) -> tuple[str, str]:
        """Initiate SSO login flow.

        Args:
            provider_name: Name of the registered provider
            return_url: URL to redirect after successful login

        Returns:
            Tuple of (authorization_url, state_token)
        """
        if provider_name not in self._providers:
            raise ValueError(f"Unknown SSO provider: {provider_name}")

        provider = self._providers[provider_name]

        # Generate state token
        state = secrets.token_urlsafe(32)
        self._states[state] = {
            "provider": provider_name,
            "return_url": return_url,
            "created_at": datetime.utcnow(),
        }

        # Get authorization URL
        auth_url = await provider.get_authorization_url(state)

        return auth_url, state

    async def handle_callback(
        self,
        code: str,
        state: str,
    ) -> tuple[SSOUser, str | None]:
        """Handle SSO callback after user authentication.

        Args:
            code: Authorization code from provider
            state: State token from initiate_login

        Returns:
            Tuple of (SSOUser, return_url)

        Raises:
            ValueError: If state is invalid or expired
        """
        # Validate state
        if state not in self._states:
            raise ValueError("Invalid or expired state token")

        state_data = self._states.pop(state)

        # Check expiration (10 minute window)
        if datetime.utcnow() - state_data["created_at"] > timedelta(minutes=10):
            raise ValueError("State token expired")

        provider_name = state_data["provider"]
        provider = self._providers[provider_name]

        # Exchange code for tokens
        tokens = await provider.exchange_code(code)
        access_token = tokens["access_token"]

        # Get user info
        user = await provider.get_user_info(access_token)

        return user, state_data.get("return_url")

    def get_provider_names(self) -> list[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())

    async def cleanup(self) -> None:
        """Cleanup resources."""
        for provider in self._providers.values():
            await provider.close()

        # Clean expired states
        now = datetime.utcnow()
        expired = [
            state
            for state, data in self._states.items()
            if now - data["created_at"] > timedelta(minutes=10)
        ]
        for state in expired:
            del self._states[state]


# Singleton instance
_sso_service: SSOService | None = None


def get_sso_service() -> SSOService:
    """Get or create the SSO service singleton."""
    global _sso_service
    if _sso_service is None:
        _sso_service = SSOService()
    return _sso_service


def configure_sso_from_settings() -> None:
    """Configure SSO providers from application settings."""
    from grc_backend.config import get_settings

    settings = get_settings()
    sso = get_sso_service()

    # Azure AD configuration
    azure_client_id = getattr(settings, "azure_ad_client_id", None)
    if azure_client_id:
        sso.register_provider(
            "azure_ad",
            SSOConfig(
                provider=SSOProvider.AZURE_AD,
                client_id=azure_client_id,
                client_secret=getattr(settings, "azure_ad_client_secret", ""),
                tenant_id=getattr(settings, "azure_ad_tenant_id", None),
                redirect_uri=getattr(settings, "sso_redirect_uri", ""),
                scopes=["openid", "profile", "email", "User.Read"],
            ),
        )

    # Okta configuration
    okta_client_id = getattr(settings, "okta_client_id", None)
    if okta_client_id:
        sso.register_provider(
            "okta",
            SSOConfig(
                provider=SSOProvider.OKTA,
                client_id=okta_client_id,
                client_secret=getattr(settings, "okta_client_secret", ""),
                issuer_url=getattr(settings, "okta_issuer_url", ""),
                redirect_uri=getattr(settings, "sso_redirect_uri", ""),
                scopes=["openid", "profile", "email", "groups"],
            ),
        )
