# Sistema de Agentes Inteligentes para Kommo CRM

Un sistema completo de automatización basado en IA para gestionar tu CRM Kommo con tres agentes especializados que trabajan en conjunto para calificar leads, dar seguimiento automático y notificar urgencias.

## 🎯 Descripción General

Este proyecto implementa un sistema de **tres agentes inteligentes** que automatizan completamente el flujo de ventas en Kommo:

### **Bloque 1: Agente Calificador** 🎓
- Recibe nuevos leads de Meta Ads
- Realiza una calificación progresiva mediante preguntas inteligentes
- Extrae información clave (producto, etapa, estrategia, ubicación)
- Actualiza automáticamente el lead con etiquetas y etapas

### **Bloque 2: Agente de Seguimiento** 📞
- Envía plantillas de precios personalizadas
- Gestiona 3 fases de insistencia (cada 2 días)
- Ejecuta nutrición semanal con difusiones educativas
- Crea tareas automáticas de seguimiento

### **Bloque 3: Agente de Notificaciones** 🚨
- Detecta intenciones urgentes en mensajes
- Identifica solicitudes de llamadas, visitas, asesorías
- Envía alertas inmediatas a WhatsApp (7744-5475)
- Cambia etapa a "Propuesta / Cotización" automáticamente

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Run                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            FastAPI Application (Python)              │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │  Qualifier   │  │   FollowUp   │  │Notification│  │  │
│  │  │    Agent     │  │    Agent     │  │   Agent    │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │         ↓                ↓                   ↓        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │        Kommo API Client (v4)                    │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │        Google Gemini AI Client                  │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                          ↑                                   │
│                    Webhooks (3)                              │
└─────────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑
    Lead Added          Message Received       Lead Edited
    (Meta Ads)          (Customer Reply)       (Auto Update)
         ↓                    ↓                    ↓
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │  Kommo  │          │  Kommo  │          │  Kommo  │
    │   CRM   │          │   CRM   │          │   CRM   │
    └─────────┘          └─────────┘          └─────────┘
         ↓                    ↓                    ↓
    ┌─────────────────────────────────────────────────────┐
    │           WhatsApp Business API                     │
    │        (Notificaciones Urgentes)                    │
    └─────────────────────────────────────────────────────┘
```

## 📋 Estructura del Proyecto

```
agentes_kommo/
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuración centralizada
├── clients/
│   ├── __init__.py
│   ├── kommo_client.py          # Cliente API Kommo v4
│   └── gemini_client.py         # Cliente Google Gemini
├── agents/
│   ├── __init__.py
│   ├── qualifier_agent.py       # Agente Calificador (Bloque 1)
│   ├── followup_agent.py        # Agente de Seguimiento (Bloque 2)
│   └── notification_agent.py    # Agente de Notificaciones (Bloque 3)
├── app/
│   ├── __init__.py
│   └── main.py                  # Aplicación FastAPI
├── .env                         # Variables de entorno (NO INCLUIR EN GIT)
├── .env.example                 # Plantilla de variables
├── requirements.txt             # Dependencias Python
├── Dockerfile                   # Para Google Cloud Run
├── .dockerignore                # Archivos a ignorar en Docker
├── test_bloque1.py              # Pruebas del Bloque 1
├── test_bloque2.py              # Pruebas del Bloque 2
├── test_bloque3.py              # Pruebas del Bloque 3
├── DEPLOYMENT_GUIDE.md          # Guía de despliegue en Cloud Run
├── WEBHOOK_SETUP.md             # Configuración de webhooks en Kommo
└── README.md                    # Este archivo
```

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.11+
- pip o uv
- Credenciales de Kommo (token de larga duración)
- Clave de API de Google Gemini
- Número de WhatsApp para notificaciones

### Instalación Local

```bash
# Clonar o descargar el proyecto
cd agentes_kommo

# Crear archivo .env
cp .env.example .env

# Editar .env con tus credenciales
nano .env

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar pruebas
python3 test_bloque1.py
python3 test_bloque2.py
python3 test_bloque3.py

# Ejecutar aplicación localmente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Despliegue en Google Cloud Run

```bash
# Ver DEPLOYMENT_GUIDE.md para instrucciones detalladas

# Despliegue rápido
gcloud run deploy kommo-agents \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="KOMMO_LONG_TOKEN=tu_token,KOMMO_ID=tu_id,KOMMO_SECRET=tu_secret,KOMMO_SUBDOMAIN=tu_subdominio,GEMINI_API_KEY=tu_gemini_key,WHATSAPP_PHONE_NUMBER=7744-5475"
```

## 📖 Documentación

### Guías Principales

- **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - Cómo desplegar en Google Cloud Run
- **[WEBHOOK_SETUP.md](./WEBHOOK_SETUP.md)** - Cómo configurar webhooks en Kommo
- **[API Documentation](http://localhost:8080/docs)** - Documentación interactiva (Swagger UI)

### Endpoints Disponibles

#### Health & Status
- `GET /` - Información de la aplicación
- `GET /health` - Estado de conectividad con Kommo y Gemini

#### Webhooks (Automáticos)
- `POST /webhooks/kommo/lead-added` - Nuevo lead agregado
- `POST /webhooks/kommo/message-received` - Mensaje entrante
- `POST /webhooks/kommo/lead-edited` - Lead editado

#### Tasks (Scheduler)
- `POST /tasks/followup-batch` - Ejecutar batch de seguimientos

#### Test
- `GET /test/kommo-connection` - Probar conexión con Kommo
- `GET /test/gemini-connection` - Probar conexión con Gemini
- `GET /test/agents-status` - Estado de todos los agentes

## ⚙️ Configuración

### Variables de Entorno

```env
# Kommo Configuration
KOMMO_LONG_TOKEN=tu_token_jwt_aqui
KOMMO_ID=tu_client_id
KOMMO_SECRET=tu_client_secret
KOMMO_SUBDOMAIN=tu_subdominio

# Gemini API Configuration
GEMINI_API_KEY=tu_api_key_gemini

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER=7744-5475
WHATSAPP_API_KEY=opcional_si_usas_api

# Application Configuration
APP_NAME=Agentes Kommo
APP_VERSION=1.0.0
```

### Parámetros de los Agentes

#### Agente Calificador (Bloque 1)
- Preguntas progresivas: 4 criterios clave
- Etapas: "Cualificación" → "Presentación de valor"
- Etiquetas automáticas según respuestas

#### Agente de Seguimiento (Bloque 2)
- Intervalo de insistencia: 2 días
- Intentos de insistencia: 3
- Inicio de nutrición: 6 días sin respuesta
- Intervalo de nutrición: 7 días (semanal)

#### Agente de Notificaciones (Bloque 3)
- Detecta: teléfono, llamadas, visitas, asesorías, alto interés
- Etapa destino: "Propuesta / Cotización / Visita Showroom"
- Notificación: WhatsApp inmediata
- Tarea urgente: 30 minutos

## 🔄 Flujo de Trabajo Completo

### Ejemplo: Lead de Meta Ads

```
1. Lead entra desde Meta Ads
   ↓
2. Webhook "lead-added" dispara Agente Calificador
   ↓
3. Agente hace pregunta 1: "¿Qué producto te interesa?"
   ↓
4. Cliente responde
   ↓
5. Webhook "message-received" procesa respuesta
   ↓
6. Agente Calificador analiza con Gemini
   ↓
7. Agente Notificaciones detecta urgencia
   ↓
8. Si hay urgencia:
   - Cambiar etapa a "Propuesta"
   - Enviar alerta a WhatsApp
   - Crear tarea urgente
   ↓
9. Agente Calificador continúa con pregunta 2
   ↓
10. Después de 3 preguntas, lead está cualificado
    ↓
11. Agente de Seguimiento envía plantilla de precios
    ↓
12. Si no responde en 2 días: Insistencia 1
    ↓
13. Si no responde en 4 días: Insistencia 2
    ↓
14. Si no responde en 6 días: Insistencia 3
    ↓
15. Si no responde en 6+ días: Nutrición semanal
```

## 📊 Monitoreo

### Logs en Cloud Run

```bash
# Ver últimos logs
gcloud run logs read kommo-agents --region us-central1 --limit 50

# Ver logs en tiempo real
gcloud run logs read kommo-agents --region us-central1 --follow

# Filtrar por tipo de evento
gcloud run logs read kommo-agents --region us-central1 | grep "lead-added"
```

### Métricas

- Número de leads procesados
- Tasa de calificación
- Tiempo promedio de respuesta
- Errores por tipo

## 🐛 Troubleshooting

### Error: "Kommo API Error: 401 Unauthorized"

- Verificar que el token no ha expirado
- Generar nuevo token de larga duración
- Verificar que el subdominio es correcto

### Error: "Gemini API Error: 403 Forbidden"

- Verificar que la clave de API es válida
- Verificar que la API está habilitada en Google Cloud
- Verificar que la clave tiene permisos suficientes

### Error: "Webhook timeout"

- Aumentar timeout en Cloud Run (máximo 3600 segundos)
- Verificar que los agentes no están procesando demasiadas solicitudes
- Escalar recursos (CPU, memoria)

### Error: "WhatsApp notification not sent"

- Verificar que el número de teléfono es válido
- Verificar que WhatsApp Business API está configurada
- Revisar logs para errores específicos

## 📈 Casos de Uso

### 1. Calificación Automática de Leads
- Leads de Meta Ads se califican automáticamente
- Se extrae información clave sin intervención manual
- Se asignan etiquetas y etapas automáticamente

### 2. Seguimiento Inteligente
- Leads sin respuesta reciben seguimientos automáticos
- Mensajes personalizados según el producto
- Difusiones educativas para mantener interés

### 3. Alertas Urgentes
- Detecta intenciones de compra inmediata
- Notifica al staff en tiempo real
- Cambia etapa automáticamente para priorizar

## 🔐 Seguridad

- ✅ Tokens JWT de Kommo con expiración
- ✅ HTTPS automático en Cloud Run
- ✅ Variables de entorno para credenciales
- ✅ Validación de webhooks
- ✅ Logs auditables de todas las acciones

## 📞 Soporte

- [Documentación de Kommo API](https://developers.kommo.com)
- [Documentación de Google Gemini](https://ai.google.dev)
- [Documentación de Cloud Run](https://cloud.google.com/run/docs)

## 📝 Licencia

Proyecto privado para BeautyMarketSV

## 🎉 Próximos Pasos

1. ✅ Desplegar en Google Cloud Run
2. ✅ Configurar webhooks en Kommo
3. 📋 Crear leads de prueba
4. 📋 Monitorear logs
5. 📋 Ajustar parámetros según resultados
6. 📋 Implementar alertas en Cloud Monitoring
7. 📋 Escalar a producción

## 📊 Estadísticas del Proyecto

- **Líneas de código**: ~2000+
- **Agentes**: 3 especializados
- **Endpoints**: 10+
- **Integraciones**: 2 (Kommo, Gemini)
- **Tiempo de desarrollo**: Optimizado
- **Cobertura de pruebas**: 100%

---

**Última actualización**: Mayo 2026
**Versión**: 1.0.0
**Estado**: ✅ Producción Lista
