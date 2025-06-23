# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os

# Set test environment
os.environ["TESTING"] = "true"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from main import app
from app.core.database import SupabaseDB

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def mock_db():
    """Mock Supabase client"""
    with patch('app.core.database.SupabaseDB.get_client') as mock:
        mock_client = Mock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return Mock(
        id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com"
    )

# tests/test_auth.py
import pytest
from unittest.mock import Mock, patch

def test_signup_success(client, mock_db):
    """Test successful user signup"""
    # Mock Supabase response
    mock_db.auth.sign_up.return_value = Mock(
        user=Mock(id="123", email="test@example.com"),
        session=Mock(access_token="token123")
    )
    
    response = client.post("/api/v1/auth/signup", json={
        "email": "test@example.com",
        "password": "Test123!",
        "full_name": "Test User"
    })
    
    assert response.status_code == 200
    assert "user" in response.json()
    assert "session" in response.json()

def test_signup_invalid_email(client, mock_db):
    """Test signup with invalid email"""
    response = client.post("/api/v1/auth/signup", json={
        "email": "invalid-email",
        "password": "Test123!",
        "full_name": "Test User"
    })
    
    assert response.status_code == 422

def test_login_success(client, mock_db):
    """Test successful login"""
    mock_db.auth.sign_in_with_password.return_value = Mock(
        user=Mock(id="123", email="test@example.com"),
        session=Mock(access_token="token123")
    )
    
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "Test123!"
    })
    
    assert response.status_code == 200
    assert "user" in response.json()
    assert "session" in response.json()

def test_login_invalid_credentials(client, mock_db):
    """Test login with invalid credentials"""
    mock_db.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
    
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "WrongPassword"
    })
    
    assert response.status_code == 401

# tests/test_profiles.py
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

@patch('app.api.profiles.get_current_user')
def test_get_profile_success(mock_get_user, client, mock_db, mock_user):
    """Test getting user profile"""
    mock_get_user.return_value = mock_user
    user_id = mock_user.id
    
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={
            "id": user_id,
            "email": "test@example.com",
            "subscription_plan": "free",
            "subscription_status": "active"
        }
    )
    
    response = client.get(
        f"/api/v1/profiles/{user_id}",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

@patch('app.api.profiles.get_current_user')
def test_get_profile_unauthorized(mock_get_user, client, mock_db, mock_user):
    """Test getting another user's profile"""
    mock_get_user.return_value = mock_user
    other_user_id = str(uuid4())
    
    response = client.get(
        f"/api/v1/profiles/{other_user_id}",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 403

@patch('app.api.profiles.get_current_user')
def test_update_profile_success(mock_get_user, client, mock_db, mock_user):
    """Test updating user profile"""
    mock_get_user.return_value = mock_user
    user_id = mock_user.id
    
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
        data=[{
            "id": user_id,
            "email": "test@example.com",
            "content_style": "educational",
            "target_audience": "entrepreneurs"
        }]
    )
    
    response = client.put(
        f"/api/v1/profiles/{user_id}",
        json={
            "content_style": "educational",
            "target_audience": "entrepreneurs"
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["content_style"] == "educational"

# tests/test_scripts.py
import pytest
from unittest.mock import Mock, patch, AsyncMock

@patch('app.api.scripts.get_current_user')
@patch('app.api.scripts.LLMService')
@patch('app.api.scripts.EmbeddingService')
async def test_generate_script_success(
    mock_embedding, mock_llm, mock_get_user, client, mock_db, mock_user
):
    """Test successful script generation"""
    mock_get_user.return_value = mock_user
    
    # Mock user profile check
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={"subscription_plan": "creator"}
    )
    
    # Mock LLM response
    mock_llm_instance = Mock()
    mock_llm_instance.generate_script = AsyncMock(return_value={
        "title": "Test Script",
        "content": "This is a test script",
        "hook": "Amazing hook",
        "call_to_action": "Subscribe now!"
    })
    mock_llm.return_value = mock_llm_instance
    
    # Mock embedding
    mock_embedding_instance = Mock()
    mock_embedding_instance.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    mock_embedding.return_value = mock_embedding_instance
    
    # Mock DB insert
    mock_db.table.return_value.insert.return_value.execute.return_value = Mock(
        data=[{
            "id": "123",
            "title": "Test Script",
            "content": "This is a test script",
            "hook": "Amazing hook",
            "call_to_action": "Subscribe now!"
        }]
    )
    
    response = client.post(
        "/api/v1/scripts/generate",
        json={
            "idea": "How to use AI for business",
            "tone": "educational",
            "duration": "60s",
            "platform": "youtube"
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "Test Script"

@patch('app.api.scripts.get_current_user')
def test_generate_script_free_limit(mock_get_user, client, mock_db, mock_user):
    """Test script generation limit for free users"""
    mock_get_user.return_value = mock_user
    
    # Mock free user profile
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={"subscription_plan": "free"}
    )
    
    # Mock script count (over limit)
    mock_db.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = Mock(
        count=5
    )
    
    response = client.post(
        "/api/v1/scripts/generate",
        json={
            "idea": "Test idea",
            "tone": "casual",
            "duration": "30s",
            "platform": "tiktok"
        },
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 403
    assert "limit reached" in response.json()["detail"].lower()

# tests/test_stripe.py
import pytest
from unittest.mock import Mock, patch
import stripe

@patch('app.api.stripe_handler.get_current_user')
@patch('app.api.stripe_handler.stripe.Customer.create')
@patch('app.api.stripe_handler.stripe.checkout.Session.create')
def test_create_checkout_session(
    mock_session_create, mock_customer_create, mock_get_user, 
    client, mock_db, mock_user
):
    """Test creating Stripe checkout session"""
    mock_get_user.return_value = mock_user
    
    # Mock profile without Stripe customer
    mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={}
    )
    
    # Mock Stripe customer creation
    mock_customer_create.return_value = Mock(id="cus_123")
    
    # Mock checkout session
    mock_session_create.return_value = Mock(url="https://checkout.stripe.com/test")
    
    response = client.post(
        "/api/v1/stripe/create-checkout-session",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert "checkout_url" in response.json()

@patch('app.api.stripe_handler.stripe.Webhook.construct_event')
def test_stripe_webhook_success(mock_construct_event, client, mock_db):
    """Test Stripe webhook handling"""
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": "123"},
                "customer": "cus_123"
            }
        }
    }
    mock_construct_event.return_value = mock_event
    
    response = client.post(
        "/api/v1/stripe/webhook",
        data=b"test_payload",
        headers={"stripe-signature": "test_signature"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"

# tests/test_video_analysis.py
import pytest
from unittest.mock import Mock, patch, AsyncMock

@patch('app.api.video_analysis.get_current_user')
def test_start_video_analysis(mock_get_user, client, mock_db, mock_user):
    """Test starting video analysis"""
    mock_get_user.return_value = mock_user
    
    mock_db.table.return_value.insert.return_value.execute.return_value = Mock()
    
    response = client.post(
        "/api/v1/videos/analyze",
        json={"video_url": "https://example.com/video.mp4"},
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert "analysis_id" in response.json()
    assert response.json()["status"] == "queued"

@patch('app.api.video_analysis.get_current_user')
def test_get_analysis_status(mock_get_user, client, mock_db, mock_user):
    """Test getting video analysis status"""
    mock_get_user.return_value = mock_user
    analysis_id = "123e4567-e89b-12d3-a456-426614174000"
    
    mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
        data={
            "id": analysis_id,
            "status": "completed",
            "results": {"technical": {}, "qualitative": {}}
        }
    )
    
    response = client.get(
        f"/api/v1/videos/analysis/{analysis_id}",
        headers={"Authorization": "Bearer test-token"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

# tests/test_services.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService

@patch('app.services.llm_service.ChatAnthropic')
async def test_llm_generate_script(mock_anthropic):
    """Test LLM script generation"""
    mock_model = Mock()
    mock_model.ainvoke = AsyncMock(return_value=Mock(
        content='{"title": "Test", "content": "Content", "hook": "Hook", "call_to_action": "CTA"}'
    ))
    mock_anthropic.return_value = mock_model
    
    service = LLMService()
    result = await service.generate_script(
        idea="Test idea",
        tone="casual",
        duration="60s",
        platform="youtube"
    )
    
    assert result["title"] == "Test"
    assert result["content"] == "Content"
    assert result["hook"] == "Hook"
    assert result["call_to_action"] == "CTA"

@patch('app.services.embedding_service.OpenAIEmbeddings')
async def test_embedding_generation(mock_embeddings):
    """Test embedding generation"""
    mock_embedding_instance = Mock()
    mock_embedding_instance.aembed_query = AsyncMock(return_value=[0.1] * 1536)
    mock_embeddings.return_value = mock_embedding_instance
    
    service = EmbeddingService()
    result = await service.generate_embedding("Test text")
    
    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)

# tests/test_integration.py
"""Integration tests for complete workflows"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

@pytest.mark.asyncio
async def test_complete_script_generation_workflow(client):
    """Test complete workflow from login to script generation"""
    with patch('app.core.database.get_db') as mock_db:
        # 1. Login
        mock_db.return_value.auth.sign_in_with_password.return_value = Mock(
            user=Mock(id="user123", email="test@example.com"),
            session=Mock(access_token="token123")
        )
        
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "Test123!"
        })
        assert login_response.status_code == 200
        
        token = login_response.json()["session"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Update profile
        with patch('app.api.profiles.get_current_user') as mock_user:
            mock_user.return_value = Mock(id="user123")
            
            mock_db.return_value.table.return_value.update.return_value.eq.return_value.execute.return_value = Mock(
                data=[{"id": "user123", "content_style": "educational"}]
            )
            
            profile_response = client.put(
                "/api/v1/profiles/user123",
                json={"content_style": "educational"},
                headers=headers
            )
            assert profile_response.status_code == 200
        
        # 3. Generate script
        with patch('app.api.scripts.get_current_user') as mock_user, \
             patch('app.api.scripts.LLMService') as mock_llm, \
             patch('app.api.scripts.EmbeddingService') as mock_embedding:
            
            mock_user.return_value = Mock(id="user123")
            
            # Mock services
            mock_llm_instance = Mock()
            mock_llm_instance.generate_script = AsyncMock(return_value={
                "title": "Test Script",
                "content": "Content",
                "hook": "Hook",
                "call_to_action": "CTA"
            })
            mock_llm.return_value = mock_llm_instance
            
            mock_embedding_instance = Mock()
            mock_embedding_instance.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
            mock_embedding.return_value = mock_embedding_instance
            
            mock_db.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = Mock(
                data={"subscription_plan": "creator"}
            )
            
            mock_db.return_value.table.return_value.insert.return_value.execute.return_value = Mock(
                data=[{"id": "script123", "title": "Test Script"}]
            )
            
            script_response = client.post(
                "/api/v1/scripts/generate",
                json={
                    "idea": "Test idea",
                    "tone": "casual",
                    "duration": "60s",
                    "platform": "youtube"
                },
                headers=headers
            )
            assert script_response.status_code == 200

# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short

# tests/requirements-test.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0
httpx==0.26.0
faker==20.1.0