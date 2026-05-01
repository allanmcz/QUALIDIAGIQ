"""Configuração centralizada (pydantic-settings). Camada: Infrastructure."""

from src.infrastructure.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
