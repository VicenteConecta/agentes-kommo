from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentes Kommo", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    logger.info("✅ Agentes Kommo iniciados")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhooks/kommo/lead-added")
async def webhook_lead_added(data: dict):
    logger.info(f"Webhook recibido: {data}")
    return {"status": "received"}
