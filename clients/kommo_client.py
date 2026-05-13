"""
Cliente para interactuar con la API de Kommo.
"""
import requests
import logging
from typing import Dict, Any, List, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

class KommoClient:
    """Cliente para la API de Kommo v4."""
    
    def __init__(self, token: str, subdomain: str):
        """
        Inicializa el cliente de Kommo.
        
        Args:
            token: Token de acceso de larga duración
            subdomain: Subdominio de la cuenta Kommo
        """
        self.token = token
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.kommo.com/api/v4"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Realiza una solicitud a la API de Kommo.
        
        Args:
            method: Método HTTP (GET, POST, PATCH, DELETE)
            endpoint: Endpoint de la API (sin la URL base)
            **kwargs: Argumentos adicionales para requests
        
        Returns:
            Respuesta JSON de la API
        
        Raises:
            requests.exceptions.RequestException: Si la solicitud falla
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error en solicitud a Kommo: {e}")
            raise
    
    # ============ Account Methods ============
    
    def get_account_info(self) -> Dict[str, Any]:
        """Obtiene información de la cuenta."""
        return self._make_request("GET", "account")
    
    # ============ Leads Methods ============
    
    def get_leads(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        Obtiene lista de leads.
        
        Args:
            limit: Número máximo de leads a retornar
            offset: Offset para paginación
        
        Returns:
            Lista de leads
        """
        return self._make_request("GET", f"leads?limit={limit}&offset={offset}")
    
    def get_lead(self, lead_id: int) -> Dict[str, Any]:
        """Obtiene un lead específico por ID."""
        return self._make_request("GET", f"leads/{lead_id}")
    
    def create_lead(self, name: str, phone: Optional[str] = None, 
                   email: Optional[str] = None, **custom_fields) -> Dict[str, Any]:
        """
        Crea un nuevo lead.
        
        Args:
            name: Nombre del lead
            phone: Teléfono (opcional)
            email: Email (opcional)
            **custom_fields: Campos personalizados adicionales
        
        Returns:
            Datos del lead creado
        """
        payload = {
            "add": [
                {
                    "name": name,
                    "custom_fields_values": []
                }
            ]
        }
        
        # Agregar teléfono si está disponible
        if phone:
            payload["add"][0]["custom_fields_values"].append({
                "field_id": 1,  # ID del campo de teléfono
                "values": [{"value": phone}]
            })
        
        return self._make_request("POST", "leads", json=payload)
    
    def update_lead(self, lead_id: int, **updates) -> Dict[str, Any]:
        """
        Actualiza un lead existente.
        
        Args:
            lead_id: ID del lead
            **updates: Campos a actualizar (name, status_id, etc.)
        
        Returns:
            Datos del lead actualizado
        """
        payload = {
            "update": [
                {
                    "id": lead_id,
                    **updates
                }
            ]
        }
        return self._make_request("PATCH", "leads", json=payload)
    
    def update_lead_custom_fields(self, lead_id: int, 
                                 custom_fields: Dict[int, str]) -> Dict[str, Any]:
        """
        Actualiza campos personalizados de un lead.
        
        Args:
            lead_id: ID del lead
            custom_fields: Diccionario {field_id: value}
        
        Returns:
            Datos del lead actualizado
        """
        custom_fields_values = [
            {
                "field_id": field_id,
                "values": [{"value": value}]
            }
            for field_id, value in custom_fields.items()
        ]
        
        payload = {
            "update": [
                {
                    "id": lead_id,
                    "custom_fields_values": custom_fields_values
                }
            ]
        }
        return self._make_request("PATCH", "leads", json=payload)
    
    # ============ Tags Methods ============
    
    def get_tags(self) -> Dict[str, Any]:
        """Obtiene lista de etiquetas."""
        return self._make_request("GET", "tags")
    
    def create_tag(self, name: str, color: str = "#0052CC") -> Dict[str, Any]:
        """
        Crea una nueva etiqueta.
        
        Args:
            name: Nombre de la etiqueta
            color: Color hexadecimal de la etiqueta
        
        Returns:
            Datos de la etiqueta creada
        """
        payload = {
            "add": [
                {
                    "name": name,
                    "color": color
                }
            ]
        }
        return self._make_request("POST", "tags", json=payload)
    
    def add_tags_to_lead(self, lead_id: int, tag_ids: List[int]) -> Dict[str, Any]:
        """
        Agrega etiquetas a un lead.
        
        Args:
            lead_id: ID del lead
            tag_ids: Lista de IDs de etiquetas
        
        Returns:
            Respuesta de la API
        """
        payload = {
            "add": [
                {
                    "id": lead_id,
                    "tags": [{"id": tag_id} for tag_id in tag_ids]
                }
            ]
        }
        return self._make_request("PATCH", f"leads/{lead_id}/tags", json=payload)
    
    # ============ Pipelines & Stages Methods ============
    
    def get_pipelines(self) -> Dict[str, Any]:
        """Obtiene lista de pipelines (embudos)."""
        return self._make_request("GET", "leads/pipelines")
    
    def get_pipeline_stages(self, pipeline_id: int) -> Dict[str, Any]:
        """Obtiene etapas de un pipeline."""
        return self._make_request("GET", f"leads/pipelines/{pipeline_id}/stages")
    
    # ============ Chats Methods ============
    
    def get_chats(self, contact_id: int) -> Dict[str, Any]:
        """Obtiene conversaciones de un contacto."""
        return self._make_request("GET", f"contacts/{contact_id}/chats")
    
    def send_message(self, chat_id: int, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje a través de la API de Chats.
        
        Args:
            chat_id: ID del chat
            message: Contenido del mensaje
        
        Returns:
            Respuesta de la API
        """
        payload = {
            "add": [
                {
                    "chat_id": chat_id,
                    "message": message,
                    "type": "text"
                }
            ]
        }
        return self._make_request("POST", "chats/messages", json=payload)
    
    # ============ Tasks Methods ============
    
    def create_task(self, text: str, entity_id: int, entity_type: str = "lead",
                   responsible_user_id: Optional[int] = None,
                   complete_till: Optional[int] = None,
                   task_type_id: int = 1) -> Dict[str, Any]:
        """
        Crea una tarea.
        
        Args:
            text: Descripción de la tarea
            entity_id: ID de la entidad (lead, contacto, etc.)
            entity_type: Tipo de entidad (lead, contact, company)
            responsible_user_id: ID del usuario responsable (opcional)
            complete_till: Fecha límite en formato timestamp Unix (opcional)
            task_type_id: Tipo de tarea (por defecto 1)
        
        Returns:
            Datos de la tarea creada
        """
        import time
        
        # Si no se proporciona complete_till, usar 24 horas desde ahora
        if complete_till is None:
            complete_till = int(time.time()) + (24 * 3600)
        
        # Mapear entity_type a la forma correcta
        entity_type_plural = f"{entity_type}s" if not entity_type.endswith('s') else entity_type
        
        payload = [
            {
                "task_type_id": task_type_id,
                "text": text,
                "complete_till": complete_till,
                "entity_id": entity_id,
                "entity_type": entity_type_plural,
                "request_id": f"task_{entity_id}_{int(time.time())}"
            }
        ]
        
        if responsible_user_id:
            payload[0]["responsible_user_id"] = responsible_user_id
        
        return self._make_request("POST", "tasks", json=payload)
    
    # ============ Notes Methods ============
    
    def add_note(self, entity_id: int, entity_type: str, note_text: str) -> Dict[str, Any]:
        """
        Agrega una nota a una entidad.
        
        Args:
            entity_id: ID de la entidad
            entity_type: Tipo de entidad (lead, contact, company)
            note_text: Contenido de la nota
        
        Returns:
            Datos de la nota creada
        """
        # Mapear entity_type a la forma correcta (plural)
        entity_type_plural = f"{entity_type}s" if not entity_type.endswith('s') else entity_type
        
        payload = [
            {
                "entity_id": entity_id,
                "note_type": "common",
                "text": note_text
            }
        ]
        return self._make_request("POST", f"{entity_type_plural}/notes", json=payload)


def get_kommo_client() -> KommoClient:
    """Factory function para obtener una instancia del cliente Kommo."""
    return KommoClient(
        token=settings.KOMMO_LONG_TOKEN,
        subdomain=settings.KOMMO_SUBDOMAIN
    )
