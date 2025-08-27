# 🤖 Legal AI Assistant

**Sistema inteligente de análisis y generación de documentos legales con IA**

Una aplicación completa de inteligencia artificial para el sector legal que combina análisis predictivo de sentencias, búsqueda vectorial de jurisprudencia, y generación automática de documentos legales.

## ⚡ Quick Start

### Opción 1: Solo Backend (API)
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales
python init_db.py
uvicorn main:app --reload
```
API disponible en: `http://localhost:8000/docs`

### Opción 2: Aplicación Completa (Backend + Frontend)
```bash
# 1. Iniciar backend (como arriba)
# 2. Abrir frontend/index.html en tu navegador
# 3. ¡Listo! Interfaz web completa funcionando
```

## 🚀 Características Principales

### 🔍 Análisis Predictivo de Sentencias
- **Modelo híbrido ML**: Combina embeddings legales con clasificación supervisada
- **Predicción de resultados**: Estima el resultado probable de casos legales
- **Explicabilidad (XAI)**: Proporciona fundamentos para las predicciones
- **Casos similares**: Encuentra jurisprudencia relevante automáticamente

### 🔎 Búsqueda Inteligente de Jurisprudencia
- **Búsqueda vectorial**: Utiliza FAISS para búsquedas ultra-rápidas
- **Embeddings legales**: Modelos especializados en lenguaje jurídico
- **Filtros avanzados**: Por tribunal, materia, fecha, similitud
- **Ranking inteligente**: Resultados ordenados por relevancia

### 📄 Generación de Documentos Legales
- **Plantillas inteligentes**: Sistema de plantillas con placeholders
- **IA generativa**: Integración con GPT-4/Claude para mejora de contenido
- **Citaciones automáticas**: Incorpora jurisprudencia relevante
- **Múltiples tipos**: Demandas, contestaciones, recursos, etc.

### 📊 Gestión de Casos
- **Organización por expedientes**: Sistema completo de gestión de casos
- **Documentos asociados**: Vinculación automática de documentos
- **Seguimiento temporal**: Historial completo de cada caso
- **Estadísticas**: Métricas y análisis de cartera

## 🏗️ Arquitectura Técnica

### Backend
- **FastAPI**: API moderna y rápida con documentación automática
- **PostgreSQL**: Base de datos robusta para datos legales
- **Redis**: Cache y sesiones de usuario
- **SQLAlchemy**: ORM para gestión de base de datos

### Machine Learning
- **Sentence Transformers**: Embeddings especializados en texto legal
- **FAISS**: Índice vectorial para búsquedas ultra-rápidas
- **Scikit-learn**: Clasificación supervisada de resultados legales
- **NLTK/Spacy**: Procesamiento de lenguaje natural

### IA Generativa
- **OpenAI GPT-4**: Generación y mejora de documentos
- **Anthropic Claude**: Alternativa para generación de contenido
- **LangChain**: Framework para aplicaciones de IA

### Integración
- **Google Drive API**: Sincronización automática de datos
- **JWT**: Autenticación segura de usuarios
- **CORS**: Soporte para frontend web

## 📋 Requisitos del Sistema

### Software
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### Hardware Recomendado
- **Desarrollo**: 8GB RAM, 4 cores
- **Producción**: 16GB+ RAM, 8+ cores
- **Almacenamiento**: 50GB+ para modelos ML

## 🛠️ Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd legal-ai-app
```

### 2. Configurar Entorno Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependencias
```bash
cd backend
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:
```env
# JWT
JWT_SECRET=tu-clave-secreta-super-segura

# Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/legal_ai_db

# Redis
REDIS_URL=redis://localhost:6379

# Google Drive API
GOOGLE_DRIVE_CLIENT_ID=tu-client-id
GOOGLE_DRIVE_CLIENT_SECRET=tu-client-secret

# IA Models
OPENAI_API_KEY=tu-openai-key
ANTHROPIC_API_KEY=tu-anthropic-key
```

### 5. Configurar Google Drive API

#### Obtener Credenciales
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API de Google Drive
4. Crea credenciales OAuth 2.0
5. Descarga el archivo `client_secrets.json`

#### Configurar Credenciales
```bash
# Coloca el archivo en el directorio backend/
cp client_secrets.json backend/
```

### 6. Inicializar Base de Datos
```bash
cd backend
python init_db.py
```

### 7. Sincronizar Datos desde Google Drive
```bash
python sync_data.py
```

### 8. Ejecutar la Aplicación
```bash
uvicorn main:app --reload
```

## 🌐 Frontend Integrado

### Características del Frontend
- **Interfaz Moderna**: Diseño responsivo con CSS moderno y JavaScript ES6+
- **Funcionalidades Completas**: Todas las funcionalidades del backend integradas
- **Autenticación**: Sistema completo de login/registro con JWT
- **UX Intuitiva**: Navegación clara y feedback visual para el usuario

### Archivos del Frontend
```
frontend/
├── index.html          # Página principal de la aplicación
├── styles.css          # Estilos CSS con variables y diseño responsivo
├── script.js           # Lógica JavaScript de la aplicación
└── README.md           # Documentación del frontend
```

### Uso del Frontend
1. **Desarrollo Local**: Abrir `frontend/index.html` en tu navegador
2. **Producción**: Subir la carpeta `frontend/` a tu servidor web
3. **Configuración**: Modificar `script.js` para cambiar la URL del backend

### Integración con Backend
- El frontend se comunica automáticamente con el backend a través de la API REST
- Soporte completo para JWT y autenticación
- Manejo de errores y estados de carga
- Notificaciones toast para feedback del usuario

## 🚀 Despliegue en Producción

### Render
1. Conecta tu repositorio GitHub
2. Configura las variables de entorno
3. Selecciona Python como runtime
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Railway
1. Conecta tu repositorio
2. Configura variables de entorno
3. Railway detectará automáticamente Python
4. Deploy automático en cada push

### Variables de Entorno de Producción
```env
DEBUG=False
HOST=0.0.0.0
PORT=8000
JWT_SECRET=clave-super-secreta-de-produccion
DATABASE_URL=postgresql://usuario:password@host:5432/db
REDIS_URL=redis://host:6379
```

## 📚 Uso de la API

### Autenticación
```bash
# Registrar usuario
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"usuario@ejemplo.com","username":"usuario","full_name":"Usuario Ejemplo","password":"password123"}'

# Obtener token
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=usuario&password=password123"
```

### Análisis de Casos
```bash
# Predecir resultado de caso
curl -X POST "http://localhost:8000/api/v1/analysis/predict" \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"case_description":"Caso de estafa...","case_type":"penal"}'
```

### Búsqueda de Jurisprudencia
```bash
# Búsqueda semántica
curl -X GET "http://localhost:8000/api/v1/search/semantic?query=estafa%20penal&limit=10" \
  -H "Authorization: Bearer TU_TOKEN"
```

### Generación de Documentos
```bash
# Generar documento legal
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"case_id":1,"document_type":"demanda","template_name":"Demanda","case_details":{"description":"..."}}'
```

## 🔧 Scripts de Utilidad

### Inicialización de Base de Datos
```bash
python init_db.py
```
- Crea tablas de base de datos
- Establece usuario administrador
- Configura estructura inicial

### Sincronización de Datos
```bash
python sync_data.py
```
- Descarga documentos legales desde Google Drive
- Sincroniza plantillas de documentos
- Entrena modelos de ML
- Actualiza índices de búsqueda

## 📊 Monitoreo y Mantenimiento

### Endpoints de Estado
- `/health` - Estado general de la aplicación
- `/api/v1/analysis/model-status` - Estado de modelos ML
- `/api/v1/search/statistics` - Estadísticas de búsqueda
- `/api/v1/data-sync/sync-status` - Estado de sincronización

### Logs
La aplicación genera logs detallados para:
- Operaciones de sincronización
- Entrenamiento de modelos
- Errores y excepciones
- Rendimiento de búsquedas

## 🧪 Testing

### Testing del Backend
```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest
```

### Testing del Frontend
1. **Abrir en el navegador**: `frontend/index.html`
2. **Verificar funcionalidades**:
   - Navegación entre secciones
   - Formularios de login/registro
   - Formularios de análisis y búsqueda
   - Responsive design en diferentes tamaños de pantalla

### Testing de la Aplicación Completa
1. **Iniciar el backend**: `uvicorn main:app --reload`
2. **Abrir el frontend**: `frontend/index.html`
3. **Probar flujo completo**:
   - Registro de usuario
   - Login
   - Análisis de caso
   - Búsqueda de jurisprudencia
   - Generación de documento
   - Gestión de casos

### Tests Disponibles
- Tests de autenticación
- Tests de análisis de casos
- Tests de búsqueda
- Tests de generación de documentos
- Tests de sincronización

## 🔒 Seguridad

### Autenticación
- JWT tokens con expiración configurable
- Hashing seguro de contraseñas con bcrypt
- Control de acceso basado en roles

### Validación de Datos
- Validación Pydantic para todos los inputs
- Sanitización de texto de entrada
- Protección contra inyección SQL

### HTTPS
- Configuración obligatoria en producción
- Headers de seguridad automáticos
- CORS configurado apropiadamente

## 🤝 Contribución

### Estructura del Proyecto
```
legal-ai-app/
├── backend/                 # Backend FastAPI
│   ├── main.py             # Aplicación principal
│   ├── config.py           # Configuración
│   ├── models/             # Modelos de base de datos
│   ├── services/           # Servicios de negocio
│   ├── routers/            # Endpoints de API
│   ├── ml_models/          # Modelos de machine learning
│   └── requirements.txt    # Dependencias Python
├── frontend/               # Frontend integrado y funcional
│   ├── index.html          # Página principal
│   ├── styles.css          # Estilos CSS
│   ├── script.js           # Lógica JavaScript
│   └── README.md           # Documentación del frontend
├── data/                   # Datos y modelos
├── render.yaml             # Configuración para Render
├── railway.json            # Configuración para Railway
├── Procfile                # Configuración para Heroku
├── Dockerfile              # Configuración Docker (opcional)
└── README.md               # Este archivo
```

### Guías de Contribución
1. Fork el repositorio
2. Crea una rama para tu feature
3. Implementa cambios con tests
4. Envía un Pull Request
5. Espera revisión y merge

## 📞 Soporte

### Documentación
- **API Docs**: Disponible en `/docs` cuando la app esté corriendo
- **ReDoc**: Documentación alternativa en `/redoc`

### Issues
- Reporta bugs en GitHub Issues
- Incluye logs y pasos para reproducir
- Proporciona información del entorno

### Comunidad
- Únete a nuestro Discord/Slack
- Participa en discusiones de GitHub
- Comparte casos de uso y mejoras

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- **FastAPI** por el framework web excepcional
- **Hugging Face** por los modelos de transformers
- **Facebook Research** por FAISS
- **Google** por la API de Drive
- **OpenAI** y **Anthropic** por los modelos de IA

---

**¡Construyamos el futuro del derecho juntos! 🚀⚖️**