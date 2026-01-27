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


# In-memory emails storage
_emails_db: List[dict] = []


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

                # Check for attachments
                has_attachments = False
                attachment_names = []
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get("Content-Disposition") and "attachment" in str(part.get("Content-Disposition")):
                            filename = part.get_filename()
                            if filename:
                                attachment_names.append(decode_header_value(filename).replace("\r\n", "").strip())
                                has_attachments = True

                is_order = "caspar" in from_addr.lower() and has_attachments

                email_data = {
                    "id": str(uuid.uuid4()),
                    "imap_uid": msg_id,
                    "subject": subject,
                    "from_address": from_addr,
                    "received_at": internal_date.isoformat(),
                    "has_attachments": has_attachments,
                    "attachments": attachment_names,
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


# Startup/shutdown events
@app.on_event("startup")
async def startup():
    """Startup event"""
    pass


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    pass
