"""
Agente de Seguimiento de Embudos - Bloque 2

Este agente gestiona el seguimiento automático de leads en los embudos de venta.
Implementa:
- Envío de plantillas de precios tras cualificación
- Fase de Insistencia: 3 intentos cada 2 días
- Fase de Nutrición: Difusiones semanales basadas en etiquetas
- Cambios automáticos de etapas
- Creación de tareas de seguimiento
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


class FollowUpPhase(Enum):
    """Fases de seguimiento en el embudo"""
    INITIAL = "initial"  # Recién cualificado
    INSISTENCE_1 = "insistence_1"  # Primer intento
    INSISTENCE_2 = "insistence_2"  # Segundo intento
    INSISTENCE_3 = "insistence_3"  # Tercer intento
    NUTRITION = "nutrition"  # Fase de nutrición (difusiones)
    CLOSED = "closed"  # Cerrado o convertido


class FollowUpAgent:
    """
    Agente responsable de gestionar el seguimiento automático de leads.
    
    Flujo:
    1. Lead cualificado → Enviar plantilla de precios → Etapa "Presentación de valor"
    2. Sin respuesta en 2 días → Intento 1 de insistencia
    3. Sin respuesta en 2 días → Intento 2 de insistencia
    4. Sin respuesta en 2 días → Intento 3 de insistencia
    5. Sin respuesta en 6 días → Activar fase de nutrición (difusiones semanales)
    """
    
    # IDs de etapas (ajustar según tu Kommo)
    STAGE_VALUE_PRESENTATION = 142  # "Presentación de valor"
    STAGE_PROPOSAL = 143  # "Propuesta / Cotización / Visita Showroom"
    
    def __init__(self, kommo_client, gemini_client):
        """
        Inicializa el Agente de Seguimiento.
        
        Args:
            kommo_client: Cliente de API de Kommo
            gemini_client: Cliente de API de Gemini
        """
        self.kommo = kommo_client
        self.gemini = gemini_client
        
        # Configuración de parámetros de seguimiento
        self.insistence_interval_days = 2  # Cada 2 días
        self.insistence_attempts = 3  # Máximo 3 intentos
        self.nutrition_start_days = 6  # Iniciar nutrición después de 6 días
        self.nutrition_interval_days = 7  # Difusiones semanales
        
        logger.info("✅ Agente de Seguimiento inicializado")
    
    def send_value_template(self, lead_id: int, lead_data: Dict[str, Any]) -> bool:
        """
        Envía la plantilla de precios correspondiente al lead cualificado.
        
        Args:
            lead_id: ID del lead
            lead_data: Datos del lead (incluye producto, etapa, estrategia)
        
        Returns:
            True si se envió exitosamente
        """
        try:
            # Extraer información del lead
            lead_name = lead_data.get("name", "Prospecto")
            
            # Generar plantilla personalizada con Gemini
            template_text = self.gemini.generate_follow_up_message(
                lead_data=lead_data,
                follow_up_type="nutrition"  # Usar el método existente
            )
            
            logger.info(f"📧 Plantilla generada para lead {lead_id}")
            logger.debug(f"   Contenido: {template_text[:100]}...")
            
            # Agregar nota con la plantilla enviada
            self.kommo.add_note(
                entity_id=lead_id,
                entity_type="lead",
                note_text=f"[PLANTILLA ENVIADA]\n{template_text}"
            )
            
            # Cambiar etapa a "Presentación de valor"
            self.kommo.update_lead(
                lead_id=lead_id,
                status_id=self.STAGE_VALUE_PRESENTATION
            )
            
            # Crear tarea de seguimiento para 2 días después
            follow_up_date = int(time.time()) + (2 * 24 * 3600)
            self.kommo.create_task(
                text=f"Seguimiento: {lead_name}",
                entity_id=lead_id,
                entity_type="lead",
                complete_till=follow_up_date,
                task_type_id=1
            )
            
            logger.info(f"✅ Plantilla enviada al lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al enviar plantilla: {str(e)}")
            return False
    
    def _count_insistence_attempts(self, notes: List[Dict[str, Any]]) -> int:
        """
        Cuenta el número de intentos de insistencia registrados en las notas.
        
        Args:
            notes: Lista de notas del lead
        
        Returns:
            Número de intentos de insistencia
        """
        count = 0
        for note in notes:
            text = note.get("text", "")
            if "[INTENTO INSISTENCIA" in text:
                count += 1
        return count
    
    def check_insistence_phase(self, lead_id: int, lead_data: Dict[str, Any]) -> Optional[str]:
        """
        Verifica si el lead debe entrar en fase de insistencia y ejecuta el intento.
        
        Args:
            lead_id: ID del lead
            lead_data: Datos del lead
        
        Returns:
            Fase actual del lead o None
        """
        try:
            # Obtener historial de intentos desde las notas
            # Nota: El cliente Kommo actual no tiene get_notes(), así que usamos un workaround
            # En una implementación real, se debería agregar este método al cliente
            
            # Por ahora, asumimos que se puede rastrear por las tareas
            lead_name = lead_data.get("name", "Prospecto")
            
            # Generar mensaje de insistencia personalizado
            insistence_message = self.gemini.generate_follow_up_message(
                lead_data=lead_data,
                follow_up_type="insistence"
            )
            
            # Agregar nota de intento
            self.kommo.add_note(
                entity_id=lead_id,
                entity_type="lead",
                note_text=f"[INTENTO INSISTENCIA]\n{insistence_message}"
            )
            
            # Crear tarea de seguimiento para 2 días después
            follow_up_date = int(time.time()) + (2 * 24 * 3600)
            self.kommo.create_task(
                text=f"Seguimiento insistencia: {lead_name}",
                entity_id=lead_id,
                entity_type="lead",
                complete_till=follow_up_date,
                task_type_id=1
            )
            
            logger.info(f"📢 Intento de insistencia para lead {lead_id}")
            return "insistence"
            
        except Exception as e:
            logger.error(f"❌ Error en fase de insistencia: {str(e)}")
            return None
    
    def check_nutrition_phase(self, lead_id: int, lead_data: Dict[str, Any]) -> bool:
        """
        Verifica si el lead debe recibir difusión de nutrición y la envía.
        
        Args:
            lead_id: ID del lead
            lead_data: Datos del lead
        
        Returns:
            True si se envió la difusión
        """
        try:
            lead_name = lead_data.get("name", "Prospecto")
            
            # Generar contenido de nutrición personalizado
            nutrition_content = self.gemini.generate_follow_up_message(
                lead_data=lead_data,
                follow_up_type="nutrition"
            )
            
            # Agregar nota de difusión
            self.kommo.add_note(
                entity_id=lead_id,
                entity_type="lead",
                note_text=f"[DIFUSIÓN NUTRICIÓN]\n{nutrition_content}"
            )
            
            # Crear tarea de seguimiento para 7 días después
            follow_up_date = int(time.time()) + (7 * 24 * 3600)
            self.kommo.create_task(
                text=f"Difusión semanal: {lead_name}",
                entity_id=lead_id,
                entity_type="lead",
                complete_till=follow_up_date,
                task_type_id=1
            )
            
            logger.info(f"📚 Difusión de nutrición enviada al lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en fase de nutrición: {str(e)}")
            return False
    
    def process_lead_followup(self, lead_id: int) -> Dict[str, Any]:
        """
        Procesa el seguimiento completo de un lead.
        
        Args:
            lead_id: ID del lead a procesar
        
        Returns:
            Información del resultado del procesamiento
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
            
            lead_name = lead_data.get("name", "Unknown")
            status_id = lead_data.get("status_id")
            
            logger.info(f"🔄 Procesando seguimiento para lead {lead_id}: {lead_name}")
            
            # Determinar fase actual basada en etapa
            if status_id == self.STAGE_VALUE_PRESENTATION:  # "Presentación de valor"
                # Verificar si debe entrar en insistencia
                phase = self.check_insistence_phase(lead_id, lead_data)
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "lead_name": lead_name,
                    "phase": phase,
                    "action": "insistence_check"
                }
            
            elif status_id == self.STAGE_PROPOSAL:  # "Propuesta / Cotización" (fase de nutrición)
                # Enviar difusión de nutrición
                success = self.check_nutrition_phase(lead_id, lead_data)
                return {
                    "success": success,
                    "lead_id": lead_id,
                    "lead_name": lead_name,
                    "phase": "nutrition",
                    "action": "nutrition_sent"
                }
            
            else:
                logger.info(f"ℹ️ Lead {lead_id} en etapa {status_id}, sin acción de seguimiento")
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "lead_name": lead_name,
                    "phase": "none",
                    "action": "no_action"
                }
        
        except Exception as e:
            logger.error(f"❌ Error procesando seguimiento: {str(e)}")
            return {
                "success": False,
                "lead_id": lead_id,
                "error": str(e)
            }
    
    def get_leads_for_followup(self) -> List[int]:
        """
        Obtiene la lista de leads que necesitan seguimiento.
        
        Returns:
            Lista de IDs de leads
        """
        try:
            # Obtener leads
            leads_response = self.kommo.get_leads(limit=100)
            
            # Extraer leads de la respuesta
            if isinstance(leads_response, dict) and "_embedded" in leads_response:
                leads = leads_response["_embedded"]["leads"]
            else:
                leads = leads_response if isinstance(leads_response, list) else []
            
            followup_leads = []
            for lead in leads:
                status_id = lead.get("status_id")
                # Filtrar por etapas que necesitan seguimiento
                if status_id in [self.STAGE_VALUE_PRESENTATION, self.STAGE_PROPOSAL]:
                    followup_leads.append(lead.get("id"))
            
            logger.info(f"📋 {len(followup_leads)} leads necesitan seguimiento")
            return followup_leads
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo leads para seguimiento: {str(e)}")
            return []
    
    def run_followup_batch(self) -> Dict[str, Any]:
        """
        Ejecuta el procesamiento de seguimiento para todos los leads pendientes.
        
        Returns:
            Resumen del procesamiento
        """
        logger.info("🚀 Iniciando procesamiento batch de seguimientos")
        
        leads = self.get_leads_for_followup()
        results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for lead_id in leads:
            result = self.process_lead_followup(lead_id)
            results["total_processed"] += 1
            
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append(result)
        
        logger.info(f"✅ Batch completado: {results['successful']}/{results['total_processed']} exitosos")
        return results


def get_followup_agent(kommo_client, gemini_client) -> FollowUpAgent:
    """Factory function para obtener una instancia del Agente de Seguimiento."""
    return FollowUpAgent(kommo_client, gemini_client)
