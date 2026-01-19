"""
DoruMake API
FastAPI application for admin panel communication
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from src.config import settings
from src.api.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    Token,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# Create FastAPI app
app = FastAPI(
    title="DoruMake API",
    description="Order Automation System API",
    version=settings.app_version,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# MODELS
# ============================================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: dict


class OrderResponse(BaseModel):
    id: str
    order_code: str
    supplier_type: str
    status: str
    customer_name: Optional[str]
    item_count: int
    total_amount: Optional[float]
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


class EmailResponse(BaseModel):
    id: str
    subject: str
    from_address: str
    received_at: str
    status: str
    has_attachments: bool
    attachment_count: int


class StatsResponse(BaseModel):
    today_orders: int
    today_successful: int
    today_failed: int
    pending_orders: int
    today_emails: int
    queue_mutlu: int
    queue_mann: int


class ManualOrderRequest(BaseModel):
    supplier_type: str
    order_code: str
    customer_code: str
    items: List[dict]


# ============================================
# AUTH ENDPOINTS
# ============================================

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    print(f"Login attempt - username: {form_data.username}, password length: {len(form_data.password)}")
    user = authenticate_user(form_data.username, form_data.password)
    print(f"Authentication result: {user}")
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user info"""
    return {"username": current_user.username}


# ============================================
# ENDPOINTS (Protected)
# ============================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "services": {
            "api": "running",
            "email_worker": "running",  # TODO: Check actual status
            "order_worker": "running",  # TODO: Check actual status
            "scheduler": "running",  # TODO: Check actual status
        }
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get dashboard statistics"""
    # TODO: Implement actual database queries
    return {
        "today_orders": 0,
        "today_successful": 0,
        "today_failed": 0,
        "pending_orders": 0,
        "today_emails": 0,
        "queue_mutlu": 0,
        "queue_mann": 0,
    }


@app.get("/api/orders", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    supplier: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List orders with pagination and filters"""
    # TODO: Implement database query
    return {
        "orders": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Get order details"""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Order not found")


@app.post("/api/orders/{order_id}/retry")
async def retry_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Retry failed order"""
    # TODO: Implement retry logic
    return {"status": "queued", "order_id": order_id}


@app.get("/api/emails")
async def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List processed emails"""
    # TODO: Implement database query
    return {
        "emails": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/logs")
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = None,
    source: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get system logs"""
    # TODO: Implement database query
    return {
        "logs": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


@app.post("/api/orders/manual")
async def create_manual_order(request: ManualOrderRequest, current_user: User = Depends(get_current_active_user)):
    """Create and process order manually"""
    # TODO: Implement manual order creation
    return {
        "status": "created",
        "order_id": "manual-" + datetime.now().strftime("%Y%m%d%H%M%S"),
    }


@app.get("/api/suppliers")
async def list_suppliers(current_user: User = Depends(get_current_active_user)):
    """List configured suppliers"""
    return {
        "suppliers": [
            {
                "code": "MUTLU",
                "name": "Mutlu Akü",
                "portal_url": settings.mutlu_aku.portal_url,
                "active": True,
            },
            {
                "code": "MANN",
                "name": "Mann & Hummel",
                "portal_url": settings.mann_hummel.portal_url,
                "active": True,
            },
        ]
    }


@app.get("/api/scheduler/jobs")
async def get_scheduler_jobs(current_user: User = Depends(get_current_active_user)):
    """Get scheduled jobs"""
    # TODO: Get from scheduler instance
    return {"jobs": []}


# Startup/shutdown events
@app.on_event("startup")
async def startup():
    """Startup event"""
    pass


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    pass
