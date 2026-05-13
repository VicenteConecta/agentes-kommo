"""
Agente Calificador de Leads.
Recibe leads de Meta Ads y los cualifica mediante preguntas progresivas.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from clients.kommo_client import KommoClient
from clients.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class QualifierAgent:
    """Agente responsable de calificar leads de forma progresiva."""
    
    # Campos personalizados en Kommo (estos IDs deben validarse en tu cuenta)
    CUSTOM_FIELD_IDS = {
        "product_interest": 1,  # Ajusta según tu Kommo
        "business_stage": 2,
        "business_strategy": 3,
        "location": 4,
        "qualification_score": 5,
        "qualification_status": 6,
    }
    
    # Etiquetas para asignar según producto
    PRODUCT_TAGS = {
        "lavacabezas": "Lavacabezas",
        "sillas": "Sillas",
        "sillones": "Sillones de Barbero",
        "camillas": "Camillas",
    }
    
    # Pipeline y etapas (estos IDs deben validarse)
    PIPELINE_ID = 1
    STAGE_QUALIFICATION = 1
    STAGE_PRESENTATION = 2
    
    def __init__(self, kommo_client: KommoClient, gemini_client: GeminiClient):
        """
        Inicializa el agente calificador.
        
        Args:
            kommo_client: Cliente de Kommo
            gemini_client: Cliente de Gemini
        """
        self.kommo = kommo_client
        self.gemini = gemini_client
        self.qualification_threshold = 0.7  # Confianza mínima para considerar cualificado
    
    async def process_new_lead(self, lead_id: int, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un nuevo lead que entra al sistema.
        
        Args:
            lead_id: ID del lead en Kommo
            lead_data: Datos del lead
        
        Returns:
            Resultado del procesamiento
        """
        logger.info(f"Procesando nuevo lead: {lead_id}")
        
        try:
            # 1. Obtener información completa del lead
            lead = self.kommo.get_lead(lead_id)
            logger.info(f"Lead obtenido: {lead}")
            
            # 2. Inicializar contexto de calificación
            qualification_context = {
                "lead_id": lead_id,
                "lead_name": lead.get("name", "Sin nombre"),
                "lead_phone": lead.get("phone", ""),
                "lead_email": lead.get("email", ""),
                "created_at": datetime.now().isoformat(),
                "questions_asked": [],
                "answers": {},
                "qualification_data": {}
            }
            
            # 3. Generar primera pregunta de calificación
            first_question = self.gemini.generate_qualification_question(
                lead_data=lead,
                asked_questions=[]
            )
            
            logger.info(f"Primera pregunta generada: {first_question}")
            
            # 4. Guardar contexto como nota en el lead
            self._save_qualification_context(lead_id, qualification_context)
            
            # 5. Enviar primer mensaje (si hay contacto disponible)
            await self._send_qualification_message(lead_id, first_question)
            
            # 6. Crear tarea de seguimiento
            self._create_follow_up_task(lead_id, "Calificación en progreso")
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "action": "qualification_started",
                "first_question": first_question
            }
        
        except Exception as e:
            logger.error(f"Error procesando lead {lead_id}: {e}")
            return {
                "status": "error",
                "lead_id": lead_id,
                "error": str(e)
            }
    
    async def process_lead_response(self, lead_id: int, message_text: str) -> Dict[str, Any]:
        """
        Procesa una respuesta del lead a una pregunta de calificación.
        
        Args:
            lead_id: ID del lead
            message_text: Respuesta del lead
        
        Returns:
            Resultado del procesamiento
        """
        logger.info(f"Procesando respuesta del lead {lead_id}: {message_text}")
        
        try:
            # 1. Obtener contexto de calificación actual
            qualification_context = self._get_qualification_context(lead_id)
            
            if not qualification_context:
                logger.warning(f"No hay contexto de calificación para lead {lead_id}")
                return {"status": "error", "message": "No hay contexto de calificación"}
            
            # 2. Registrar la respuesta
            qualification_context["answers"][f"question_{len(qualification_context['questions_asked'])}"] = message_text
            
            # 3. Analizar respuesta con Gemini
            lead = self.kommo.get_lead(lead_id)
            analysis = self.gemini.analyze_lead_qualification(
                lead_data=lead,
                conversation_history=qualification_context["answers"]
            )
            
            logger.info(f"Análisis de Gemini: {analysis}")
            
            # 4. Actualizar contexto con análisis
            qualification_context["qualification_data"].update(analysis)
            
            # 5. Verificar si la calificación es suficiente
            confidence = analysis.get("confidence", 0)
            
            if confidence >= self.qualification_threshold:
                # Calificación completa
                return await self._complete_qualification(lead_id, qualification_context, analysis)
            else:
                # Necesita más información
                return await self._continue_qualification(lead_id, qualification_context, analysis)
        
        except Exception as e:
            logger.error(f"Error procesando respuesta de lead {lead_id}: {e}")
            return {
                "status": "error",
                "lead_id": lead_id,
                "error": str(e)
            }
    
    async def _complete_qualification(self, lead_id: int, context: Dict[str, Any], 
                                     analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completa la calificación del lead.
        
        Args:
            lead_id: ID del lead
            context: Contexto de calificación
            analysis: Análisis de Gemini
        
        Returns:
            Resultado de la calificación
        """
        logger.info(f"Completando calificación del lead {lead_id}")
        
        try:
            # 1. Actualizar campos personalizados en Kommo
            custom_fields = {
                self.CUSTOM_FIELD_IDS["product_interest"]: analysis.get("product_interest", ""),
                self.CUSTOM_FIELD_IDS["business_stage"]: analysis.get("business_stage", ""),
                self.CUSTOM_FIELD_IDS["business_strategy"]: analysis.get("business_strategy", ""),
                self.CUSTOM_FIELD_IDS["location"]: analysis.get("location", ""),
                self.CUSTOM_FIELD_IDS["qualification_score"]: str(analysis.get("confidence", 0)),
                self.CUSTOM_FIELD_IDS["qualification_status"]: "Cualificado",
            }
            
            self.kommo.update_lead_custom_fields(lead_id, custom_fields)
            logger.info(f"Campos personalizados actualizados para lead {lead_id}")
            
            # 2. Asignar etiqueta según producto
            product = analysis.get("product_interest", "").lower()
            tag_name = self.PRODUCT_TAGS.get(product, "Cualificado")
            
            # Obtener o crear etiqueta
            tags = self.kommo.get_tags()
            tag_id = None
            
            for tag in tags.get("_embedded", {}).get("tags", []):
                if tag.get("name") == tag_name:
                    tag_id = tag.get("id")
                    break
            
            if not tag_id:
                # Crear etiqueta si no existe
                new_tag = self.kommo.create_tag(tag_name)
                tag_id = new_tag.get("_embedded", {}).get("tags", [{}])[0].get("id")
            
            if tag_id:
                self.kommo.add_tags_to_lead(lead_id, [tag_id])
                logger.info(f"Etiqueta '{tag_name}' asignada al lead {lead_id}")
            
            # 3. Cambiar etapa a "Cualificación"
            self.kommo.update_lead(lead_id, status_id=self.STAGE_QUALIFICATION)
            logger.info(f"Etapa del lead {lead_id} cambiada a 'Cualificación'")
            
            # 4. Agregar nota con resumen de calificación
            summary = f"""
Calificación Completada:
- Producto: {analysis.get('product_interest', 'N/A')}
- Etapa del Negocio: {analysis.get('business_stage', 'N/A')}
- Estrategia: {analysis.get('business_strategy', 'N/A')}
- Ubicación: {analysis.get('location', 'N/A')}
- Confianza: {analysis.get('confidence', 0):.0%}
"""
            self.kommo.add_note(lead_id, "lead", summary)
            
            # 5. Guardar contexto actualizado
            self._save_qualification_context(lead_id, context)
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "action": "qualification_completed",
                "qualification_data": analysis
            }
        
        except Exception as e:
            logger.error(f"Error completando calificación del lead {lead_id}: {e}")
            raise
    
    async def _continue_qualification(self, lead_id: int, context: Dict[str, Any],
                                     analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Continúa el proceso de calificación con una nueva pregunta.
        
        Args:
            lead_id: ID del lead
            context: Contexto de calificación
            analysis: Análisis de Gemini
        
        Returns:
            Resultado del procesamiento
        """
        logger.info(f"Continuando calificación del lead {lead_id}")
        
        try:
            # 1. Generar siguiente pregunta
            next_question = analysis.get("next_question", "")
            
            if not next_question:
                next_question = self.gemini.generate_qualification_question(
                    lead_data=self.kommo.get_lead(lead_id),
                    asked_questions=context["questions_asked"]
                )
            
            # 2. Registrar pregunta
            context["questions_asked"].append(next_question)
            
            # 3. Enviar siguiente pregunta
            await self._send_qualification_message(lead_id, next_question)
            
            # 4. Guardar contexto actualizado
            self._save_qualification_context(lead_id, context)
            
            return {
                "status": "success",
                "lead_id": lead_id,
                "action": "qualification_continued",
                "next_question": next_question,
                "confidence": analysis.get("confidence", 0)
            }
        
        except Exception as e:
            logger.error(f"Error continuando calificación del lead {lead_id}: {e}")
            raise
    
    async def _send_qualification_message(self, lead_id: int, message: str) -> None:
        """
        Envía un mensaje de calificación al lead.
        
        Args:
            lead_id: ID del lead
            message: Contenido del mensaje
        """
        try:
            # Obtener contactos del lead
            lead = self.kommo.get_lead(lead_id)
            
            # Intentar obtener chats
            # Nota: Esto requiere que el lead esté vinculado a un contacto
            # Por ahora, registramos la intención en una nota
            self.kommo.add_note(lead_id, "lead", f"Mensaje de calificación: {message}")
            logger.info(f"Mensaje de calificación registrado para lead {lead_id}")
        
        except Exception as e:
            logger.error(f"Error enviando mensaje de calificación: {e}")
            # No lanzar excepción, solo registrar
    
    def _create_follow_up_task(self, lead_id: int, description: str) -> None:
        """
        Crea una tarea de seguimiento para el lead.
        
        Args:
            lead_id: ID del lead
            description: Descripción de la tarea
        """
        try:
            complete_till = (datetime.now() + timedelta(days=1)).isoformat()
            self.kommo.create_task(
                text=description,
                entity_id=lead_id,
                entity_type="lead",
                complete_till=complete_till
            )
            logger.info(f"Tarea de seguimiento creada para lead {lead_id}")
        except Exception as e:
            logger.error(f"Error creando tarea de seguimiento: {e}")
    
    def _save_qualification_context(self, lead_id: int, context: Dict[str, Any]) -> None:
        """
        Guarda el contexto de calificación como nota en el lead.
        
        Args:
            lead_id: ID del lead
            context: Contexto de calificación
        """
        try:
            context_json = json.dumps(context, indent=2, ensure_ascii=False)
            self.kommo.add_note(lead_id, "lead", f"[CONTEXTO_CALIFICACION]\n{context_json}")
        except Exception as e:
            logger.error(f"Error guardando contexto de calificación: {e}")
    
    def _get_qualification_context(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el contexto de calificación guardado en el lead.
        
        Args:
            lead_id: ID del lead
        
        Returns:
            Contexto de calificación o None
        """
        # Nota: Esta es una implementación simplificada.
        # En producción, deberías usar una base de datos para almacenar contextos.
        try:
            lead = self.kommo.get_lead(lead_id)
            # Buscar en notas del lead
            # Por ahora, retornamos un contexto vacío
            return {
                "lead_id": lead_id,
                "questions_asked": [],
                "answers": {},
                "qualification_data": {}
            }
        except Exception as e:
            logger.error(f"Error obteniendo contexto de calificación: {e}")
            return None
