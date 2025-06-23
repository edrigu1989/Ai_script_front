# main.py
from fastapi import FastAPI, Depends, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.api import auth, profiles, stripe_handler, scripts, video_analysis
from app.core.config import settings
from app.core.database import init_db

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title="AI Script Strategist API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(stripe_handler.router, prefix="/api/v1/stripe", tags=["payments"])
app.include_router(scripts.router, prefix="/api/v1/scripts", tags=["scripts"])
app.include_router(video_analysis.router, prefix="/api/v1/videos", tags=["videos"])

@app.get("/")
async def root():
    return {"message": "AI Script Strategist API", "version": "1.0.0"}

# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Script Strategist"
    DEBUG: bool = False
    
    # Database
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_CREATOR: str
    
    # AI Providers
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Redis (opcional para caché)
    REDIS_URL: str = None
    
    class Config:
        env_file = ".env"

settings = Settings()

# app/core/database.py
from supabase import create_client, Client
from app.core.config import settings
import asyncio
from typing import Optional

class SupabaseDB:
    client: Optional[Client] = None
    
    @classmethod
    async def init(cls):
        cls.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    
    @classmethod
    def get_client(cls) -> Client:
        if not cls.client:
            raise Exception("Database not initialized")
        return cls.client

async def init_db():
    await SupabaseDB.init()

def get_db() -> Client:
    return SupabaseDB.get_client()

# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.database import get_db

security = HTTPBearer()

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    
    # Verificar token con Supabase
    db = get_db()
    try:
        user = db.auth.get_user(token)
        return user.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

# app/models/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    subscription_plan: Literal["free", "creator"] = "free"
    subscription_status: Literal["active", "cancelled", "expired"] = "active"
    stripe_customer_id: Optional[str] = None
    onboarding_completed: bool = False
    content_style: Optional[str] = None
    target_audience: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    content_style: Optional[str] = None
    target_audience: Optional[str] = None
    onboarding_completed: Optional[bool] = None

# app/models/script.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

class ScriptGeneration(BaseModel):
    idea: str = Field(..., min_length=10, max_length=1000)
    tone: Literal["casual", "professional", "humorous", "educational", "dramatic"] = "casual"
    duration: Literal["30s", "60s", "90s", "3min"] = "60s"
    platform: Literal["youtube", "tiktok", "instagram", "linkedin"] = "youtube"
    additional_context: Optional[str] = None

class Script(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    content: str
    hook: str
    call_to_action: str
    tone: str
    duration: str
    platform: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    created_at: datetime
    updated_at: datetime

class ScriptRegenerateRequest(BaseModel):
    element: Literal["hook", "intro", "body", "cta", "full"]
    additional_instructions: Optional[str] = None

# app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from app.core.database import get_db
from app.models.user import UserProfile
from pydantic import BaseModel, EmailStr

router = APIRouter()

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

@router.post("/signup")
async def signup(request: SignupRequest, db = Depends(get_db)):
    """Register a new user"""
    try:
        # Crear usuario en Supabase Auth
        auth_response = db.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name
                }
            }
        })
        
        if auth_response.user:
            return {
                "user": auth_response.user,
                "session": auth_response.session
            }
        else:
            raise HTTPException(status_code=400, detail="Signup failed")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(request: LoginRequest, db = Depends(get_db)):
    """Login user"""
    try:
        auth_response = db.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        return {
            "user": auth_response.user,
            "session": auth_response.session
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
async def logout(db = Depends(get_db)):
    """Logout user"""
    try:
        db.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# app/api/profiles.py
from fastapi import APIRouter, HTTPException, Depends, status
from app.core.security import get_current_user
from app.core.database import get_db
from app.models.user import UserProfile, UserProfileUpdate
from uuid import UUID

router = APIRouter()

@router.get("/{user_id}", response_model=UserProfile)
async def get_profile(
    user_id: UUID,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get user profile"""
    # Verificar que el usuario actual solo puede acceder a su propio perfil
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this profile"
        )
    
    response = db.table("profiles").select("*").eq("id", str(user_id)).single().execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return UserProfile(**response.data)

@router.put("/{user_id}", response_model=UserProfile)
async def update_profile(
    user_id: UUID,
    profile_update: UserProfileUpdate,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update user profile"""
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this profile"
        )
    
    update_data = profile_update.dict(exclude_unset=True)
    
    response = db.table("profiles")\
        .update(update_data)\
        .eq("id", str(user_id))\
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return UserProfile(**response.data[0])

# app/api/stripe_handler.py
from fastapi import APIRouter, HTTPException, Depends, Header, Request, BackgroundTasks
from app.core.config import settings
from app.core.security import get_current_user
from app.core.database import get_db
import stripe
from typing import Optional
import logging

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

@router.post("/create-checkout-session")
async def create_checkout_session(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a Stripe checkout session"""
    try:
        # Obtener o crear customer de Stripe
        profile = db.table("profiles").select("stripe_customer_id").eq("id", str(current_user.id)).single().execute()
        
        if profile.data and profile.data.get("stripe_customer_id"):
            customer_id = profile.data["stripe_customer_id"]
        else:
            # Crear nuevo customer en Stripe
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)}
            )
            customer_id = customer.id
            
            # Guardar customer_id en el perfil
            db.table("profiles").update({
                "stripe_customer_id": customer_id
            }).eq("id", str(current_user.id)).execute()
        
        # Crear sesión de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID_CREATOR,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing",
            metadata={
                "user_id": str(current_user.id)
            }
        )
        
        return {"checkout_url": checkout_session.url}
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(None),
    db = Depends(get_db)
):
    """Handle Stripe webhooks"""
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Procesar evento en background
    background_tasks.add_task(process_stripe_event, event, db)
    
    return {"status": "success"}

async def process_stripe_event(event, db):
    """Process Stripe webhook events"""
    logger.info(f"Processing Stripe event: {event['type']}")
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        
        # Actualizar perfil del usuario
        db.table("profiles").update({
            "subscription_plan": "creator",
            "subscription_status": "active",
            "stripe_customer_id": session["customer"]
        }).eq("id", user_id).execute()
        
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        
        # Buscar usuario por customer_id
        profile = db.table("profiles").select("id").eq("stripe_customer_id", customer_id).single().execute()
        
        if profile.data:
            # Actualizar a plan free
            db.table("profiles").update({
                "subscription_plan": "free",
                "subscription_status": "cancelled"
            }).eq("id", profile.data["id"]).execute()