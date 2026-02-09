"""
KolayRobot Configuration Settings
Pydantic-based settings management with environment variable support
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings (SQL Server)"""
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    host: str = "localhost"
    port: int = 1433
    user: str = "sa"
    password: str = ""  # Set via DB_PASSWORD env var
    name: str = "DoruMake"
    driver: str = "ODBC Driver 18 for SQL Server"

    @property
    def url(self) -> str:
        # Sync connection string for SQL Server
        return f"mssql+pyodbc://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?driver={self.driver}&TrustServerCertificate=yes"

    @property
    def async_url(self) -> str:
        # Async connection string for SQL Server using aioodbc
        return f"mssql+aioodbc://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?driver={self.driver}&TrustServerCertificate=yes"


class EmailSettings(BaseSettings):
    """Email (IMAP) settings"""
    model_config = SettingsConfigDict(
        env_prefix="EMAIL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    host: str = "imap.gmail.com"
    port: int = 993
    user: str = ""
    password: str = ""
    use_ssl: bool = True
    poll_interval: int = 60  # seconds


class MutluAkuSettings(BaseSettings):
    """Mutlu Akü portal settings"""
    model_config = SettingsConfigDict(
        env_prefix="MUTLU_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    portal_url: str = "https://mutlu.visionnext.com.tr/Prm/UserAccount/Login"
    username: str = ""  # Set via MUTLU_USERNAME env var
    password: str = ""  # Set via MUTLU_PASSWORD env var
    default_depo: str = "A. Merkez Depo"
    default_personel: str = "CASTROL DALAY"
    default_odeme_vadesi: str = "60 Gün"
    default_odeme_tipi: str = "Açık Hesap"
    default_fiyat_listesi: str = "Castrol Fiyat Listesi 25003"


class MannHummelSettings(BaseSettings):
    """Mann & Hummel (TecCom) portal settings"""
    model_config = SettingsConfigDict(
        env_prefix="MANN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    portal_url: str = "https://teccom.tecalliance.net/newapp/auth/welcome"
    username: str = ""  # Set via MANN_USERNAME env var
    password: str = ""  # Set via MANN_PASSWORD env var
    default_tedarikci: str = "FILTRON-MANN+HUMMEL Türkiye"


class RetrySettings(BaseSettings):
    """Retry configuration"""
    model_config = SettingsConfigDict(env_prefix="RETRY_")

    login_max_attempts: int = 3
    login_wait_seconds: List[int] = [5, 15, 30]

    navigation_max_attempts: int = 3
    navigation_wait_seconds: List[int] = [2, 5, 10]

    form_fill_max_attempts: int = 2
    form_fill_wait_seconds: List[int] = [3, 10]

    submit_max_attempts: int = 3
    submit_wait_seconds: List[int] = [5, 15, 30]


class NotificationSettings(BaseSettings):
    """Notification settings"""
    model_config = SettingsConfigDict(
        env_prefix="NOTIFY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    enabled: bool = True
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    recipients: List[str] = [
        "arif.ozelci@dorufinansal.com",
        "dilsad.kaptan@dorufinansal.com",
        "asim.koc@dorufinansal.com"
    ]
    throttle_minutes: int = 60  # Same error notification throttle


class PlaywrightSettings(BaseSettings):
    """Playwright browser settings"""
    model_config = SettingsConfigDict(env_prefix="PLAYWRIGHT_")

    headless: bool = True
    slow_mo: int = 100  # milliseconds between actions
    timeout: int = 30000  # default timeout in ms
    screenshot_on_error: bool = True
    screenshot_path: str = "screenshots"
    download_path: str = "downloads"


class LogSettings(BaseSettings):
    """Logging configuration"""
    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    path: str = "logs"
    rotation: str = "1 day"
    retention: str = "30 days"
    compression: str = "gz"


class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    app_name: str = "KolayRobot"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # JWT Auth - MUST be set via JWT_SECRET_KEY environment variable in production
    jwt_secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-RANDOM-64-CHAR-SECRET",
        description="JWT secret key - must be changed in production via JWT_SECRET_KEY env var"
    )

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    email: EmailSettings = Field(default_factory=EmailSettings)
    mutlu_aku: MutluAkuSettings = Field(default_factory=MutluAkuSettings)
    mann_hummel: MannHummelSettings = Field(default_factory=MannHummelSettings)
    retry: RetrySettings = Field(default_factory=RetrySettings)
    notification: NotificationSettings = Field(default_factory=NotificationSettings)
    playwright: PlaywrightSettings = Field(default_factory=PlaywrightSettings)
    log: LogSettings = Field(default_factory=LogSettings)


# Global settings instance
settings = Settings()
