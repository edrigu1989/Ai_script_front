# requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0

# Database
supabase==2.3.0
asyncpg==0.29.0

# AI/ML
langchain==0.1.0
langchain-anthropic==0.0.1
langchain-openai==0.0.2
langchain-google-genai==0.0.1
openai==1.8.0
anthropic==0.8.1
google-generativeai==0.3.2

# Google Cloud
google-cloud-videointelligence==2.11.4

# Stripe
stripe==7.8.0

# Search/Scraping
google-search-results==2.4.2

# Utils
httpx==0.26.0
redis==5.0.1
numpy==1.24.3

# .env.example
# App
APP_NAME="AI Script Strategist"
DEBUG=False

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_CREATOR=price_...

# AI Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...

# Search
SERPAPI_KEY=your-serpapi-key

# Frontend
FRONTEND_URL=http://localhost:3000

# Redis (optional)
REDIS_URL=redis://localhost:6379

# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

# Dockerfile (alternativo para Railway)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml (para desarrollo local)
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    env_file:
      - .env
    volumes:
      - ./app:/app/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

# Makefile
.PHONY: install dev test migrate

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

format:
	black app/
	isort app/

lint:
	flake8 app/
	mypy app/

migrate:
	python scripts/migrate.py

docker-build:
	docker build -t ai-script-strategist .

docker-run:
	docker run -p 8000:8000 --env-file .env ai-script-strategist

# scripts/setup_supabase.sql
-- Enable pg_vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Profiles table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    subscription_plan TEXT DEFAULT 'free' CHECK (subscription_plan IN ('free', 'creator')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'cancelled', 'expired')),
    stripe_customer_id TEXT UNIQUE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    content_style TEXT,
    target_audience TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scripts table
CREATE TABLE IF NOT EXISTS public.scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    hook TEXT NOT NULL,
    call_to_action TEXT NOT NULL,
    tone TEXT NOT NULL,
    duration TEXT NOT NULL,
    platform TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Video analyses table
CREATE TABLE IF NOT EXISTS public.video_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    video_url TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
    results JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trends table
CREATE TABLE IF NOT EXISTS public.trends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date TIMESTAMPTZ NOT NULL,
    analysis JSONB NOT NULL,
    status TEXT DEFAULT 'completed',
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_scripts_user_id ON public.scripts(user_id);
CREATE INDEX idx_scripts_created_at ON public.scripts(created_at DESC);
CREATE INDEX idx_video_analyses_user_id ON public.video_analyses(user_id);
CREATE INDEX idx_video_analyses_status ON public.video_analyses(status);
CREATE INDEX idx_trends_date ON public.trends(date DESC);

-- Vector similarity search function
CREATE OR REPLACE FUNCTION match_scripts(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    user_id uuid
)
RETURNS TABLE (
    id uuid,
    title text,
    content text,
    hook text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id,
        s.title,
        s.content,
        s.hook,
        1 - (s.embedding <=> query_embedding) AS similarity
    FROM scripts s
    WHERE s.user_id = match_scripts.user_id
    AND 1 - (s.embedding <=> query_embedding) > match_threshold
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Trigger to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        new.id,
        new.email,
        new.raw_user_meta_data->>'full_name'
    );
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.video_analyses ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Scripts policies
CREATE POLICY "Users can view own scripts" ON public.scripts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own scripts" ON public.scripts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scripts" ON public.scripts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own scripts" ON public.scripts
    FOR DELETE USING (auth.uid() = user_id);

-- Video analyses policies
CREATE POLICY "Users can view own analyses" ON public.video_analyses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own analyses" ON public.video_analyses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Trends are public read
CREATE POLICY "Anyone can read trends" ON public.trends
    FOR SELECT USING (true);

# scripts/test_api.py
"""
Script para probar los endpoints de la API
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_api():
    async with httpx.AsyncClient() as client:
        # 1. Test signup
        print("1. Testing signup...")
        signup_data = {
            "email": "test@example.com",
            "password": "Test123!",
            "full_name": "Test User"
        }
        response = await client.post(f"{BASE_URL}/auth/signup", json=signup_data)
        print(f"Signup response: {response.status_code}")
        
        # 2. Test login
        print("\n2. Testing login...")
        login_data = {
            "email": "test@example.com",
            "password": "Test123!"
        }
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            token = auth_data["session"]["access_token"]
            user_id = auth_data["user"]["id"]
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 3. Test profile update
            print("\n3. Testing profile update...")
            profile_data = {
                "content_style": "educational",
                "target_audience": "entrepreneurs",
                "onboarding_completed": True
            }
            response = await client.put(
                f"{BASE_URL}/profiles/{user_id}",
                json=profile_data,
                headers=headers
            )
            print(f"Profile update response: {response.status_code}")
            
            # 4. Test script generation
            print("\n4. Testing script generation...")
            script_data = {
                "idea": "How to start a successful online business in 2025",
                "tone": "educational",
                "duration": "60s",
                "platform": "youtube",
                "additional_context": "Focus on AI tools and automation"
            }
            response = await client.post(
                f"{BASE_URL}/scripts/generate",
                json=script_data,
                headers=headers
            )
            print(f"Script generation response: {response.status_code}")
            if response.status_code == 200:
                script = response.json()
                print(f"Generated script ID: {script['id']}")
                print(f"Hook: {script['hook'][:50]}...")
            
            # 5. Test video analysis
            print("\n5. Testing video analysis...")
            video_data = {
                "video_url": "https://example.com/video.mp4"
            }
            response = await client.post(
                f"{BASE_URL}/videos/analyze",
                json=video_data,
                headers=headers
            )
            print(f"Video analysis response: {response.status_code}")
            if response.status_code == 200:
                analysis = response.json()
                print(f"Analysis ID: {analysis['analysis_id']}")
                print(f"Status: {analysis['status']}")

if __name__ == "__main__":
    asyncio.run(test_api())

# README.md
# AI Script Strategist - Backend

Plataforma de generación de scripts para contenido viral usando IA.

## 🚀 Setup Rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/ai-script-strategist.git
cd ai-script-strategist
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Configurar Supabase
1. Crear proyecto en [Supabase](https://supabase.com)
2. Ejecutar el script SQL en `scripts/setup_supabase.sql`
3. Copiar las credenciales al `.env`

### 4. Instalar dependencias
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Ejecutar en desarrollo
```bash
make dev
# o directamente:
uvicorn main:app --reload
```

## 📦 Despliegue en Railway

### 1. Preparar el repositorio
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Configurar en Railway
1. Crear nuevo proyecto en [Railway](https://railway.app)
2. Conectar con GitHub
3. Agregar todas las variables de entorno
4. Deploy automático al hacer push

### 3. Configurar Cron Job para tendencias
En Railway, crear un nuevo servicio:
- Comando: `python app/tasks/trends_radar.py`
- Schedule: `0 9 * * *` (diariamente a las 9 AM)

## 🛠️ Estructura del Proyecto

```
ai-script-strategist/
├── app/
│   ├── api/              # Endpoints FastAPI
│   ├── core/             # Configuración y seguridad
│   ├── models/           # Modelos Pydantic
│   ├── services/         # Lógica de negocio
│   └── tasks/            # Tareas asíncronas
├── scripts/              # Scripts de setup y utilidades
├── tests/                # Tests unitarios
├── main.py               # Punto de entrada
├── requirements.txt      # Dependencias
└── railway.toml          # Configuración Railway
```

## 🔑 APIs Necesarias

1. **Supabase**: Base de datos y autenticación
2. **Stripe**: Procesamiento de pagos
3. **Anthropic**: Claude para generación de scripts
4. **OpenAI**: Embeddings y modelos auxiliares
5. **Google Cloud**: Video Intelligence API
6. **SerpAPI**: Búsqueda de tendencias

## 📊 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/signup` - Registro de usuarios
- `POST /api/v1/auth/login` - Inicio de sesión
- `POST /api/v1/auth/logout` - Cerrar sesión

### Perfiles
- `GET /api/v1/profiles/{user_id}` - Obtener perfil
- `PUT /api/v1/profiles/{user_id}` - Actualizar perfil

### Scripts
- `POST /api/v1/scripts/generate` - Generar nuevo script
- `GET /api/v1/scripts` - Listar scripts del usuario
- `POST /api/v1/scripts/{id}/regenerate` - Regenerar elementos

### Pagos
- `POST /api/v1/stripe/create-checkout-session` - Iniciar pago
- `POST /api/v1/stripe/webhook` - Webhook de Stripe

### Análisis de Video
- `POST /api/v1/videos/analyze` - Analizar video
- `GET /api/v1/videos/analysis/{id}` - Ver resultado

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Test manual de la API
python scripts/test_api.py
```

## 🔒 Seguridad

- Autenticación JWT con Supabase
- Row Level Security (RLS) en todas las tablas
- Validación de webhooks de Stripe
- Variables de entorno para secretos
- HTTPS obligatorio en producción

## 📈 Monitoreo

Railway proporciona:
- Logs en tiempo real
- Métricas de uso
- Alertas automáticas
- Health checks

## 🤝 Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto es privado y propietario.
            