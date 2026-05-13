"""Configuración centralizada para los agentes de Kommo."""
import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de .env
load_dotenv()

class Settings:
    """Configuración de la aplicación."""
    
    # Kommo API Configuration
    KOMMO_SUBDOMAIN: str = os.getenv("KOMMO_SUBDOMAIN", "new1774376235")
    KOMMO_LONG_TOKEN: str = os.getenv("KOMMO_LONG_TOKEN", "")
    KOMMO_ID: str = os.getenv("KOMMO_ID", "")
    KOMMO_SECRET: str = os.getenv("KOMMO_SECRET", "")
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # WhatsApp Configuration
    WHATSAPP_PHONE_NUMBER: str = os.getenv("WHATSAPP_PHONE_NUMBER", "7744-5475")
    WHATSAPP_API_KEY: Optional[str] = os.getenv("WHATSAPP_API_KEY", None)
    
    # Application Configuration
    APP_NAME: str = "Agentes Kommo"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Configuration
    API_BASE_URL: str = f"https://{KOMMO_SUBDOMAIN}.kommo.com/api/v4"
    
    @classmethod
    def validate(cls) -> bool:
        """Valida que todas las configuraciones necesarias estén presentes."""
        required_fields = [
            ("KOMMO_SUBDOMAIN", cls.KOMMO_SUBDOMAIN),
            ("KOMMO_LONG_TOKEN", cls.KOMMO_LONG_TOKEN),
            ("GEMINI_API_KEY", cls.GEMINI_API_KEY),
        ]
        
        missing = [name for name, value in required_fields if not value]
        if missing:
            raise ValueError(f"Configuraciones faltantes: {', '.join(missing)}")
        return True

settings = Settings()
