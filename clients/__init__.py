"""Paquete de clientes para APIs externas."""
from .kommo_client import KommoClient, get_kommo_client
from .gemini_client import GeminiClient, get_gemini_client

__all__ = ["KommoClient", "get_kommo_client", "GeminiClient", "get_gemini_client"]
