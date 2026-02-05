"""
DoruMake Base Robot
Abstract base class for all supplier robots
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import uuid

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeout

from src.config import settings
from src.utils.logger import logger, robot_logger
from src.utils.retry import retry_async, RetryError
from src.db.models import Order, OrderStatus, OrderLog


class RobotStep(Enum):
    """Robot işlem adımları"""
    INIT = "INIT"
    LOGIN = "LOGIN"
    CUSTOMER_SELECT = "CUSTOMER_SELECT"
    MENU_NAVIGATE = "MENU_NAVIGATE"
    ORDER_CREATE = "ORDER_CREATE"
    FORM_FILL = "FORM_FILL"
    PRODUCTS_TAB = "PRODUCTS_TAB"
    PRODUCTS_SEARCH = "PRODUCTS_SEARCH"
    PRODUCTS_ADD = "PRODUCTS_ADD"
    PRODUCTS_SAVE = "PRODUCTS_SAVE"
    ORDER_SAVE = "ORDER_SAVE"
    ORDER_CONFIRM = "ORDER_CONFIRM"  # SAP
    FILE_UPLOAD = "FILE_UPLOAD"  # TecCom
    SUPPLIER_SELECT = "SUPPLIER_SELECT"  # TecCom
    REQUEST_SUBMIT = "REQUEST_SUBMIT"  # TecCom TALEP
    ORDER_SUBMIT = "ORDER_SUBMIT"  # TecCom SİPARİŞ
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class RobotError(Exception):
    """Robot hata sınıfı"""

    def __init__(
        self,
        message: str,
        step: RobotStep,
        screenshot_path: Optional[str] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.step = step
        self.screenshot_path = screenshot_path
        self.original_error = original_error
        self.timestamp = datetime.utcnow()


@dataclass
class RobotResult:
    """Robot işlem sonucu"""
    success: bool
    order_id: str
    portal_order_no: Optional[str] = None
    message: str = ""
    steps_completed: List[RobotStep] = field(default_factory=list)
    error: Optional[RobotError] = None
    screenshot_paths: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class BaseRobot(ABC):
    """
    Abstract base class for supplier robots

    Her tedarikçi robot'u bu sınıftan türemeli ve
    abstract metodları implement etmelidir.
    """

    # Subclass'ların override etmesi gereken değerler
    SUPPLIER_NAME: str = "Unknown"
    SUPPLIER_CODE: str = "UNKNOWN"
    PORTAL_URL: str = ""

    def __init__(self, order: Order, session: Any = None):
        """
        Initialize robot

        Args:
            order: İşlenecek sipariş
            session: Database session (opsiyonel)
        """
        self.order = order
        self.session = session
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        self.current_step: RobotStep = RobotStep.INIT
        self.steps_completed: List[RobotStep] = []
        self.screenshot_paths: List[str] = []
        self.logs: List[Dict[str, Any]] = []

        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        # Paths
        self.screenshot_dir = Path(settings.playwright.screenshot_path) / self.SUPPLIER_CODE.lower()
        self.download_dir = Path(settings.playwright.download_path)

    async def __aenter__(self):
        """Context manager entry"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.teardown()

    async def setup(self) -> None:
        """Browser ve context oluştur"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Setting up browser...")

        # Create directories
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Launch browser
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=settings.playwright.headless,
            slow_mo=settings.playwright.slow_mo
        )

        # Create context with download handling
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR"
        )

        # Set default timeout
        self.context.set_default_timeout(settings.playwright.timeout)

        # Create page
        self.page = await self.context.new_page()

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Browser setup complete")

    async def teardown(self) -> None:
        """Browser ve context temizle"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Tearing down browser...")

        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        except Exception as e:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Teardown error: {e}")

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Browser teardown complete")

    async def take_screenshot(self, name: str, is_error: bool = False) -> Optional[str]:
        """
        Screenshot al

        Args:
            name: Screenshot adı
            is_error: Hata durumu mu?

        Returns:
            Screenshot dosya yolu
        """
        if not self.page:
            return None

        # Sadece hata durumunda veya ayar açıksa screenshot al
        if not is_error and not settings.playwright.screenshot_on_error:
            return None

        try:
            timestamp = datetime.now().strftime("%H%M%S")
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"{self.order.order_code}_{name}_{timestamp}.png"

            # Create date subdirectory
            screenshot_path = self.screenshot_dir / date_str
            screenshot_path.mkdir(parents=True, exist_ok=True)

            full_path = screenshot_path / filename
            await self.page.screenshot(path=str(full_path), full_page=True)

            self.screenshot_paths.append(str(full_path))
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] Screenshot saved: {full_path}")

            return str(full_path)

        except Exception as e:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Screenshot failed: {e}")
            return None

    def log_step(
        self,
        step: RobotStep,
        status: str,
        message: str,
        details: Optional[Dict] = None,
        screenshot_path: Optional[str] = None
    ) -> None:
        """
        Adım logla - hem memory'e hem veritabanına kaydeder

        Args:
            step: İşlem adımı
            status: SUCCESS, FAILED, INFO, RETRY, PROCESSING
            message: Log mesajı
            details: Ek detaylar
            screenshot_path: Screenshot yolu
        """
        import json

        log_entry = {
            "id": str(uuid.uuid4()),
            "order_id": self.order.id,
            "action": step.value,
            "status": status,
            "message": message,
            "details": details,
            "screenshot_path": screenshot_path,
            "created_at": datetime.utcnow().isoformat()
        }

        self.logs.append(log_entry)

        # Console log
        log_func = robot_logger.info if status == "SUCCESS" else (
            robot_logger.error if status == "FAILED" else robot_logger.debug
        )
        log_func(f"[{self.SUPPLIER_NAME}] [{step.value}] {status}: {message}")

        # Save to database
        try:
            from src.db.sqlserver import db
            details_str = json.dumps(details) if details else None
            db.add_order_log(
                order_id=self.order.id,
                action=step.value,
                status=status,
                message=message,
                details=details_str,
                screenshot_path=screenshot_path
            )
        except Exception as e:
            robot_logger.warning(f"Could not save log to database: {e}")

    async def execute_step(
        self,
        step: RobotStep,
        func,
        operation_name: str,
        max_attempts: int = 3,
        wait_seconds: List[int] = [5, 15, 30],
        take_screenshot_on_error: bool = True
    ) -> Any:
        """
        Adımı retry ile çalıştır

        Args:
            step: İşlem adımı
            func: Çalıştırılacak async fonksiyon
            operation_name: İşlem adı (logging için)
            max_attempts: Maksimum deneme sayısı
            wait_seconds: Bekleme süreleri
            take_screenshot_on_error: Hata durumunda screenshot al

        Returns:
            Fonksiyon sonucu

        Raises:
            RobotError: Tüm denemeler başarısız olursa
        """
        self.current_step = step

        async def on_retry(attempt: int, error: Exception):
            self.log_step(step, "RETRY", f"Attempt {attempt} failed: {error}")
            if take_screenshot_on_error:
                await self.take_screenshot(f"{step.value}_retry_{attempt}", is_error=True)

        async def on_failure(error: Exception):
            screenshot_path = None
            if take_screenshot_on_error:
                screenshot_path = await self.take_screenshot(f"{step.value}_failed", is_error=True)
            self.log_step(step, "FAILED", str(error), screenshot_path=screenshot_path)

        try:
            result = await retry_async(
                func,
                max_attempts=max_attempts,
                wait_seconds=wait_seconds,
                exceptions=(Exception,),
                on_retry=on_retry,
                on_failure=on_failure,
                operation_name=f"{self.SUPPLIER_NAME}:{operation_name}"
            )

            self.steps_completed.append(step)
            self.log_step(step, "SUCCESS", f"{operation_name} completed")
            return result

        except RetryError as e:
            screenshot_path = self.screenshot_paths[-1] if self.screenshot_paths else None
            raise RobotError(
                message=str(e),
                step=step,
                screenshot_path=screenshot_path,
                original_error=e.last_exception
            )

    async def navigate_to_portal(self) -> None:
        """Portal'a git"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Navigating to {self.PORTAL_URL}")
        await self.page.goto(self.PORTAL_URL, wait_until="networkidle")

    async def wait_for_element(
        self,
        selector: str,
        timeout: int = None,
        state: str = "visible"
    ) -> Any:
        """
        Element bekle

        Args:
            selector: CSS/XPath selector
            timeout: Timeout (ms)
            state: visible, attached, detached, hidden

        Returns:
            Element handle
        """
        timeout = timeout or settings.playwright.timeout
        return await self.page.wait_for_selector(selector, timeout=timeout, state=state)

    async def click_element(self, selector: str, timeout: int = None) -> None:
        """Element'e tıkla"""
        element = await self.wait_for_element(selector, timeout)
        await element.click()

    async def fill_input(self, selector: str, value: str, timeout: int = None) -> None:
        """Input'a değer yaz"""
        element = await self.wait_for_element(selector, timeout)
        await element.fill(value)

    async def select_option(self, selector: str, value: str = None, label: str = None) -> None:
        """Dropdown'dan seçim yap"""
        if value:
            await self.page.select_option(selector, value=value)
        elif label:
            await self.page.select_option(selector, label=label)

    async def wait_for_navigation(self, timeout: int = None) -> None:
        """Sayfa yüklemesini bekle"""
        timeout = timeout or settings.playwright.timeout
        await self.page.wait_for_load_state("networkidle", timeout=timeout)

    async def wait_for_text(self, text: str, timeout: int = None) -> None:
        """Belirli text'in görünmesini bekle"""
        timeout = timeout or settings.playwright.timeout
        await self.page.wait_for_selector(f"text={text}", timeout=timeout)

    # ============================================
    # ABSTRACT METHODS - Subclass'lar implement etmeli
    # ============================================

    @abstractmethod
    async def login(self) -> None:
        """Portal'a giriş yap"""
        pass

    @abstractmethod
    async def process_order(self) -> RobotResult:
        """
        Sipariş işle

        Returns:
            RobotResult: İşlem sonucu
        """
        pass

    # ============================================
    # MAIN EXECUTION
    # ============================================

    async def run(self) -> RobotResult:
        """
        Robot'u çalıştır

        Returns:
            RobotResult: İşlem sonucu
        """
        self.start_time = datetime.utcnow()
        result = RobotResult(success=False, order_id=self.order.id)

        try:
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Starting order processing: {self.order.order_code}")

            # Log start
            self.log_step(
                RobotStep.INIT,
                "PROCESSING",
                f"Sipariş işleme başlatılıyor: {self.order.order_code}",
                details={"supplier": self.SUPPLIER_NAME, "portal": self.PORTAL_URL}
            )

            # Setup browser
            await self.setup()

            # Navigate to portal
            await self.navigate_to_portal()
            self.log_step(RobotStep.INIT, "SUCCESS", f"Portal açıldı: {self.PORTAL_URL}")

            # Process order (implemented by subclass)
            result = await self.process_order()

            self.end_time = datetime.utcnow()
            result.duration_seconds = (self.end_time - self.start_time).total_seconds()

            robot_logger.info(
                f"[{self.SUPPLIER_NAME}] Order processing completed: {self.order.order_code} "
                f"- Success: {result.success} - Duration: {result.duration_seconds:.2f}s"
            )

        except RobotError as e:
            self.end_time = datetime.utcnow()
            result.success = False
            result.error = e
            result.message = str(e)
            result.steps_completed = self.steps_completed
            result.screenshot_paths = self.screenshot_paths
            result.duration_seconds = (self.end_time - self.start_time).total_seconds()

            robot_logger.error(
                f"[{self.SUPPLIER_NAME}] Order processing failed at step {e.step.value}: {e}"
            )

        except Exception as e:
            self.end_time = datetime.utcnow()
            screenshot_path = await self.take_screenshot("unexpected_error", is_error=True)

            result.success = False
            result.error = RobotError(
                message=str(e),
                step=self.current_step,
                screenshot_path=screenshot_path,
                original_error=e
            )
            result.message = str(e)
            result.steps_completed = self.steps_completed
            result.screenshot_paths = self.screenshot_paths
            result.duration_seconds = (self.end_time - self.start_time).total_seconds()

            robot_logger.exception(f"[{self.SUPPLIER_NAME}] Unexpected error: {e}")

        finally:
            await self.teardown()

        return result
