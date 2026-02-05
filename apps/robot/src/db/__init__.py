# Database module

# Lazy import for async connection (requires aioodbc)
try:
    from .connection import get_db, engine, AsyncSessionLocal
except ImportError:
    get_db = None
    engine = None
    AsyncSessionLocal = None

# Sync SQL Server database helper (uses pyodbc)
try:
    from .sqlserver import db as sqlserver_db
except ImportError:
    sqlserver_db = None

from .models import (
    Supplier,
    Customer,
    CustomerSupplierMapping,
    Product,
    Order,
    OrderItem,
    OrderLog,
    Email,
    EmailAttachment,
    SystemLog,
    Setting,
    OrderStatus,
    EmailStatus,
    LogLevel
)

__all__ = [
    "get_db",
    "engine",
    "AsyncSessionLocal",
    "sqlserver_db",
    "Supplier",
    "Customer",
    "CustomerSupplierMapping",
    "Product",
    "Order",
    "OrderItem",
    "OrderLog",
    "Email",
    "EmailAttachment",
    "SystemLog",
    "Setting",
    "OrderStatus",
    "EmailStatus",
    "LogLevel"
]
