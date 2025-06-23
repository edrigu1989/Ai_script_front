# app/api/scripts.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.core.security import get_current_user
from app.core.database import get_db
from app.models.script import ScriptGeneration, Script, ScriptRegenerateRequest
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from typing import List
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/generate", response_model=Script)
async def generate_script(
    request: ScriptGeneration,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Generate a new script with AI"""
    try:
        # Verificar límites del plan
        user_profile = db.table("profiles").select("subscription_plan").eq("id", str(current_user.id)).single().execute()
        
        if user_profile.data["subscription_plan"] == "free":
            # Verificar límite de scripts del mes
            scripts_count = db.table("scripts")\
                .select("id", count="exact")\
                .eq("user_id", str(current_user.id))\
                .gte("created_at", datetime.now().replace(day=1).isoformat())\
                .execute()
            
            if scripts_count.count >= 5:
                raise HTTPException(
                    status_code=403,
                    detail="Free plan limit reached. Upgrade to Creator plan for unlimited scripts."
                )
        
        # Obtener historial de scripts para evitar repetición
        similar_scripts = await get_similar_scripts(
            user_id=str(current_user.id),
            idea=request.idea,
            db=db,
            limit=3
        )
        
        # Generar script con LLM
        llm_service = LLMService()
        generated_script = await llm_service.generate_script(
            idea=request.idea,
            tone=request.tone,
            duration=request.duration,
            platform=request.platform,
            additional_context=request.additional_context,
            previous_scripts=similar_scripts,
            user_style=user_profile.data.get("content_style"),
            target_audience=user_profile.data.get("target_audience")
        )
        
        # Generar embedding del script
        embedding_service = EmbeddingService()
        embedding = await embedding_service.generate_embedding(generated_script["content"])
        
        # Guardar en la base de datos
        script_data = {
            "id": str(uuid.uuid4()),
            "user_id": str(current_user.id),
            "title": generated_script["title"],
            "content": generated_script["content"],
            "hook": generated_script["hook"],
            "call_to_action": generated_script["call_to_action"],
            "tone": request.tone,
            "duration": request.duration,
            "platform": request.platform,
            "metadata": {
                "idea": request.idea,
                "additional_context": request.additional_context,
                "generated_by": "claude-3-opus"
            },
            "embedding": embedding,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        response = db.table("scripts").insert(script_data).execute()
        
        return Script(**response.data[0])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Script])
async def get_scripts(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user's scripts"""
    response = db.table("scripts")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .order("created_at", desc=True)\
        .range(skip, skip + limit - 1)\
        .execute()
    
    return [Script(**script) for script in response.data]

@router.get("/{script_id}", response_model=Script)
async def get_script(
    script_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get a specific script"""
    response = db.table("scripts")\
        .select("*")\
        .eq("id", str(script_id))\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return Script(**response.data)

@router.post("/{script_id}/regenerate", response_model=Script)
async def regenerate_script_element(
    script_id: uuid.UUID,
    request: ScriptRegenerateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Regenerate a specific element of the script"""
    # Obtener script original
    script_response = db.table("scripts")\
        .select("*")\
        .eq("id", str(script_id))\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()
    
    if not script_response.data:
        raise HTTPException(status_code=404, detail="Script not found")
    
    script = script_response.data
    
    # Regenerar elemento específico
    llm_service = LLMService()
    
    if request.element == "hook":
        new_content = await llm_service.regenerate_hook(
            current_script=script["content"],
            current_hook=script["hook"],
            additional_instructions=request.additional_instructions
        )
        script["hook"] = new_content
        
    elif request.element == "cta":
        new_content = await llm_service.regenerate_cta(
            current_script=script["content"],
            current_cta=script["call_to_action"],
            additional_instructions=request.additional_instructions
        )
        script["call_to_action"] = new_content
        
    elif request.element == "full":
        # Regenerar todo el script
        new_script = await llm_service.generate_script(
            idea=script["metadata"]["idea"],
            tone=script["tone"],
            duration=script["duration"],
            platform=script["platform"],
            additional_context=request.additional_instructions,
            previous_scripts=[script]  # Incluir el actual para evitar repetirlo
        )
        
        script.update({
            "content": new_script["content"],
            "hook": new_script["hook"],
            "call_to_action": new_script["call_to_action"],
            "title": new_script["title"]
        })
    
    # Actualizar en la base de datos
    script["updated_at"] = datetime.now().isoformat()
    
    response = db.table("scripts")\
        .update(script)\
        .eq("id", str(script_id))\
        .execute()
    
    return Script(**response.data[0])

async def get_similar_scripts(user_id: str, idea: str, db, limit: int = 3):
    """Get similar scripts using vector search"""
    embedding_service = EmbeddingService()
    idea_embedding = await embedding_service.generate_embedding(idea)
    
    # Usar pg_vector para búsqueda por similitud
    # Nota: Esto requiere que hayas configurado pg_vector en Supabase
    response = db.rpc(
        'match_scripts',
        {
            'query_embedding': idea_embedding,
            'match_threshold': 0.7,
            'match_count': limit,
            'user_id': user_id
        }
    ).execute()
    
    return response.data if response.data else []

# app/services/llm_service.py
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage
from app.core.config import settings
from typing import Dict, List, Optional, Literal
import json

class LLMService:
    def __init__(self):
        # Alias para modelos
        self.models = {
            "BEST_CREATIVE": ChatAnthropic(
                model="claude-3-opus-20240229",
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.7
            ),
            "FAST_AND_CHEAP": ChatAnthropic(
                model="claude-3-haiku-20240307",
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
                temperature=0.5
            ),
            "BALANCED": ChatOpenAI(
                model="gpt-4-turbo-preview",
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.6
            )
        }
    
    async def generate_script(
        self,
        idea: str,
        tone: str,
        duration: str,
        platform: str,
        additional_context: Optional[str] = None,
        previous_scripts: List[Dict] = None,
        user_style: Optional[str] = None,
        target_audience: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate a complete script using the BEST_CREATIVE model"""
        
        # Construir el Master Prompt
        system_prompt = self._build_master_prompt(
            tone=tone,
            duration=duration,
            platform=platform,
            user_style=user_style,
            target_audience=target_audience
        )
        
        # Construir el contexto de scripts previos
        context = f"Idea principal: {idea}\n"
        if additional_context:
            context += f"Contexto adicional: {additional_context}\n"
        
        if previous_scripts:
            context += "\n### Scripts similares previos (EVITAR repetir estos enfoques):\n"
            for i, script in enumerate(previous_scripts[:3], 1):
                context += f"\n{i}. Hook anterior: {script.get('hook', 'N/A')}\n"
                context += f"   Resumen: {script.get('content', '')[:200]}...\n"
        
        # Llamar al modelo
        model = self.models["BEST_CREATIVE"]
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await model.ainvoke(messages)
        
        # Parsear la respuesta
        return self._parse_script_response(response.content)
    
    async def regenerate_hook(
        self,
        current_script: str,
        current_hook: str,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Regenerate just the hook using FAST_AND_CHEAP model"""
        
        prompt = f"""Genera un nuevo hook completamente diferente para este script.
        
Hook actual (NO repetir este estilo): {current_hook}

Script completo:
{current_script}

{f"Instrucciones adicionales: {additional_instructions}" if additional_instructions else ""}

Genera SOLO el nuevo hook (máximo 2 líneas). Debe ser impactante y diferente al anterior."""
        
        model = self.models["FAST_AND_CHEAP"]
        response = await model.ainvoke([HumanMessage(content=prompt)])
        
        return response.content.strip()
    
    async def regenerate_cta(
        self,
        current_script: str,
        current_cta: str,
        additional_instructions: Optional[str] = None
    ) -> str:
        """Regenerate the call to action"""
        
        prompt = f"""Genera un nuevo call to action para este script.
        
CTA actual: {current_cta}

Script:
{current_script}

{f"Instrucciones adicionales: {additional_instructions}" if additional_instructions else ""}

Genera SOLO el nuevo CTA (máximo 2 líneas). Debe ser claro y motivador."""
        
        model = self.models["FAST_AND_CHEAP"]
        response = await model.ainvoke([HumanMessage(content=prompt)])
        
        return response.content.strip()
    
    def _build_master_prompt(
        self,
        tone: str,
        duration: str,
        platform: str,
        user_style: Optional[str] = None,
        target_audience: Optional[str] = None
    ) -> str:
        """Build the master prompt for script generation"""
        
        return f"""Eres un experto guionista especializado en contenido viral para {platform}.

OBJETIVO: Crear un script cautivador de {duration} con tono {tone}.

{f"Estilo del creador: {user_style}" if user_style else ""}
{f"Audiencia objetivo: {target_audience}" if target_audience else ""}

ESTRUCTURA OBLIGATORIA:
1. **HOOK** (primeras 3 segundos): Debe capturar la atención inmediatamente
2. **DESARROLLO**: Mantener el interés con ritmo dinámico
3. **CLIMAX**: Punto de máximo interés
4. **CTA**: Call to action claro y específico

REGLAS:
- Usar lenguaje conversacional y directo
- Incluir pausas estratégicas [pausa]
- Indicar énfasis con MAYÚSCULAS
- Ser específico, no genérico
- Evitar clichés

FORMATO DE RESPUESTA (JSON):
{{
    "title": "Título descriptivo del script",
    "hook": "Las primeras líneas que capturan atención",
    "content": "Script completo con formato y pausas",
    "call_to_action": "Acción específica para el viewer"
}}"""
    
    def _parse_script_response(self, response: str) -> Dict[str, str]:
        """Parse the LLM response to extract script components"""
        try:
            # Intentar parsear como JSON
            return json.loads(response)
        except:
            # Si falla, extraer manualmente
            lines = response.split('\n')
            
            result = {
                "title": "Script generado",
                "hook": "",
                "content": response,
                "call_to_action": ""
            }
            
            # Buscar patrones en el texto
            for i, line in enumerate(lines):
                if "hook:" in line.lower():
                    result["hook"] = lines[i+1] if i+1 < len(lines) else line
                elif "cta:" in line.lower() or "call to action:" in line.lower():
                    result["call_to_action"] = lines[i+1] if i+1 < len(lines) else line
            
            return result

# app/services/embedding_service.py
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from typing import List
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text"""
        embedding = await self.embeddings.aembed_query(text)
        return embedding
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = await self.embeddings.aembed_documents(texts)
        return embeddings