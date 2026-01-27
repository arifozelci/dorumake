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
    get_password_hash,
    Token,
    User,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from src.notifications.email_sender import EmailSender, generate_random_password

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


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    receive_notifications: bool
    created_at: str


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: Optional[str] = None
    full_name: Optional[str] = ""
    role: str = "user"


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    receive_notifications: Optional[bool] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    body: str
    description: str
    variables: List[str]
    is_active: bool
    updated_at: str


class UpdateTemplateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ============================================
# AUTH ENDPOINTS
# ============================================

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    user = authenticate_user(form_data.username, form_data.password)
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


class ForgotPasswordRequest(BaseModel):
    email: str


@app.post("/api/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email"""
    # Find user by email
    for user in _users_db:
        if user.get("email") == request.email:
            # Generate new password
            new_password = generate_random_password()
            user["hashed_password"] = get_password_hash(new_password)

            # Send email
            email_sender = EmailSender()
            email_sent = email_sender.send_email(
                to=request.email,
                subject="DoruMake - Şifre Sıfırlama",
                body=f"""Merhaba {user.get('full_name', user['username'])},

Şifre sıfırlama talebiniz alındı.

Yeni geçici şifreniz: {new_password}

Lütfen giriş yaptıktan sonra şifrenizi değiştirin.

Giriş adresi: https://93-94-251-138.sslip.io/login

İyi çalışmalar,
DoruMake Ekibi"""
            )

            return {
                "status": "success",
                "message": "If the email exists, a password reset link has been sent"
            }

    # Return same message even if user not found (security)
    return {
        "status": "success",
        "message": "If the email exists, a password reset link has been sent"
    }


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


# In-memory storage (initialized before endpoints that use them)
_emails_db: List[dict] = []

_orders_db: List[dict] = [
    {
        "id": "ord-001",
        "order_code": "ORD-2026-00001",
        "supplier_type": "mutlu_aku",
        "status": "completed",
        "customer_name": "CASTROL BATMAN DALAY PETROL",
        "item_count": 12,
        "total_amount": 45600.00,
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "completed_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "error_message": None,
    },
    {
        "id": "ord-002",
        "order_code": "ORD-2026-00002",
        "supplier_type": "mann_hummel",
        "status": "completed",
        "customer_name": "TRM56062",
        "item_count": 45,
        "total_amount": 12350.00,
        "created_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        "completed_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "error_message": None,
    },
    {
        "id": "ord-003",
        "order_code": "ORD-2026-00003",
        "supplier_type": "mutlu_aku",
        "status": "failed",
        "customer_name": "CASTROL BATMAN DALAY PETROL",
        "item_count": 8,
        "total_amount": 28400.00,
        "created_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
        "completed_at": None,
        "error_message": "SAP onay butonu bulunamadı",
    },
    {
        "id": "ord-004",
        "order_code": "ORD-2026-00004",
        "supplier_type": "mann_hummel",
        "status": "processing",
        "customer_name": "TRM56018",
        "item_count": 22,
        "total_amount": 8900.00,
        "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
        "completed_at": None,
        "error_message": None,
    },
    {
        "id": "ord-005",
        "order_code": "ORD-2026-00005",
        "supplier_type": "mutlu_aku",
        "status": "pending",
        "customer_name": "CASTROL BATMAN DALAY PETROL",
        "item_count": 15,
        "total_amount": 52100.00,
        "created_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
        "completed_at": None,
        "error_message": None,
    },
]

# Audit logs - user actions
_audit_logs_db: List[dict] = [
    {"id": "audit-001", "user": "admin", "action": "login", "resource_type": "auth", "resource_id": None, "details": "Kullanıcı giriş yaptı", "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(), "ip_address": "192.168.1.100"},
    {"id": "audit-002", "user": "admin", "action": "view_orders", "resource_type": "order", "resource_id": None, "details": "Sipariş listesi görüntülendi", "timestamp": (datetime.utcnow() - timedelta(minutes=45)).isoformat(), "ip_address": "192.168.1.100"},
    {"id": "audit-003", "user": "admin", "action": "view_order", "resource_type": "order", "resource_id": "ord-001", "details": "Sipariş detayı görüntülendi: ORD-2026-00001", "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat(), "ip_address": "192.168.1.100"},
    {"id": "audit-004", "user": "admin", "action": "fetch_emails", "resource_type": "email", "resource_id": None, "details": "E-postalar IMAP'tan çekildi", "timestamp": (datetime.utcnow() - timedelta(minutes=20)).isoformat(), "ip_address": "192.168.1.100"},
]

# Order operation logs - step by step robot actions
_order_logs_db: List[dict] = [
    # ord-001 (completed - mutlu_aku)
    {"id": "log-001-01", "order_id": "ord-001", "step": 1, "action": "portal_open", "message": "Mutlu Akü portalı açılıyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=5)).isoformat()},
    {"id": "log-001-02", "order_id": "ord-001", "step": 2, "action": "login", "message": "Giriş yapılıyor: burak.bakar@castrol.com", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=4)).isoformat()},
    {"id": "log-001-03", "order_id": "ord-001", "step": 3, "action": "customer_select", "message": "Müşteri seçiliyor: CASTROL BATMAN DALAY PETROL", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=3)).isoformat()},
    {"id": "log-001-04", "order_id": "ord-001", "step": 4, "action": "menu_navigate", "message": "Menü: Satış/Satın Alma > Satın Alma Siparişi", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=2)).isoformat()},
    {"id": "log-001-05", "order_id": "ord-001", "step": 5, "action": "form_create", "message": "Yeni sipariş formu oluşturuluyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=1)).isoformat()},
    {"id": "log-001-06", "order_id": "ord-001", "step": 6, "action": "form_fill", "message": "Form dolduruldu - Depo: Merkez, Ödeme: 60 Gün", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=1, minutes=58)).isoformat()},
    {"id": "log-001-07", "order_id": "ord-001", "step": 7, "action": "products_tab", "message": "Ürünler sekmesine geçiliyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=1, minutes=55)).isoformat()},
    {"id": "log-001-08", "order_id": "ord-001", "step": 8, "action": "products_add", "message": "12 ürün eklendi, toplam: ₺45.600", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=1, minutes=45)).isoformat()},
    {"id": "log-001-09", "order_id": "ord-001", "step": 9, "action": "order_save", "message": "Sipariş kaydediliyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=1, minutes=10)).isoformat()},
    {"id": "log-001-10", "order_id": "ord-001", "step": 10, "action": "sap_confirm", "message": "SAP onayı gönderildi", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=1, minutes=5)).isoformat()},
    {"id": "log-001-11", "order_id": "ord-001", "step": 11, "action": "complete", "message": "Sipariş başarıyla tamamlandı: SAP-2026-00001", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat()},

    # ord-002 (completed - mann_hummel)
    {"id": "log-002-01", "order_id": "ord-002", "step": 1, "action": "portal_open", "message": "TecCom portalı açılıyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=5)).isoformat()},
    {"id": "log-002-02", "order_id": "ord-002", "step": 2, "action": "login", "message": "Giriş yapılıyor: dilsad.kaptan@dorufinansal.com", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=4)).isoformat()},
    {"id": "log-002-03", "order_id": "ord-002", "step": 3, "action": "menu_navigate", "message": "Menü: Sorgulama ve sipariş > Dosya Yükle", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=3)).isoformat()},
    {"id": "log-002-04", "order_id": "ord-002", "step": 4, "action": "csv_generate", "message": "CSV dosyası oluşturuldu: 45 ürün", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=2)).isoformat()},
    {"id": "log-002-05", "order_id": "ord-002", "step": 5, "action": "file_upload", "message": "Siparis_formu_TecOrder_2018.csv yükleniyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=1)).isoformat()},
    {"id": "log-002-06", "order_id": "ord-002", "step": 6, "action": "supplier_select", "message": "Tedarikçi seçildi: FILTRON-MANN+HUMMEL Türkiye", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=55)).isoformat()},
    {"id": "log-002-07", "order_id": "ord-002", "step": 7, "action": "customer_select", "message": "Müşteri seçildi: TRM56062", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=50)).isoformat()},
    {"id": "log-002-08", "order_id": "ord-002", "step": 8, "action": "order_submit", "message": "TALEP → SİPARİŞ butonu tıklandı", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2, minutes=10)).isoformat()},
    {"id": "log-002-09", "order_id": "ord-002", "step": 9, "action": "complete", "message": "Sipariş başarıyla tamamlandı: TEC-2026-00002", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()},

    # ord-003 (failed - mutlu_aku)
    {"id": "log-003-01", "order_id": "ord-003", "step": 1, "action": "portal_open", "message": "Mutlu Akü portalı açılıyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=4, minutes=5)).isoformat()},
    {"id": "log-003-02", "order_id": "ord-003", "step": 2, "action": "login", "message": "Giriş yapılıyor: burak.bakar@castrol.com", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=4, minutes=4)).isoformat()},
    {"id": "log-003-03", "order_id": "ord-003", "step": 3, "action": "customer_select", "message": "Müşteri seçiliyor: CASTROL BATMAN DALAY PETROL", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=4, minutes=3)).isoformat()},
    {"id": "log-003-04", "order_id": "ord-003", "step": 4, "action": "menu_navigate", "message": "Menü: Satış/Satın Alma > Satın Alma Siparişi", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=4, minutes=2)).isoformat()},
    {"id": "log-003-05", "order_id": "ord-003", "step": 5, "action": "form_create", "message": "Yeni sipariş formu oluşturuluyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=4, minutes=1)).isoformat()},
    {"id": "log-003-06", "order_id": "ord-003", "step": 6, "action": "form_fill", "message": "Form dolduruldu - Depo: Merkez, Ödeme: 60 Gün", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=58)).isoformat()},
    {"id": "log-003-07", "order_id": "ord-003", "step": 7, "action": "products_tab", "message": "Ürünler sekmesine geçiliyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=55)).isoformat()},
    {"id": "log-003-08", "order_id": "ord-003", "step": 8, "action": "products_add", "message": "8 ürün eklendi, toplam: ₺28.400", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=45)).isoformat()},
    {"id": "log-003-09", "order_id": "ord-003", "step": 9, "action": "order_save", "message": "Sipariş kaydediliyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=40)).isoformat()},
    {"id": "log-003-10", "order_id": "ord-003", "step": 10, "action": "sap_confirm", "message": "SAP onay butonu bulunamadı - 3 deneme yapıldı", "status": "error", "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=35)).isoformat(), "screenshot": "ord-003_sap_confirm_error.png"},

    # ord-004 (processing - mann_hummel)
    {"id": "log-004-01", "order_id": "ord-004", "step": 1, "action": "portal_open", "message": "TecCom portalı açılıyor...", "status": "success", "timestamp": (datetime.utcnow() - timedelta(minutes=30)).isoformat()},
    {"id": "log-004-02", "order_id": "ord-004", "step": 2, "action": "login", "message": "Giriş yapılıyor: dilsad.kaptan@dorufinansal.com", "status": "success", "timestamp": (datetime.utcnow() - timedelta(minutes=29)).isoformat()},
    {"id": "log-004-03", "order_id": "ord-004", "step": 3, "action": "menu_navigate", "message": "Menü: Sorgulama ve sipariş > Dosya Yükle", "status": "success", "timestamp": (datetime.utcnow() - timedelta(minutes=28)).isoformat()},
    {"id": "log-004-04", "order_id": "ord-004", "step": 4, "action": "csv_generate", "message": "CSV dosyası oluşturuldu: 22 ürün", "status": "success", "timestamp": (datetime.utcnow() - timedelta(minutes=27)).isoformat()},
    {"id": "log-004-05", "order_id": "ord-004", "step": 5, "action": "file_upload", "message": "Dosya yükleniyor...", "status": "processing", "timestamp": (datetime.utcnow() - timedelta(minutes=26)).isoformat()},

    # ord-005 (pending - no logs yet)
]


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(get_current_active_user)):
    """Get dashboard statistics"""
    today = datetime.utcnow().date()

    # Calculate stats from in-memory data
    today_orders = [o for o in _orders_db if datetime.fromisoformat(o["created_at"]).date() == today]
    today_emails = [e for e in _emails_db if datetime.fromisoformat(e.get("received_at", "2000-01-01T00:00:00")).date() == today]

    return {
        "today_orders": len(today_orders),
        "today_successful": len([o for o in today_orders if o["status"] == "completed"]),
        "today_failed": len([o for o in today_orders if o["status"] == "failed"]),
        "pending_orders": len([o for o in _orders_db if o["status"] in ("pending", "processing")]),
        "today_emails": len(today_emails),
        "queue_mutlu": len([o for o in _orders_db if o["status"] == "pending" and o["supplier_type"] == "mutlu_aku"]),
        "queue_mann": len([o for o in _orders_db if o["status"] == "pending" and o["supplier_type"] == "mann_hummel"]),
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
    # Filter orders
    filtered = _orders_db

    if status:
        filtered = [o for o in filtered if o["status"] == status]

    if supplier:
        filtered = [o for o in filtered if o["supplier_type"] == supplier]

    # Sort by created_at descending
    filtered = sorted(filtered, key=lambda x: x["created_at"], reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    orders = filtered[start:end]

    return {
        "orders": orders,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Get order details"""
    for order in _orders_db:
        if order["id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")


@app.post("/api/orders/{order_id}/retry")
async def retry_order(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Retry failed order"""
    for order in _orders_db:
        if order["id"] == order_id:
            if order["status"] == "failed":
                order["status"] = "pending"
                order["error_message"] = None
                # Add audit log
                _audit_logs_db.append({
                    "id": f"audit-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "user": current_user.username,
                    "action": "order_retry",
                    "resource_type": "order",
                    "resource_id": order_id,
                    "details": f"Sipariş yeniden deneme kuyruğuna alındı: {order['order_code']}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "ip_address": "127.0.0.1"
                })
                return {"status": "queued", "order_id": order_id}
            else:
                raise HTTPException(status_code=400, detail="Order is not in failed status")
    raise HTTPException(status_code=404, detail="Order not found")


@app.get("/api/orders/{order_id}/logs")
async def get_order_logs(order_id: str, current_user: User = Depends(get_current_active_user)):
    """Get step-by-step operation logs for an order"""
    logs = [log for log in _order_logs_db if log["order_id"] == order_id]
    logs = sorted(logs, key=lambda x: x["step"])
    return {"logs": logs, "total": len(logs)}


@app.get("/api/emails")
async def list_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """List processed emails"""
    # Filter by status if provided
    filtered = _emails_db
    if status:
        filtered = [e for e in _emails_db if e.get("status") == status]

    # Sort by received_at descending
    filtered = sorted(filtered, key=lambda x: x.get("received_at", ""), reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    emails = filtered[start:end]

    return {
        "emails": emails,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.post("/api/emails/fetch")
async def fetch_emails_from_imap(
    current_user: User = Depends(get_current_active_user),
):
    """Fetch all emails from IMAP and store in memory"""
    import ssl
    import email as email_module
    from email.header import decode_header
    from imapclient import IMAPClient
    import uuid

    global _emails_db

    def decode_header_value(value):
        if value is None:
            return ""
        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                charset = charset or "utf-8"
                try:
                    result.append(part.decode(charset))
                except:
                    result.append(part.decode("utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    try:
        # Connect to IMAP
        ssl_context = ssl.create_default_context()
        client = IMAPClient(
            host=settings.email.host,
            port=settings.email.port,
            ssl=settings.email.use_ssl,
            ssl_context=ssl_context
        )

        client.login(settings.email.user, settings.email.password)
        client.select_folder("INBOX")

        # Get all messages
        all_messages = client.search(["ALL"])

        emails_data = []

        for msg_id in all_messages:
            try:
                response = client.fetch([msg_id], ["RFC822", "INTERNALDATE", "FLAGS"])
                raw_email = response[msg_id][b"RFC822"]
                internal_date = response[msg_id][b"INTERNALDATE"]
                flags = response[msg_id][b"FLAGS"]

                msg = email_module.message_from_bytes(raw_email)

                subject = decode_header_value(msg.get("Subject", ""))
                from_addr = decode_header_value(msg.get("From", ""))

                # Extract email address
                if "<" in from_addr and ">" in from_addr:
                    from_addr = from_addr[from_addr.index("<")+1:from_addr.index(">")]

                # Check for attachments and extract body text
                has_attachments = False
                attachment_names = []
                body_text = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition", ""))

                        # Extract attachments
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                attachment_names.append(decode_header_value(filename).replace("\r\n", "").strip())
                                has_attachments = True
                        # Extract body text
                        elif content_type == "text/plain" and not body_text:
                            try:
                                charset = part.get_content_charset() or "utf-8"
                                body_text = part.get_payload(decode=True).decode(charset, errors="replace")
                                # Limit body text length
                                if len(body_text) > 2000:
                                    body_text = body_text[:2000] + "..."
                            except:
                                pass
                else:
                    # Single part message
                    try:
                        charset = msg.get_content_charset() or "utf-8"
                        body_text = msg.get_payload(decode=True).decode(charset, errors="replace")
                        if len(body_text) > 2000:
                            body_text = body_text[:2000] + "..."
                    except:
                        pass

                is_order = "caspar" in from_addr.lower() and has_attachments

                email_data = {
                    "id": str(uuid.uuid4()),
                    "imap_uid": msg_id,
                    "subject": subject,
                    "from_address": from_addr,
                    "received_at": internal_date.isoformat(),
                    "has_attachments": has_attachments,
                    "attachment_count": len(attachment_names),
                    "attachments": attachment_names,
                    "body_text": body_text,
                    "is_read": b"\\Seen" in flags,
                    "status": "processed" if b"\\Seen" in flags else "pending",
                    "is_order_email": is_order
                }

                emails_data.append(email_data)

            except Exception as e:
                continue

        client.logout()

        # Update global storage
        _emails_db = emails_data

        order_count = len([e for e in emails_data if e.get("is_order_email")])

        return {
            "status": "success",
            "total_fetched": len(emails_data),
            "order_emails": order_count,
            "message": f"Fetched {len(emails_data)} emails from IMAP"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"IMAP error: {str(e)}")


@app.get("/api/logs")
async def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    level: Optional[str] = None,
    source: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get system logs from PM2 log files"""
    import re
    from pathlib import Path

    logs = []
    log_files = [
        ("/home/ubuntu/.pm2/logs/dorumake-api-out.log", "api"),
        ("/home/ubuntu/.pm2/logs/dorumake-api-error.log", "api"),
        ("/home/ubuntu/.pm2/logs/dorumake-email-worker-out.log", "email-worker"),
        ("/home/ubuntu/.pm2/logs/dorumake-email-worker-error.log", "email-worker"),
    ]

    for log_file, source_name in log_files:
        try:
            path = Path(log_file)
            if path.exists():
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()[-500:]  # Last 500 lines

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Parse log level
                    log_level = "INFO"
                    if "ERROR" in line.upper():
                        log_level = "ERROR"
                    elif "WARNING" in line.upper() or "WARN" in line.upper():
                        log_level = "WARNING"
                    elif "DEBUG" in line.upper():
                        log_level = "DEBUG"

                    # Extract timestamp if available
                    timestamp = datetime.utcnow().isoformat()
                    # Try to parse timestamps like "2026-01-27 10:28:29"
                    ts_match = re.search(r"(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})", line)
                    if ts_match:
                        timestamp = ts_match.group(1).replace(" ", "T")

                    logs.append({
                        "id": len(logs) + 1,
                        "timestamp": timestamp,
                        "level": log_level,
                        "source": source_name,
                        "message": line[:500],  # Limit message length
                    })
        except Exception as e:
            continue

    # Calculate stats before filtering
    stats = {
        "error_count": sum(1 for l in logs if l["level"].upper() == "ERROR"),
        "warning_count": sum(1 for l in logs if l["level"].upper() == "WARNING"),
        "info_count": sum(1 for l in logs if l["level"].upper() == "INFO"),
        "debug_count": sum(1 for l in logs if l["level"].upper() == "DEBUG"),
    }

    # Filter by level if specified
    if level:
        logs = [l for l in logs if l["level"].upper() == level.upper()]

    # Filter by source if specified
    if source:
        logs = [l for l in logs if l["source"] == source]

    # Sort by timestamp descending
    logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)

    # Paginate
    total = len(logs)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_logs = logs[start:end]

    return {
        "logs": paginated_logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "stats": stats,
    }


@app.get("/api/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: Optional[str] = None,
    action: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
):
    """Get user audit logs"""
    filtered = _audit_logs_db

    if user:
        filtered = [l for l in filtered if l["user"] == user]

    if action:
        filtered = [l for l in filtered if l["action"] == action]

    # Sort by timestamp descending
    filtered = sorted(filtered, key=lambda x: x["timestamp"], reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    return {
        "logs": paginated,
        "total": total,
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
    # Return configured scheduled jobs
    jobs = [
        {
            "id": "email_poll",
            "name": "Email Polling",
            "description": "IMAP'ten yeni sipariş emaillerini kontrol eder",
            "schedule": "Her 60 saniyede bir",
            "cron": "*/1 * * * *",
            "status": "active",
            "last_run": datetime.utcnow().isoformat(),
            "next_run": (datetime.utcnow() + timedelta(seconds=60)).isoformat(),
        },
        {
            "id": "order_processor",
            "name": "Order Processor",
            "description": "Bekleyen siparişleri işler",
            "schedule": "Her 5 dakikada bir",
            "cron": "*/5 * * * *",
            "status": "active",
            "last_run": datetime.utcnow().isoformat(),
            "next_run": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
        },
        {
            "id": "health_check",
            "name": "Health Check",
            "description": "Sistem sağlık kontrolü yapar",
            "schedule": "Her 10 dakikada bir",
            "cron": "*/10 * * * *",
            "status": "active",
            "last_run": datetime.utcnow().isoformat(),
            "next_run": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
        },
        {
            "id": "log_cleanup",
            "name": "Log Cleanup",
            "description": "Eski log dosyalarını temizler",
            "schedule": "Her gün gece yarısı",
            "cron": "0 0 * * *",
            "status": "active",
            "last_run": datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat(),
            "next_run": (datetime.utcnow().replace(hour=0, minute=0, second=0) + timedelta(days=1)).isoformat(),
        },
    ]
    return {"jobs": jobs}


# ============================================
# USER MANAGEMENT ENDPOINTS
# ============================================

# In-memory users storage (will be replaced with database later)
# Pre-computed password hashes (salt: dorumake-salt-2025)
# admin123 -> eefe9baf8455e2d688e375da8aa9103ee8785326e28fcbd7e9fbde4aa6d3e073
_users_db: List[dict] = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@dorufinansal.com",
        "full_name": "Sistem Yöneticisi",
        "role": "admin",
        "is_active": True,
        "receive_notifications": True,
        "created_at": "2025-01-01T00:00:00",
        "hashed_password": "eefe9baf8455e2d688e375da8aa9103ee8785326e28fcbd7e9fbde4aa6d3e073",
    },
    {
        "id": 2,
        "username": "arif.ozelci",
        "email": "arif.ozelci@dorufinansal.com",
        "full_name": "Arif Ozelci",
        "role": "admin",
        "is_active": True,
        "receive_notifications": True,
        "created_at": "2026-01-27T07:00:00",
        "hashed_password": "eefe9baf8455e2d688e375da8aa9103ee8785326e28fcbd7e9fbde4aa6d3e073",
    },
    {
        "id": 3,
        "username": "asim.koc",
        "email": "asim.koc@dorufinansal.com",
        "full_name": "Asim Koc",
        "role": "admin",
        "is_active": True,
        "receive_notifications": True,
        "created_at": "2026-01-27T07:00:00",
        "hashed_password": "eefe9baf8455e2d688e375da8aa9103ee8785326e28fcbd7e9fbde4aa6d3e073",
    },
    {
        "id": 4,
        "username": "dilsad.kaptan",
        "email": "dilsad.kaptan@dorufinansal.com",
        "full_name": "Dilsad Kaptan",
        "role": "admin",
        "is_active": True,
        "receive_notifications": True,
        "created_at": "2026-01-27T07:00:00",
        "hashed_password": "eefe9baf8455e2d688e375da8aa9103ee8785326e28fcbd7e9fbde4aa6d3e073",
    },
]
_next_user_id = 5


@app.get("/api/users", response_model=List[UserResponse])
async def list_users(current_user: User = Depends(get_current_active_user)):
    """List all users"""
    return _users_db


@app.post("/api/users/create-with-email", response_model=UserResponse)
async def create_user_with_email(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new user and send email notification"""
    global _next_user_id

    # Check if username already exists
    for u in _users_db:
        if u["username"] == request.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if u["email"] == request.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    # Generate password if not provided
    password = request.password or generate_random_password()

    new_user = {
        "id": _next_user_id,
        "username": request.username,
        "email": request.email,
        "full_name": request.full_name or "",
        "role": request.role,
        "is_active": True,
        "receive_notifications": True,
        "created_at": datetime.utcnow().isoformat(),
        "hashed_password": get_password_hash(password),
    }
    _users_db.append(new_user)
    _next_user_id += 1

    # Send welcome email
    email_sender = EmailSender()
    email_sent = email_sender.send_email(
        to=request.email,
        subject="DoruMake - Hoş Geldiniz",
        body=f"""Merhaba {request.full_name or request.username},

DoruMake sistemine hoş geldiniz!

Kullanıcı adınız: {request.username}
Geçici şifreniz: {password}

Lütfen ilk girişinizde şifrenizi değiştirin.

Giriş adresi: https://93-94-251-138.sslip.io/login

İyi çalışmalar,
DoruMake Ekibi"""
    )

    if not email_sent:
        # Log warning but don't fail the request
        print(f"Warning: Could not send welcome email to {request.email}")

    return new_user


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update a user"""
    for user in _users_db:
        if user["id"] == user_id:
            if request.email is not None:
                user["email"] = request.email
            if request.full_name is not None:
                user["full_name"] = request.full_name
            if request.role is not None:
                user["role"] = request.role
            if request.is_active is not None:
                user["is_active"] = request.is_active
            if request.receive_notifications is not None:
                user["receive_notifications"] = request.receive_notifications
            return user

    raise HTTPException(status_code=404, detail="User not found")


@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a user"""
    global _users_db

    for i, user in enumerate(_users_db):
        if user["id"] == user_id:
            if user["username"] == "admin":
                raise HTTPException(status_code=400, detail="Cannot delete admin user")
            _users_db.pop(i)
            return {"status": "deleted", "user_id": user_id}

    raise HTTPException(status_code=404, detail="User not found")


@app.post("/api/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Reset user password and send email"""
    for user in _users_db:
        if user["id"] == user_id:
            # Generate new password
            new_password = generate_random_password()
            user["hashed_password"] = get_password_hash(new_password)

            # Send password reset email
            email_sender = EmailSender()
            email_sent = email_sender.send_email(
                to=user["email"],
                subject="DoruMake - Şifre Sıfırlama",
                body=f"""Merhaba {user.get('full_name', user['username'])},

Şifreniz sıfırlandı.

Yeni geçici şifreniz: {new_password}

Lütfen giriş yaptıktan sonra şifrenizi değiştirin.

Giriş adresi: https://93-94-251-138.sslip.io/login

İyi çalışmalar,
DoruMake Ekibi"""
            )

            return {
                "status": "password_reset",
                "user_id": user_id,
                "message": "Password reset email sent" if email_sent else "Password reset but email not sent (SMTP not configured)"
            }

    raise HTTPException(status_code=404, detail="User not found")


# ============================================
# EMAIL TEMPLATE ENDPOINTS
# ============================================

# In-memory templates storage
_templates_db: List[dict] = [
    {
        "id": 1,
        "name": "new_user",
        "subject": "DoruMake - Hoş Geldiniz",
        "body": """Merhaba {full_name},

DoruMake sistemine hoş geldiniz!

Kullanıcı adınız: {username}
Geçici şifreniz: {password}

Lütfen ilk girişinizde şifrenizi değiştirin.

İyi çalışmalar,
DoruMake Ekibi""",
        "description": "Yeni kullanıcı oluşturulduğunda gönderilir",
        "variables": ["full_name", "username", "password"],
        "is_active": True,
        "updated_at": "2025-01-01T00:00:00",
    },
    {
        "id": 2,
        "name": "password_reset",
        "subject": "DoruMake - Şifre Sıfırlama",
        "body": """Merhaba {full_name},

Şifreniz sıfırlandı.

Yeni geçici şifreniz: {password}

Lütfen giriş yaptıktan sonra şifrenizi değiştirin.

İyi çalışmalar,
DoruMake Ekibi""",
        "description": "Şifre sıfırlandığında gönderilir",
        "variables": ["full_name", "password"],
        "is_active": True,
        "updated_at": "2025-01-01T00:00:00",
    },
    {
        "id": 3,
        "name": "order_error",
        "subject": "DoruMake - Sipariş Hatası: {order_code}",
        "body": """Sipariş işlenirken hata oluştu.

Sipariş Kodu: {order_code}
Tedarikçi: {supplier}
Hata: {error_message}

Lütfen kontrol edin.

DoruMake Sistemi""",
        "description": "Sipariş hatası oluştuğunda gönderilir",
        "variables": ["order_code", "supplier", "error_message"],
        "is_active": True,
        "updated_at": "2025-01-01T00:00:00",
    },
    {
        "id": 4,
        "name": "order_completed",
        "subject": "DoruMake - Sipariş Tamamlandı: {order_code}",
        "body": """Sipariş başarıyla tamamlandı.

Sipariş Kodu: {order_code}
Tedarikçi: {supplier}
Toplam Kalem: {item_count}

DoruMake Sistemi""",
        "description": "Sipariş başarıyla tamamlandığında gönderilir",
        "variables": ["order_code", "supplier", "item_count"],
        "is_active": True,
        "updated_at": "2025-01-01T00:00:00",
    },
    {
        "id": 5,
        "name": "system_alert",
        "subject": "DoruMake - Sistem Uyarısı",
        "body": """Sistem Uyarısı

Seviye: {level}
Mesaj: {message}
Zaman: {timestamp}

DoruMake Sistemi""",
        "description": "Sistem uyarıları için gönderilir",
        "variables": ["level", "message", "timestamp"],
        "is_active": True,
        "updated_at": "2025-01-01T00:00:00",
    },
]


@app.get("/api/templates", response_model=List[TemplateResponse])
async def list_templates(current_user: User = Depends(get_current_active_user)):
    """List all email templates"""
    return _templates_db


@app.put("/api/templates/{template_name}", response_model=TemplateResponse)
async def update_template(
    template_name: str,
    request: UpdateTemplateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Update an email template"""
    for template in _templates_db:
        if template["name"] == template_name:
            if request.subject is not None:
                template["subject"] = request.subject
            if request.body is not None:
                template["body"] = request.body
            if request.description is not None:
                template["description"] = request.description
            if request.is_active is not None:
                template["is_active"] = request.is_active
            template["updated_at"] = datetime.utcnow().isoformat()
            return template

    raise HTTPException(status_code=404, detail="Template not found")


# ============================================
# NOTIFICATION ENDPOINTS
# ============================================

class NotificationRequest(BaseModel):
    template_name: str
    params: dict


class OrderErrorNotificationRequest(BaseModel):
    order_code: str
    supplier: str
    error_message: str


class OrderCompletedNotificationRequest(BaseModel):
    order_code: str
    supplier: str
    item_count: int


class SystemAlertNotificationRequest(BaseModel):
    level: str  # warning, error, critical
    message: str


def _send_notification_to_all_users(template_name: str, params: dict) -> dict:
    """Send notification to all users with receive_notifications enabled"""
    # Find template
    template = None
    for t in _templates_db:
        if t["name"] == template_name:
            template = t
            break

    if not template:
        return {"success": False, "error": f"Template not found: {template_name}"}

    if not template.get("is_active", True):
        return {"success": False, "error": "Template is disabled"}

    # Prepare subject and body
    subject = template["subject"]
    body = template["body"]

    for key, value in params.items():
        placeholder = "{" + key + "}"
        subject = subject.replace(placeholder, str(value))
        body = body.replace(placeholder, str(value))

    # Get recipients
    recipients = [
        user["email"]
        for user in _users_db
        if user.get("receive_notifications", True) and user.get("is_active", True)
    ]

    if not recipients:
        return {"success": False, "error": "No recipients with notifications enabled"}

    # Send emails
    email_sender = EmailSender()
    results = {}
    success_count = 0
    fail_count = 0

    for recipient in recipients:
        sent = email_sender.send_email(to=recipient, subject=subject, body=body)
        results[recipient] = "sent" if sent else "failed"
        if sent:
            success_count += 1
        else:
            fail_count += 1

    return {
        "success": success_count > 0,
        "sent_count": success_count,
        "failed_count": fail_count,
        "recipients": results,
        "template": template_name,
    }


@app.post("/api/notifications/send")
async def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send a notification to all users using a template"""
    result = _send_notification_to_all_users(request.template_name, request.params)
    if not result["success"] and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/notifications/order-error")
async def send_order_error_notification(
    request: OrderErrorNotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send order error notification to all users"""
    result = _send_notification_to_all_users("order_error", {
        "order_code": request.order_code,
        "supplier": request.supplier,
        "error_message": request.error_message,
    })
    if not result["success"] and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/notifications/order-completed")
async def send_order_completed_notification(
    request: OrderCompletedNotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send order completed notification to all users"""
    result = _send_notification_to_all_users("order_completed", {
        "order_code": request.order_code,
        "supplier": request.supplier,
        "item_count": request.item_count,
    })
    if not result["success"] and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/notifications/system-alert")
async def send_system_alert_notification(
    request: SystemAlertNotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send system alert notification to all users"""
    result = _send_notification_to_all_users("system_alert", {
        "level": request.level,
        "message": request.message,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    })
    if not result["success"] and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# Startup/shutdown events
@app.on_event("startup")
async def startup():
    """Startup event"""
    pass


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    pass
