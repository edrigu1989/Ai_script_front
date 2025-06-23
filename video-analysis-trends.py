# app/api/video_analysis.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from app.core.security import get_current_user
from app.core.database import get_db
from app.services.video_analysis_service import VideoAnalysisService
from typing import List
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/analyze")
async def analyze_video(
    background_tasks: BackgroundTasks,
    video_url: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Start video analysis process"""
    try:
        # Crear entrada en la DB con estado "queued"
        analysis_id = str(uuid.uuid4())
        
        analysis_data = {
            "id": analysis_id,
            "user_id": str(current_user.id),
            "video_url": video_url,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        db.table("video_analyses").insert(analysis_data).execute()
        
        # Iniciar análisis en background
        background_tasks.add_task(
            process_video_analysis,
            analysis_id=analysis_id,
            video_url=video_url,
            user_id=str(current_user.id),
            db=db
        )
        
        return {
            "analysis_id": analysis_id,
            "status": "queued",
            "message": "Video analysis started. Check status endpoint for updates."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{analysis_id}")
async def get_analysis_status(
    analysis_id: uuid.UUID,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get video analysis status and results"""
    response = db.table("video_analyses")\
        .select("*")\
        .eq("id", str(analysis_id))\
        .eq("user_id", str(current_user.id))\
        .single()\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return response.data

@router.get("/analyses")
async def get_user_analyses(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get all video analyses for the current user"""
    response = db.table("video_analyses")\
        .select("*")\
        .eq("user_id", str(current_user.id))\
        .order("created_at", desc=True)\
        .range(skip, skip + limit - 1)\
        .execute()
    
    return response.data

async def process_video_analysis(analysis_id: str, video_url: str, user_id: str, db):
    """Background task to process video analysis"""
    try:
        # Actualizar estado a "processing"
        db.table("video_analyses").update({
            "status": "processing",
            "updated_at": datetime.now().isoformat()
        }).eq("id", analysis_id).execute()
        
        # Realizar análisis
        video_service = VideoAnalysisService()
        results = await video_service.analyze_video(video_url)
        
        # Guardar resultados
        db.table("video_analyses").update({
            "status": "completed",
            "results": results,
            "updated_at": datetime.now().isoformat()
        }).eq("id", analysis_id).execute()
        
    except Exception as e:
        # En caso de error, actualizar estado
        db.table("video_analyses").update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        }).eq("id", analysis_id).execute()

# app/services/video_analysis_service.py
from google.cloud import videointelligence
from app.services.llm_service import LLMService
from app.core.config import settings
import asyncio
from typing import Dict, Any

class VideoAnalysisService:
    def __init__(self):
        self.video_client = videointelligence.VideoIntelligenceServiceClient()
        self.llm_service = LLMService()
    
    async def analyze_video(self, video_url: str) -> Dict[str, Any]:
        """Analyze video using Google Video Intelligence API and LLM"""
        
        # Análisis técnico con Google Video Intelligence
        technical_analysis = await self._analyze_with_google(video_url)
        
        # Análisis cualitativo con LLM
        qualitative_analysis = await self._analyze_with_llm(
            video_url=video_url,
            technical_data=technical_analysis
        )
        
        return {
            "technical": technical_analysis,
            "qualitative": qualitative_analysis,
            "recommendations": self._generate_recommendations(
                technical_analysis,
                qualitative_analysis
            )
        }
    
    async def _analyze_with_google(self, video_url: str) -> Dict[str, Any]:
        """Use Google Video Intelligence API for technical analysis"""
        
        features = [
            videointelligence.Feature.LABEL_DETECTION,
            videointelligence.Feature.SHOT_CHANGE_DETECTION,
            videointelligence.Feature.SPEECH_TRANSCRIPTION,
        ]
        
        config = videointelligence.SpeechTranscriptionConfig(
            language_code="es-ES",
            enable_automatic_punctuation=True,
        )
        
        video_context = videointelligence.VideoContext(
            speech_transcription_config=config,
        )
        
        # Iniciar operación
        operation = self.video_client.annotate_video(
            request={
                "features": features,
                "input_uri": video_url,
                "video_context": video_context,
            }
        )
        
        # Esperar resultados
        result = operation.result(timeout=180)
        
        # Procesar resultados
        labels = []
        for label in result.annotation_results[0].segment_label_annotations:
            labels.append({
                "label": label.entity.description,
                "confidence": label.segments[0].confidence
            })
        
        shots = len(result.annotation_results[0].shot_annotations)
        
        transcript = ""
        if result.annotation_results[0].speech_transcriptions:
            for transcription in result.annotation_results[0].speech_transcriptions:
                for alternative in transcription.alternatives:
                    transcript += alternative.transcript + " "
        
        return {
            "labels": labels[:10],  # Top 10 labels
            "shot_count": shots,
            "transcript": transcript.strip(),
            "duration": result.annotation_results[0].segment.end_time_offset.total_seconds()
        }
    
    async def _analyze_with_llm(
        self, 
        video_url: str, 
        technical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM for qualitative analysis"""
        
        prompt = f"""Analiza este video basándote en los datos técnicos:

Duración: {technical_data['duration']} segundos
Número de cortes: {technical_data['shot_count']}
Etiquetas detectadas: {', '.join([l['label'] for l in technical_data['labels']])}
Transcripción: {technical_data['transcript'][:500]}...

Proporciona un análisis cualitativo considerando:
1. Efectividad del hook inicial
2. Ritmo y estructura narrativa
3. Engagement potencial
4. Puntos fuertes y débiles
5. Score de viralidad (0-100)

Formato JSON:
{{
    "hook_effectiveness": "análisis del hook",
    "narrative_structure": "análisis de la estructura",
    "engagement_potential": "alto/medio/bajo",
    "strengths": ["punto 1", "punto 2"],
    "weaknesses": ["punto 1", "punto 2"],
    "virality_score": 75,
    "summary": "resumen ejecutivo"
}}"""
        
        model = self.llm_service.models["BALANCED"]
        response = await model.ainvoke([{"role": "user", "content": prompt}])
        
        import json
        try:
            return json.loads(response.content)
        except:
            return {"error": "Could not parse LLM response", "raw": response.content}
    
    def _generate_recommendations(
        self,
        technical: Dict[str, Any],
        qualitative: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = []
        
        # Basadas en duración
        if technical['duration'] > 180:
            recommendations.append("Considera acortar el video a menos de 3 minutos para mejor retención")
        
        # Basadas en cortes
        cuts_per_minute = technical['shot_count'] / (technical['duration'] / 60)
        if cuts_per_minute < 10:
            recommendations.append("Aumenta el ritmo con más cortes y transiciones dinámicas")
        
        # Basadas en análisis cualitativo
        if qualitative.get('virality_score', 0) < 70:
            recommendations.append("Refuerza el hook inicial para capturar atención en los primeros 3 segundos")
        
        return recommendations

# app/tasks/trends_radar.py
"""
Script para ejecutar como Cron Job en Railway
Analiza tendencias virales diariamente
"""
import asyncio
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv

from serpapi import GoogleSearch
from langchain_google_genai import ChatGoogleGenerativeAI
from supabase import create_client, Client
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrendsRadar:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.3
        )
        self.serpapi_key = os.getenv("SERPAPI_KEY")
    
    async def fetch_trends(self) -> Dict[str, List[Dict]]:
        """Fetch trends from multiple sources"""
        trends = {
            "youtube": await self._fetch_youtube_trends(),
            "tiktok": await self._fetch_tiktok_trends(),
            "instagram": await self._fetch_instagram_trends(),
            "general": await self._fetch_google_trends()
        }
        return trends
    
    async def _fetch_youtube_trends(self) -> List[Dict]:
        """Fetch YouTube trending topics"""
        params = {
            "q": "trending topics YouTube creators 2025",
            "api_key": self.serpapi_key,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        trends = []
        for result in results.get("organic_results", [])[:10]:
            trends.append({
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "link": result.get("link")
            })
        
        return trends
    
    async def _fetch_tiktok_trends(self) -> List[Dict]:
        """Fetch TikTok trending topics"""
        params = {
            "q": "TikTok viral trends challenges 2025",
            "api_key": self.serpapi_key,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        trends = []
        for result in results.get("organic_results", [])[:10]:
            trends.append({
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "link": result.get("link")
            })
        
        return trends
    
    async def _fetch_instagram_trends(self) -> List[Dict]:
        """Fetch Instagram trending topics"""
        params = {
            "q": "Instagram Reels trends viral content 2025",
            "api_key": self.serpapi_key,
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        trends = []
        for result in results.get("organic_results", [])[:10]:
            trends.append({
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "link": result.get("link")
            })
        
        return trends
    
    async def _fetch_google_trends(self) -> List[Dict]:
        """Fetch general Google trends"""
        params = {
            "q": "viral content trends social media 2025",
            "api_key": self.serpapi_key,
            "tbm": "nws",  # News
            "num": 20
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        trends = []
        for result in results.get("news_results", [])[:10]:
            trends.append({
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "date": result.get("date"),
                "source": result.get("source")
            })
        
        return trends
    
    async def analyze_trends(self, trends_data: Dict[str, List[Dict]]) -> Dict:
        """Use LLM to analyze and synthesize trends"""
        
        prompt = f"""Analiza las siguientes tendencias virales de hoy y genera insights accionables para creadores de contenido:

{self._format_trends_for_prompt(trends_data)}

Genera un análisis en formato JSON con:
{{
    "top_trends": [
        {{
            "trend": "nombre de la tendencia",
            "platform": "youtube/tiktok/instagram/all",
            "description": "descripción breve",
            "content_ideas": ["idea 1", "idea 2", "idea 3"],
            "urgency": "high/medium/low"
        }}
    ],
    "insights": [
        "insight clave 1",
        "insight clave 2"
    ],
    "opportunities": [
        {{
            "opportunity": "descripción",
            "action": "qué hacer",
            "expected_impact": "alto/medio/bajo"
        }}
    ],
    "summary": "resumen ejecutivo de 2-3 líneas"
}}"""
        
        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        
        import json
        try:
            return json.loads(response.content)
        except:
            logger.error(f"Failed to parse LLM response: {response.content}")
            return {
                "error": "Failed to analyze trends",
                "raw_response": response.content
            }
    
    def _format_trends_for_prompt(self, trends_data: Dict) -> str:
        """Format trends data for LLM prompt"""
        formatted = ""
        
        for platform, trends in trends_data.items():
            formatted += f"\n### {platform.upper()} TRENDS:\n"
            for i, trend in enumerate(trends[:5], 1):
                formatted += f"{i}. {trend.get('title', 'N/A')}\n"
                formatted += f"   {trend.get('snippet', 'N/A')}\n\n"
        
        return formatted
    
    async def save_analysis(self, analysis: Dict):
        """Save analysis to Supabase"""
        
        data = {
            "date": datetime.now().isoformat(),
            "analysis": analysis,
            "status": "completed"
        }
        
        # Insertar nuevo análisis
        self.supabase.table("trends").insert(data).execute()
        
        # Mantener solo los últimos 30 días
        cutoff_date = datetime.now().replace(day=1).isoformat()
        self.supabase.table("trends")\
            .delete()\
            .lt("date", cutoff_date)\
            .execute()
        
        logger.info(f"Trends analysis saved for {data['date']}")
    
    async def run(self):
        """Main execution function"""
        try:
            logger.info("Starting trends radar analysis...")
            
            # Fetch trends
            trends_data = await self.fetch_trends()
            logger.info(f"Fetched trends from {len(trends_data)} platforms")
            
            # Analyze with LLM
            analysis = await self.analyze_trends(trends_data)
            logger.info("Completed LLM analysis")
            
            # Save to database
            await self.save_analysis(analysis)
            
            logger.info("Trends radar completed successfully")
            
        except Exception as e:
            logger.error(f"Error in trends radar: {str(e)}")
            
            # Save error state
            error_data = {
                "date": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            }
            self.supabase.table("trends").insert(error_data).execute()

async def main():
    """Entry point for Railway cron job"""
    radar = TrendsRadar()
    await radar.run()

if __name__ == "__main__":
    asyncio.run(main())