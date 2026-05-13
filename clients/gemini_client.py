"""
Cliente para interactuar con la API de Google Gemini.
"""
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from config.settings import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Cliente para la API de Google Gemini."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el cliente de Gemini.
        
        Args:
            api_key: Clave de API de Google Gemini
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
    
    def analyze_lead_qualification(self, lead_data: Dict[str, Any], 
                                  conversation_history: list) -> Dict[str, Any]:
        """
        Analiza la información del lead para determinar su calificación.
        
        Args:
            lead_data: Datos del lead
            conversation_history: Historial de conversación
        
        Returns:
            Análisis de calificación con criterios extraídos
        """
        prompt = f"""
Analiza la siguiente información de un lead y el historial de conversación para extraer los criterios de calificación.

Datos del Lead:
{lead_data}

Historial de Conversación:
{conversation_history}

Por favor, extrae y categoriza:
1. Producto de interés (ej: lavacabezas, sillas, sillones de barbero, camillas)
2. Etapa del negocio (Iniciando, Ampliando, Renovando)
3. Estrategia de negocio (Premium, Alta productividad, Alta rotación)
4. Ubicación (ciudad/región)

Responde en formato JSON con las siguientes claves:
- product_interest: string
- business_stage: string
- business_strategy: string
- location: string
- confidence: float (0-1, qué tan seguro estás de la calificación)
- next_question: string (la siguiente pregunta a hacer si no está completo)
"""
        
        try:
            response = self.model.generate_content(prompt)
            # Parsear la respuesta JSON
            import json
            import re
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                logger.warning("No se pudo extraer JSON de la respuesta de Gemini")
                return {"error": "No se pudo parsear la respuesta"}
        
        except Exception as e:
            logger.error(f"Error al analizar calificación con Gemini: {e}")
            raise
    
    def generate_qualification_question(self, lead_data: Dict[str, Any],
                                       asked_questions: list) -> str:
        """
        Genera la siguiente pregunta de calificación.
        
        Args:
            lead_data: Datos del lead
            asked_questions: Lista de preguntas ya realizadas
        
        Returns:
            Siguiente pregunta a realizar
        """
        prompt = f"""
Eres un agente de ventas profesional para una empresa de equipos de belleza (lavacabezas, sillas, sillones de barbero, camillas).

Datos del Lead:
{lead_data}

Preguntas ya realizadas:
{asked_questions}

Genera la siguiente pregunta de calificación. Debe ser:
- Clara y concisa
- Enfocada en uno de estos criterios (en este orden de prioridad):
  1. Producto de interés
  2. Etapa del negocio
  3. Estrategia de negocio
  4. Ubicación
- Natural y conversacional
- En español

Responde SOLO con la pregunta, sin explicaciones adicionales.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error al generar pregunta de calificación: {e}")
            raise
    
    def analyze_incoming_message(self, message_text: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza un mensaje entrante para detectar intenciones (teléfono, visita, etc.).
        
        Args:
            message_text: Contenido del mensaje
            lead_context: Contexto del lead
        
        Returns:
            Análisis de intención del mensaje
        """
        prompt = f"""
Analiza el siguiente mensaje de un cliente para detectar intenciones urgentes.

Mensaje: "{message_text}"

Contexto del Lead:
{lead_context}

Detecta si el cliente:
1. Proporciona su número de teléfono
2. Solicita una llamada
3. Solicita una visita al showroom
4. Solicita una asesoría
5. Muestra alto interés de compra

Responde en formato JSON con:
- has_phone: boolean
- phone_number: string o null
- requests_call: boolean
- requests_visit: boolean
- requests_consultation: boolean
- high_interest: boolean
- urgency_level: "low" | "medium" | "high"
- summary: string (resumen de lo detectado)
"""
        
        try:
            response = self.model.generate_content(prompt)
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                logger.warning("No se pudo extraer JSON de la respuesta de Gemini")
                return {"error": "No se pudo parsear la respuesta"}
        
        except Exception as e:
            logger.error(f"Error al analizar mensaje con Gemini: {e}")
            raise
    
    def generate_follow_up_message(self, lead_data: Dict[str, Any], 
                                  follow_up_type: str) -> str:
        """
        Genera un mensaje de seguimiento personalizado.
        
        Args:
            lead_data: Datos del lead
            follow_up_type: Tipo de seguimiento (insistence, nutrition, etc.)
        
        Returns:
            Mensaje personalizado
        """
        prompts = {
            "insistence": f"""
Genera un mensaje de seguimiento amable pero persuasivo para un cliente que no ha respondido.
Lead: {lead_data.get('name', 'Cliente')}
Producto de interés: {lead_data.get('product_interest', 'No especificado')}

El mensaje debe:
- Ser breve (máximo 3 líneas)
- Recordar el producto
- Ofrecer ayuda
- Ser en español
- Sonar natural y no invasivo
""",
            "nutrition": f"""
Genera un mensaje educativo/de valor para mantener el interés del cliente.
Lead: {lead_data.get('name', 'Cliente')}
Producto de interés: {lead_data.get('product_interest', 'No especificado')}

El mensaje debe:
- Compartir un tip o consejo útil
- Relacionado al producto
- Ser breve y valioso
- Ser en español
- Incluir una llamada a la acción suave
"""
        }
        
        prompt = prompts.get(follow_up_type, prompts["insistence"])
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error al generar mensaje de seguimiento: {e}")
            raise


def get_gemini_client() -> GeminiClient:
    """Factory function para obtener una instancia del cliente Gemini."""
    return GeminiClient(api_key=settings.GEMINI_API_KEY)
