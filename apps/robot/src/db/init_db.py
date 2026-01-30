"""
DoruMake Database Initialization
Creates tables and seeds initial data
"""

import asyncio
import hashlib
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from .connection import engine, AsyncSessionLocal, Base
from .models import (
    User, Supplier, Customer, CustomerSupplierMapping,
    Setting, SystemLog, LogLevel
)


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")


async def seed_suppliers(session: AsyncSession):
    """Seed supplier data"""
    suppliers = [
        {
            "id": str(uuid.uuid4()),
            "name": "Mutlu Akü",
            "code": "MUTLU",
            "portal_url": "https://mutlu.visionnext.com.tr/Prm/UserAccount/Login",
            "username": "burak.bakar@castrol.com",
            "password": "123456",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Mann & Hummel",
            "code": "MANN",
            "portal_url": "https://teccom.tecalliance.net/newapp/auth/welcome",
            "username": "dilsad.kaptan@dorufinansal.com",
            "password": "Dilsad.2201",
            "is_active": True,
        },
    ]

    for s in suppliers:
        supplier = Supplier(**s)
        session.add(supplier)

    print(f"Seeded {len(suppliers)} suppliers")
    return suppliers


async def seed_customers(session: AsyncSession):
    """Seed customer data"""
    customers = [
        {
            "id": str(uuid.uuid4()),
            "name": "CASTROL BATMAN DALAY PETROL",
            "code": "DALAY",
            "ship_to_code": "DALAY-001",
            "city": "Batman",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "CASTROL TEST MUSTERI",
            "code": "TEST",
            "ship_to_code": "TEST-001",
            "city": "Istanbul",
            "is_active": True,
        },
    ]

    for c in customers:
        customer = Customer(**c)
        session.add(customer)

    print(f"Seeded {len(customers)} customers")
    return customers


async def seed_users(session: AsyncSession):
    """Seed user data"""
    users = [
        {
            "username": "admin",
            "email": "admin@dorumake.com",
            "full_name": "Sistem Yöneticisi",
            "hashed_password": hash_password("admin123"),
            "role": "admin",
            "is_active": True,
            "receive_notifications": True,
        },
        {
            "username": "arif.ozelci",
            "email": "arif.ozelci@dorufinansal.com",
            "full_name": "Arif Özelci",
            "hashed_password": hash_password("admin123"),
            "role": "admin",
            "is_active": True,
            "receive_notifications": True,
        },
        {
            "username": "dilsad.kaptan",
            "email": "dilsad.kaptan@dorufinansal.com",
            "full_name": "Dilsad Kaptan",
            "hashed_password": hash_password("admin123"),
            "role": "admin",
            "is_active": True,
            "receive_notifications": True,
        },
    ]

    for u in users:
        user = User(**u)
        session.add(user)

    print(f"Seeded {len(users)} users")


async def seed_settings(session: AsyncSession):
    """Seed system settings"""
    settings = [
        {
            "id": str(uuid.uuid4()),
            "key": "email_poll_interval",
            "value": "60",
            "description": "E-posta kontrol aralığı (saniye)",
        },
        {
            "id": str(uuid.uuid4()),
            "key": "max_retry_attempts",
            "value": "3",
            "description": "Maksimum yeniden deneme sayısı",
        },
        {
            "id": str(uuid.uuid4()),
            "key": "screenshot_on_error",
            "value": "true",
            "description": "Hata durumunda ekran görüntüsü al",
        },
        {
            "id": str(uuid.uuid4()),
            "key": "notification_enabled",
            "value": "true",
            "description": "E-posta bildirimleri aktif",
        },
    ]

    for s in settings:
        setting = Setting(**s)
        session.add(setting)

    print(f"Seeded {len(settings)} settings")


async def log_init(session: AsyncSession):
    """Log database initialization"""
    log = SystemLog(
        id=str(uuid.uuid4()),
        level=LogLevel.INFO,
        source="DB_INIT",
        action="database_initialized",
        message="Database tables created and seeded successfully",
        details={"timestamp": datetime.utcnow().isoformat()},
    )
    session.add(log)


async def seed_all():
    """Run all seed functions"""
    print("\n=== Seeding Database ===\n")

    async with AsyncSessionLocal() as session:
        try:
            # Seed data
            await seed_suppliers(session)
            await seed_customers(session)
            await seed_users(session)
            await seed_settings(session)
            await log_init(session)

            await session.commit()
            print("\n=== Database seeded successfully! ===\n")

        except Exception as e:
            await session.rollback()
            print(f"\nError seeding database: {e}")
            raise


async def init_database():
    """Initialize database - create tables and seed data"""
    await create_tables()
    await seed_all()


def main():
    """Entry point for database initialization"""
    print("\n" + "=" * 50)
    print("DoruMake Database Initialization")
    print("=" * 50 + "\n")

    asyncio.run(init_database())

    print("\n" + "=" * 50)
    print("Initialization Complete!")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
