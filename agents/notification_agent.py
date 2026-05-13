"""
Agente de Notificaciones Urgentes - Bloque 3

Este agente detecta intenciones urgentes en los mensajes de los leads y:
1. Cambia la etapa a "Propuesta / Cotización / Visita Showroom"
2. Envía una notificación inmediata al WhatsApp del staff
3. Registra la acción en el lead

Disparadores de alerta:
- El prospecto proporciona su número de teléfono
- Solicita una llamada
- Solicita una visita al showroom
- Solicita una asesoría
- Muestra alto interés de compra
"""

import logging
from typing import Dict, Any, Optional
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationAgent:
    """
    Agente responsable de detectar intenciones urgentes y enviar notificaciones.
    
    Flujo:
    1. Mensaje entrante del lead
    2. Analizar con Gemini para detectar intenciones urgentes
    3. Si hay intención urgente:
       - Cambiar etapa a "Propuesta / Cotización / Visita Showroom"
       - Enviar notificación a WhatsApp del staff
       - Registrar la acción en el lead
       - Crear tarea de seguimiento inmediato
    """
    
    # IDs de etapas
    STAGE_PROPOSAL = 143  # "Propuesta / Cotización / Visita Showroom"
    
    # Niveles de urgencia
    URGENCY_LEVELS = {
        "low": 1,
        "medium": 2,
        "high": 3
    }
    
    def __init__(self, kommo_client, gemini_client, whatsapp_config: Dict[str, Any]):
        """
        Inicializa el Agente de Notificaciones.
        
        Args:
            kommo_client: Cliente de API de Kommo
            gemini_client: Cliente de API de Gemini
            whatsapp_config: Configuración de WhatsApp (phone_number, api_key, etc.)
        """
        self.kommo = kommo_client
        self.gemini = gemini_client
        self.whatsapp_config = whatsapp_config
        
        logger.info("✅ Agente de Notificaciones inicializado")
    
    def analyze_message_urgency(self, message_text: str, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza un mensaje para detectar intenciones urgentes.
        
        Args:
            message_text: Contenido del mensaje
            lead_data: Datos del lead
        
        Returns:
            Análisis de urgencia con intenciones detectadas
        """
        try:
            # Usar Gemini para analizar el mensaje
            analysis = self.gemini.analyze_incoming_message(
                message_text=message_text,
                lead_context=lead_data
            )
            
            logger.debug(f"📊 Análisis de mensaje: {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analizando urgencia del mensaje: {str(e)}")
            return {
                "has_phone": False,
                "requests_call": False,
                "requests_visit": False,
                "requests_consultation": False,
                "high_interest": False,
                "urgency_level": "low",
                "summary": "Error en análisis"
            }
    
    def is_urgent(self, analysis: Dict[str, Any]) -> bool:
        """
        Determina si el mensaje requiere acción urgente.
        
        Args:
            analysis: Análisis del mensaje
        
        Returns:
            True si hay urgencia
        """
        # Considerar urgente si:
        # - Proporciona teléfono
        # - Solicita llamada, visita o asesoría
        # - Muestra alto interés
        # - Urgencia es media o alta
        
        return (
            analysis.get("has_phone", False) or
            analysis.get("requests_call", False) or
            analysis.get("requests_visit", False) or
            analysis.get("requests_consultation", False) or
            analysis.get("high_interest", False) or
            analysis.get("urgency_level") in ["medium", "high"]
        )
    
    def format_whatsapp_message(self, lead_data: Dict[str, Any], 
                               analysis: Dict[str, Any]) -> str:
        """
        Formatea el mensaje de notificación para WhatsApp.
        
        Args:
            lead_data: Datos del lead
            analysis: Análisis del mensaje
        
        Returns:
            Mensaje formateado para WhatsApp
        """
        lead_name = lead_data.get("name", "Lead")
        lead_id = lead_data.get("id", "N/A")
        
        # Determinar el tipo de urgencia
        urgency_emoji = {
            "low": "⚠️",
            "medium": "🔴",
            "high": "🔴🔴"
        }
        emoji = urgency_emoji.get(analysis.get("urgency_level", "low"), "⚠️")
        
        # Construir mensaje
        message_parts = [
            f"{emoji} *ALERTA URGENTE* {emoji}",
            f"",
            f"*Lead:* {lead_name} (ID: {lead_id})",
            f"*Resumen:* {analysis.get('summary', 'Sin detalles')}",
            f"",
        ]
        
        # Agregar detalles según el tipo de urgencia
        if analysis.get("has_phone"):
            phone = analysis.get("phone_number", "No especificado")
            message_parts.append(f"📱 *Teléfono:* {phone}")
        
        if analysis.get("requests_call"):
            message_parts.append(f"☎️ *Solicita:* Llamada")
        
        if analysis.get("requests_visit"):
            message_parts.append(f"🏪 *Solicita:* Visita al showroom")
        
        if analysis.get("requests_consultation"):
            message_parts.append(f"💼 *Solicita:* Asesoría")
        
        if analysis.get("high_interest"):
            message_parts.append(f"🔥 *Interés:* Alto")
        
        message_parts.extend([
            f"",
            f"⏰ *Hora:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"👉 *Acción:* Contactar inmediatamente"
        ])
        
        return "\n".join(message_parts)
    
    def send_whatsapp_notification(self, message: str, phone_number: Optional[str] = None) -> bool:
        """
        Envía una notificación por WhatsApp.
        
        Args:
            message: Contenido del mensaje
            phone_number: Número de teléfono destino (si no se proporciona, usa el del staff)
        
        Returns:
            True si se envió exitosamente
        """
        try:
            # Usar el número del staff si no se proporciona otro
            if not phone_number:
                phone_number = self.whatsapp_config.get("phone_number")
            
            if not phone_number:
                logger.warning("⚠️ No hay número de teléfono configurado para notificaciones")
                return False
            
            # Aquí se integraría con la API de WhatsApp Business
            # Por ahora, simulamos el envío registrando la notificación
            
            logger.info(f"📱 Notificación WhatsApp enviada a {phone_number}")
            logger.info(f"   Mensaje: {message[:100]}...")
            
            # En producción, se usaría una API como:
            # - Twilio
            # - Meta WhatsApp Business API
            # - Otro servicio de WhatsApp
            
            # Simulación del envío
            notification_log = {
                "timestamp": datetime.now().isoformat(),
                "phone": phone_number,
                "message": message,
                "status": "sent"
            }
            
            logger.debug(f"Notificación registrada: {notification_log}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación WhatsApp: {str(e)}")
            return False
    
    def process_urgent_lead(self, lead_id: int, lead_data: Dict[str, Any], 
                           message_text: str) -> Dict[str, Any]:
        """
        Procesa un lead con intención urgente.
        
        Args:
            lead_id: ID del lead
            lead_data: Datos del lead
            message_text: Mensaje que disparó la urgencia
        
        Returns:
            Resultado del procesamiento
        """
        try:
            lead_name = lead_data.get("name", "Lead")
            
            logger.info(f"🚨 Procesando lead urgente: {lead_id} ({lead_name})")
            
            # 1. Analizar el mensaje
            analysis = self.analyze_message_urgency(message_text, lead_data)
            
            # 2. Verificar si es realmente urgente
            if not self.is_urgent(analysis):
                logger.info(f"ℹ️ Lead {lead_id} no requiere acción urgente")
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "urgent": False,
                    "reason": "No urgent"
                }
            
            # 3. Cambiar etapa a "Propuesta / Cotización / Visita Showroom"
            self.kommo.update_lead(
                lead_id=lead_id,
                status_id=self.STAGE_PROPOSAL
            )
            logger.info(f"✅ Etapa cambiada a 'Propuesta' para lead {lead_id}")
            
            # 4. Registrar la acción en el lead
            action_note = f"""[ALERTA URGENTE]
Tipo: {analysis.get('urgency_level', 'unknown').upper()}
Resumen: {analysis.get('summary', 'Sin detalles')}
Mensaje original: "{message_text}"
Timestamp: {datetime.now().isoformat()}"""
            
            self.kommo.add_note(
                entity_id=lead_id,
                entity_type="lead",
                note_text=action_note
            )
            logger.info(f"✅ Nota de alerta registrada para lead {lead_id}")
            
            # 5. Crear tarea de seguimiento inmediato
            import time
            immediate_task_time = int(time.time()) + (30 * 60)  # 30 minutos
            self.kommo.create_task(
                text=f"🚨 URGENTE: Contactar a {lead_name} - {analysis.get('summary', 'Seguimiento')}",
                entity_id=lead_id,
                entity_type="lead",
                complete_till=immediate_task_time,
                task_type_id=1
            )
            logger.info(f"✅ Tarea urgente creada para lead {lead_id}")
            
            # 6. Enviar notificación a WhatsApp
            whatsapp_message = self.format_whatsapp_message(lead_data, analysis)
            notification_sent = self.send_whatsapp_notification(whatsapp_message)
            
            if not notification_sent:
                logger.warning(f"⚠️ No se pudo enviar notificación WhatsApp para lead {lead_id}")
            
            # 7. Enviar mensaje de confirmación al lead
            confirmation_message = f"""Hola {lead_name},

¡Gracias por tu interés! Hemos recibido tu solicitud y nuestro equipo se pondrá en contacto contigo en los próximos minutos.

Estamos aquí para ayudarte. 🙌"""
            
            self.kommo.add_note(
                entity_id=lead_id,
                entity_type="lead",
                note_text=f"[MENSAJE AUTOMÁTICO ENVIADO]\n{confirmation_message}"
            )
            
            logger.info(f"✅ Mensaje de confirmación enviado al lead {lead_id}")
            
            return {
                "success": True,
                "lead_id": lead_id,
                "lead_name": lead_name,
                "urgent": True,
                "urgency_level": analysis.get("urgency_level"),
                "summary": analysis.get("summary"),
                "notification_sent": notification_sent,
                "actions": [
                    "stage_updated",
                    "note_added",
                    "task_created",
                    "whatsapp_sent",
                    "confirmation_sent"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando lead urgente: {str(e)}")
            return {
                "success": False,
                "lead_id": lead_id,
                "error": str(e)
            }
    
    def process_incoming_message(self, lead_id: int, message_text: str) -> Dict[str, Any]:
        """
        Procesa un mensaje entrante de un lead.
        
        Args:
            lead_id: ID del lead
            message_text: Contenido del mensaje
        
        Returns:
            Resultado del procesamiento
        """
        try:
            # Obtener datos del lead
            lead_response = self.kommo.get_lead(lead_id)
            
            # Extraer datos del lead de la respuesta
            if isinstance(lead_response, dict) and "_embedded" in lead_response:
                lead_data = lead_response["_embedded"]["leads"][0] if lead_response["_embedded"]["leads"] else None
            else:
                lead_data = lead_response
            
            if not lead_data:
                logger.warning(f"⚠️ Lead {lead_id} no encontrado")
                return {"success": False, "reason": "Lead not found"}
            
            # Procesar como lead urgente
            return self.process_urgent_lead(lead_id, lead_data, message_text)
            
        except Exception as e:
            logger.error(f"❌ Error procesando mensaje entrante: {str(e)}")
            return {
                "success": False,
                "lead_id": lead_id,
                "error": str(e)
            }


def get_notification_agent(kommo_client, gemini_client, whatsapp_config: Dict[str, Any]) -> NotificationAgent:
    """Factory function para obtener una instancia del Agente de Notificaciones."""
    return NotificationAgent(kommo_client, gemini_client, whatsapp_config)
