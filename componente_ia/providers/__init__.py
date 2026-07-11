"""Interfaces y proveedores locales del asistente."""

from componente_ia.providers.base_provider import BaseProvider, ProviderRequest, ProviderResult
from componente_ia.providers.fallback_provider import FallbackProvider
from componente_ia.providers.local_provider import LocalProvider

__all__ = [
    "BaseProvider",
    "ProviderRequest",
    "ProviderResult",
    "LocalProvider",
    "FallbackProvider",
]
