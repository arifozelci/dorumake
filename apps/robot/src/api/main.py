"""
DoruMake API
FastAPI application for admin panel communication
"""

from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings

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
# ENDPOINTS
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
async def get_stats():
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
async def get_order(order_id: str):
    """Get order details"""
    # TODO: Implement database query
    raise HTTPException(status_code=404, detail="Order not found")


@app.post("/api/orders/{order_id}/retry")
async def retry_order(order_id: str):
    """Retry failed order"""
    # TODO: Implement retry logic
    return {"status": "queued", "order_id": order_id}


@app.get("/api/emails")
async def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
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
async def create_manual_order(request: ManualOrderRequest):
    """Create and process order manually"""
    # TODO: Implement manual order creation
    return {
        "status": "created",
        "order_id": "manual-" + datetime.now().strftime("%Y%m%d%H%M%S"),
    }


@app.get("/api/suppliers")
async def list_suppliers():
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
async def get_scheduler_jobs():
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
