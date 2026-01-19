"""
DoruMake Database Models
SQLAlchemy ORM models matching Prisma schema
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum, Numeric, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .connection import Base


# ============================================
# ENUMS
# ============================================

class OrderStatus(enum.Enum):
    """Sipariş durumları"""
    PENDING = "PENDING"                 # Beklemede
    PROCESSING = "PROCESSING"           # İşleniyor
    PORTAL_LOGIN = "PORTAL_LOGIN"       # Portal'a giriş yapılıyor
    FORM_FILLING = "FORM_FILLING"       # Form dolduruluyor
    PRODUCTS_ADDING = "PRODUCTS_ADDING" # Ürünler ekleniyor
    SAVING = "SAVING"                   # Kaydediliyor
    CONFIRMING = "CONFIRMING"           # Onaylanıyor (SAP)
    COMPLETED = "COMPLETED"             # Tamamlandı
    FAILED = "FAILED"                   # Başarısız
    CANCELLED = "CANCELLED"             # İptal edildi


class EmailStatus(enum.Enum):
    """E-posta durumları"""
    UNPROCESSED = "UNPROCESSED"   # İşlenmemiş
    PROCESSING = "PROCESSING"     # İşleniyor
    PROCESSED = "PROCESSED"       # İşlendi
    FAILED = "FAILED"             # Başarısız
    IGNORED = "IGNORED"           # Yoksayıldı


class LogLevel(enum.Enum):
    """Log seviyeleri"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


# ============================================
# TEMEL MODELLER
# ============================================

class Supplier(Base):
    """Tedarikçiler (Mutlu Akü, Mann & Hummel)"""
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    portal_url: Mapped[Optional[str]] = mapped_column(String(500))
    username: Mapped[Optional[str]] = mapped_column(String(255))
    password: Mapped[Optional[str]] = mapped_column(String(255))  # Encrypted
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="supplier")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="supplier")
    customer_mappings: Mapped[List["CustomerSupplierMapping"]] = relationship(
        "CustomerSupplierMapping", back_populates="supplier"
    )


class Customer(Base):
    """Müşteriler (Castrol Bayileri)"""
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ship_to_code: Mapped[Optional[str]] = mapped_column(String(100))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    district: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")
    supplier_mappings: Mapped[List["CustomerSupplierMapping"]] = relationship(
        "CustomerSupplierMapping", back_populates="customer"
    )


class CustomerSupplierMapping(Base):
    """Müşteri-Tedarikçi Eşlemesi"""
    __tablename__ = "customer_supplier_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=False)
    supplier_customer_code: Mapped[str] = mapped_column(String(100), nullable=False)  # TRM56062
    supplier_customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_depo: Mapped[Optional[str]] = mapped_column(String(100))
    default_personel: Mapped[Optional[str]] = mapped_column(String(100))
    default_odeme_vadesi: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="supplier_mappings")
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="customer_mappings")

    __table_args__ = (
        UniqueConstraint("customer_id", "supplier_id", name="uq_customer_supplier"),
    )


class Product(Base):
    """Ürünler"""
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manufacturer_code: Mapped[Optional[str]] = mapped_column(String(100))
    palet_ici_miktar: Mapped[Optional[int]] = mapped_column(Integer)
    unit: Mapped[str] = mapped_column(String(20), default="ADET")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="products")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")

    __table_args__ = (
        UniqueConstraint("supplier_id", "code", name="uq_supplier_product"),
    )


# ============================================
# SİPARİŞ MODELLERİ
# ============================================

class Order(Base):
    """Siparişler"""
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)

    # Sipariş Bilgileri
    order_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    caspar_order_no: Mapped[Optional[str]] = mapped_column(String(100))
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Durum
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)

    # Portal Bilgileri
    portal_order_no: Mapped[Optional[str]] = mapped_column(String(100))
    sap_transferred: Mapped[bool] = mapped_column(Boolean, default=False)

    # İlişkili E-posta
    email_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("emails.id"))

    # Tutarlar
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default="TRY")

    # Notlar
    notes: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Tarihler
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="orders")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    email: Mapped[Optional["Email"]] = relationship("Email", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    logs: Mapped[List["OrderLog"]] = relationship("OrderLog", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Sipariş Kalemleri"""
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("products.id"))

    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[Optional[str]] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    total_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(10), default="TRY")

    shipment_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="order_items")


class OrderLog(Base):
    """Sipariş Logları"""
    __tablename__ = "order_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)

    action: Mapped[str] = mapped_column(String(100), nullable=False)  # LOGIN, CUSTOMER_SELECT, etc.
    status: Mapped[str] = mapped_column(String(20), nullable=False)   # SUCCESS, FAILED, INFO
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON)

    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="logs")


# ============================================
# E-POSTA MODELLERİ
# ============================================

class Email(Base):
    """E-postalar"""
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # E-posta Bilgileri
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    to_address: Mapped[str] = mapped_column(String(255), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # İçerik
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)

    # Durum
    status: Mapped[EmailStatus] = mapped_column(Enum(EmailStatus), default=EmailStatus.UNPROCESSED)

    # Ek Dosyalar
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)

    # İşleme
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attachments: Mapped[List["EmailAttachment"]] = relationship(
        "EmailAttachment", back_populates="email", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="email")


class EmailAttachment(Base):
    """E-posta Ekleri"""
    __tablename__ = "email_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email_id: Mapped[str] = mapped_column(String(36), ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # Bytes
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    is_parsed: Mapped[bool] = mapped_column(Boolean, default=False)
    parse_error: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    email: Mapped["Email"] = relationship("Email", back_populates="attachments")


# ============================================
# SİSTEM MODELLERİ
# ============================================

class SystemLog(Base):
    """Sistem Logları"""
    __tablename__ = "system_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    level: Mapped[LogLevel] = mapped_column(Enum(LogLevel), default=LogLevel.INFO)
    source: Mapped[str] = mapped_column(String(100), nullable=False)  # EMAIL_SERVICE, ROBOT, API
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Setting(Base):
    """Sistem Ayarları"""
    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
