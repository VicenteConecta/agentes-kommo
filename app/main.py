"""
Aplicación FastAPI principal para los agentes de Kommo.
"""
import logging
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar configuración y clientes
from config.settings import settings
from clients.kommo_client import get_kommo_client
from clients.gemini_client import get_gemini_client
from agents.qualifier_agent import QualifierAgent
from agents.followup_agent import get_followup_agent
from agents.notification_agent import get_notification_agent

# Inicializar aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de agentes inteligentes para Kommo CRM"
)

# Inicializar clientes globales
try:
    settings.validate()
    kommo_client = get_kommo_client()
    gemini_client = get_gemini_client()
    qualifier_agent = QualifierAgent(kommo_client, gemini_client)
    
    # Inicializar agentes del Bloque 2 y 3
    followup_agent = get_followup_agent(kommo_client, gemini_client)
    
    whatsapp_config = {
        "phone_number": settings.WHATSAPP_PHONE_NUMBER,
        "api_key": getattr(settings, 'WHATSAPP_API_KEY', None)
    }
    notification_agent = get_notification_agent(kommo_client, gemini_client, whatsapp_config)
    
    logger.info("✅ Todos los clientes y agentes inicializados correctamente")
except ValueError as e:
    logger.error(f"❌ Error en configuración: {e}")
    raise

# ============ Modelos Pydantic ============

class WebhookPayload(BaseModel):
    """Modelo para payloads de webhooks de Kommo."""
    event: str
    data: Dict[str, Any]
    account_id: Optional[int] = None
    time: Optional[str] = None

class HealthCheck(BaseModel):
    """Modelo para respuesta de health check."""
    status: str
    version: str
    kommo_connected: bool
    gemini_connected: bool

# ============ Endpoints de Health ============

@app.get("/", tags=["Health"])
async def root():
    """Endpoint raíz."""
    return {
        "message": "Agentes Kommo API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "agents": ["Qualifier", "FollowUp", "Notification"]
    }

@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """
    Verifica el estado de la aplicación y la conectividad con servicios externos.
    """
    kommo_ok = False
    gemini_ok = False
    
    try:
        # Verificar conexión con Kommo
        account_info = kommo_client.get_account_info()
        kommo_ok = "id" in account_info
        logger.info(f"✅ Kommo conectado: {account_info.get('name', 'Unknown')}")
    except Exception as e:
        logger.error(f"❌ Error conectando con Kommo: {e}")
    
    try:
        # Verificar conexión con Gemini
        response = gemini_client.model.generate_content("Responde con 'OK'")
        gemini_ok = response.text is not None
        logger.info("✅ Gemini conectado correctamente")
    except Exception as e:
        logger.error(f"❌ Error conectando con Gemini: {e}")
    
    status = "healthy" if (kommo_ok and gemini_ok) else "degraded"
    
    return HealthCheck(
        status=status,
        version=settings.APP_VERSION,
        kommo_connected=kommo_ok,
        gemini_connected=gemini_ok
    )

# ============ Webhooks Endpoints - Bloque 1 ============

@app.post("/webhooks/kommo/lead-added", tags=["Webhooks", "Bloque 1"])
async def webhook_lead_added(payload: WebhookPayload):
    """
    Webhook para cuando se agrega un nuevo lead.
    Dispara el Agente Calificador (Bloque 1).
    """
    try:
        logger.info(f"📥 Webhook lead-added recibido: {payload.data}")
        
        lead_id = payload.data.get("id")
        if not lead_id:
            raise HTTPException(status_code=400, detail="Lead ID no encontrado en payload")
        
        # Procesar lead de forma asíncrona
        result = await qualifier_agent.process_new_lead(
            lead_id=lead_id,
            lead_data=payload.data
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        logger.error(f"❌ Error procesando webhook lead-added: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/webhooks/kommo/message-received", tags=["Webhooks", "Bloque 1 & 3"])
async def webhook_message_received(payload: WebhookPayload):
    """
    Webhook para cuando se recibe un mensaje de un lead.
    Procesa respuestas de calificación (Bloque 1) y detecta urgencias (Bloque 3).
    """
    try:
        logger.info(f"📥 Webhook message-received recibido: {payload.data}")
        
        lead_id = payload.data.get("lead_id")
        message_text = payload.data.get("message", "")
        
        if not lead_id:
            raise HTTPException(status_code=400, detail="Lead ID no encontrado en payload")
        
        # Procesar respuesta del lead para calificación
        qualifier_result = await qualifier_agent.process_lead_response(
            lead_id=lead_id,
            message_text=message_text
        )
        
        # Procesar para detectar urgencias (Bloque 3)
        notification_result = notification_agent.process_incoming_message(
            lead_id=lead_id,
            message_text=message_text
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "qualifier": qualifier_result,
                "notification": notification_result
            }
        )
    
    except Exception as e:
        logger.error(f"❌ Error procesando webhook message-received: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/webhooks/kommo/lead-edited", tags=["Webhooks", "Bloque 2"])
async def webhook_lead_edited(payload: WebhookPayload):
    """
    Webhook para cuando se edita un lead.
    Usado por el Agente de Seguimiento (Bloque 2).
    """
    try:
        logger.info(f"📥 Webhook lead-edited recibido: {payload.data}")
        
        lead_id = payload.data.get("id")
        if not lead_id:
            raise HTTPException(status_code=400, detail="Lead ID no encontrado en payload")
        
        # El Agente de Seguimiento lo procesará en el batch
        logger.info(f"✅ Evento de edición registrado para lead {lead_id}")
        
        return JSONResponse(
            status_code=200,
            content={"status": "received", "message": "Evento registrado para procesamiento posterior"}
        )
    
    except Exception as e:
        logger.error(f"❌ Error procesando webhook lead-edited: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# ============ Tasks Endpoints - Bloque 2 ============

@app.post("/tasks/followup-batch", tags=["Tasks", "Bloque 2"])
async def task_followup_batch():
    """
    Ejecuta el batch de seguimientos automáticos.
    Debe ser llamado por Cloud Scheduler cada hora.
    """
    try:
        logger.info("🚀 Iniciando batch de seguimientos...")
        
        result = followup_agent.run_followup_batch()
        
        logger.info(f"✅ Batch completado: {result['total_processed']} leads procesados")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
    
    except Exception as e:
        logger.error(f"❌ Error ejecutando batch de seguimientos: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# ============ Test Endpoints ============

@app.get("/test/kommo-connection", tags=["Test"])
async def test_kommo_connection():
    """
    Endpoint de prueba para verificar la conexión con Kommo.
    """
    try:
        account_info = kommo_client.get_account_info()
        return JSONResponse(
            status_code=200,
            content={
                "status": "connected",
                "account": account_info
            }
        )
    except Exception as e:
        logger.error(f"Error conectando con Kommo: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/test/gemini-connection", tags=["Test"])
async def test_gemini_connection():
    """
    Endpoint de prueba para verificar la conexión con Gemini.
    """
    try:
        response = gemini_client.model.generate_content("Responde con 'OK'")
        return JSONResponse(
            status_code=200,
            content={
                "status": "connected",
                "response": response.text
            }
        )
    except Exception as e:
        logger.error(f"Error conectando con Gemini: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/test/agents-status", tags=["Test"])
async def test_agents_status():
    """
    Endpoint de prueba para verificar el estado de todos los agentes.
    """
    return JSONResponse(
        status_code=200,
        content={
            "qualifier_agent": "initialized",
            "followup_agent": "initialized",
            "notification_agent": "initialized",
            "whatsapp_phone": settings.WHATSAPP_PHONE_NUMBER,
            "timestamp": str(__import__('datetime').datetime.now())
        }
    )

# ============ Error Handlers ============

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador de excepciones HTTP."""
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador de excepciones generales."""
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# ============ Startup Event ============

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación."""
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║        AGENTES KOMMO - INICIANDO APLICACIÓN               ║")
    logger.info("╚════════════════════════════════════════════════════════════╝")
    logger.info(f"✅ Aplicación iniciada: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"✅ Kommo Subdomain: {settings.KOMMO_SUBDOMAIN}")
    logger.info(f"✅ WhatsApp Phone: {settings.WHATSAPP_PHONE_NUMBER}")
    logger.info("✅ Todos los agentes listos para recibir eventos")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación."""
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║        AGENTES KOMMO - CERRANDO APLICACIÓN                ║")
    logger.info("╚════════════════════════════════════════════════════════════╝")
