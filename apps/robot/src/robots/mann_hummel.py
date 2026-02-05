"""
DoruMake Mann & Hummel Robot
TecCom Portal automation for Mann & Hummel orders via CSV upload
"""

import csv
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import TimeoutError as PlaywrightTimeout

from src.config import settings
from src.utils.logger import robot_logger
from src.db.models import Order, OrderItem

from .base import BaseRobot, RobotStep, RobotError, RobotResult


class MannHummelRobot(BaseRobot):
    """
    Mann & Hummel sipariş robotu

    TecCom portalına CSV dosyası yükleyerek sipariş oluşturur.
    6 adımlık basit bir süreç.
    """

    SUPPLIER_NAME = "Mann & Hummel"
    SUPPLIER_CODE = "MANN"
    PORTAL_URL = settings.mann_hummel.portal_url

    # Selectors
    SELECTORS = {
        # Login
        "username_input": "input[name='username'], input[id='username'], input[type='email'], input[type='text']",
        "password_input": "input[name='password'], input[id='password'], input[type='password']",
        "login_button": "button[type='submit'], input[type='submit'], .login-btn, button:has-text('Login')",

        # Menu
        "menu_query_order": "text=Sorgulama ve sipariş, text=Query and Order",
        "menu_file_upload": "text=Dosyayı yükle, text=Dosya Yükle, text=File Upload, text=Upload file",

        # File upload
        "file_input": "input[type='file']",
        "file_select_button": "text=Sipariş dosyasını seç, button:has-text('dosya'), button:has-text('Seç')",

        # Supplier selection
        "supplier_dropdown": "select:has-text('Tedarikçi'), [name*='supplier'], [id*='supplier']",
        "supplier_option": "text=FILTRON-MANN+HUMMEL Türkiye",

        # Customer selection (Sapma gösteren sevk yeri)
        "address_radio": "text=Sapma gösteren sevk yeri adresi kullan, input[type='radio'][value*='sapma']",
        "customer_dropdown": "select:has-text('Sevk'), [name*='customer'], [id*='address']",
        "customer_option": "text={customer_code}",

        # Submit buttons
        "request_button": "text=TALEP, button:has-text('TALEP'), button:has-text('Talep'), .btn-request",
        "order_button": "text=SİPARİŞ, button:has-text('SİPARİŞ'), button:has-text('Sipariş'), .btn-order",

        # Messages
        "order_number": ".order-number, [class*='order-no'], text=Sipariş No",
        "success_message": "text=Başarılı, text=Success, .success-message",
        "error_message": ".error-message, .alert-danger, text=Hata, text=Error",

        # Loading
        "loading": ".loading, .spinner, [class*='loading']"
    }

    def __init__(self, order: Order, order_items: List[OrderItem] = None, session: Any = None):
        super().__init__(order, session)
        self.order_items = order_items or []
        self.portal_order_no: Optional[str] = None
        self.csv_file_path: Optional[str] = None

    def generate_csv(self, items: List[Dict[str, Any]]) -> str:
        """
        TecCom formatında CSV dosyası oluştur

        CSV Format (Siparis_formu_TecOrder_2018.csv):
        - Sıra No | Parça Numarası | Miktar | Parça Adı

        Args:
            items: Ürün listesi [{"code": "AP 139/2", "quantity": 150}, ...]

        Returns:
            CSV dosya yolu
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Generating CSV file...")

        # Create temp file
        temp_dir = Path(self.download_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        csv_path = temp_dir / f"order_{self.order.order_code}.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')

            # Header (TecCom format)
            writer.writerow([
                "TecLocal/TecWeb Kanalı ile Sipariş Formu",
                "", "", ""
            ])
            writer.writerow([])  # Empty row
            writer.writerow([
                "Sıra No", "Parça Numarası", "Miktar", "Parça Adı"
            ])

            # Data rows
            for i, item in enumerate(items, 1):
                product_code = item.get("product_code") or item.get("code", "")
                quantity = item.get("quantity", 0)
                product_name = item.get("product_name") or item.get("name", "")

                if quantity > 0:
                    writer.writerow([
                        str(i),
                        product_code,
                        str(quantity),
                        product_name
                    ])

        self.csv_file_path = str(csv_path)
        robot_logger.info(f"[{self.SUPPLIER_NAME}] CSV file generated: {self.csv_file_path}")

        return self.csv_file_path

    async def login(self) -> None:
        """Portal'a giriş yap"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Logging in...")

        # Handle cookie consent popup if present
        try:
            # Try to click "Continue without consent" or similar button
            consent_selectors = [
                "button:has-text('Continue without consent')",
                "button:has-text('Ohne Zustimmung fortfahren')",
                "button:has-text('Accept All')",
                "button:has-text('Alle akzeptieren')",
                "button:has-text('Only required')",
                "a:has-text('Continue without consent')",
                ".privacy-consent-decline",
                "#onetrust-reject-all-handler",
                ".onetrust-close-btn-handler",
            ]
            for selector in consent_selectors:
                try:
                    consent_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if consent_btn:
                        await consent_btn.click()
                        robot_logger.info(f"[{self.SUPPLIER_NAME}] Dismissed cookie consent popup")
                        await self.page.wait_for_timeout(1000)
                        break
                except:
                    continue
        except Exception as e:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] No cookie popup found or error: {e}")

        # Wait for login form
        await self.wait_for_element(self.SELECTORS["username_input"])

        # Fill credentials
        await self.fill_input(self.SELECTORS["username_input"], settings.mann_hummel.username)
        await self.fill_input(self.SELECTORS["password_input"], settings.mann_hummel.password)

        # Click login
        await self.click_element(self.SELECTORS["login_button"])

        # Wait for navigation
        await self.wait_for_navigation()

        # Verify login success
        try:
            await self.page.wait_for_selector(self.SELECTORS["username_input"], state="hidden", timeout=5000)
        except PlaywrightTimeout:
            raise RobotError(
                message="Login failed - credentials may be invalid",
                step=RobotStep.LOGIN
            )

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Login successful")

    async def navigate_to_file_upload(self) -> None:
        """Dosya yükleme ekranına git"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Navigating to file upload...")

        # Click menu
        await self.click_element(self.SELECTORS["menu_query_order"])
        await self.page.wait_for_timeout(500)

        # Click file upload
        await self.click_element(self.SELECTORS["menu_file_upload"])

        # Wait for page load
        await self.wait_for_navigation()

        robot_logger.info(f"[{self.SUPPLIER_NAME}] File upload screen loaded")

    async def upload_csv_file(self, file_path: str) -> None:
        """
        CSV dosyası yükle

        Args:
            file_path: CSV dosya yolu
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Uploading CSV file: {file_path}")

        # Find file input (may be hidden)
        file_input = await self.page.query_selector(self.SELECTORS["file_input"])

        if file_input:
            # Direct file input
            await file_input.set_input_files(file_path)
        else:
            # Click file select button and handle file chooser
            async with self.page.expect_file_chooser() as fc_info:
                await self.click_element(self.SELECTORS["file_select_button"])

            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)

        # Wait for upload processing
        await self.page.wait_for_timeout(2000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] CSV file uploaded")

    async def select_supplier(self) -> None:
        """Tedarikçi seç (FILTRON-MANN+HUMMEL Türkiye)"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selecting supplier...")

        try:
            # Try dropdown selection
            await self.select_option(
                self.SELECTORS["supplier_dropdown"],
                label=settings.mann_hummel.default_tedarikci
            )
        except Exception:
            # Try clicking option directly
            await self.click_element(self.SELECTORS["supplier_option"])

        await self.page.wait_for_timeout(500)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Supplier selected")

    async def select_customer(self, customer_code: str) -> None:
        """
        Müşteri seç (Sapma gösteren sevk yeri adresi)

        Args:
            customer_code: Müşteri kodu (TRM56062 vb.)
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selecting customer: {customer_code}")

        # Click radio button for "Sapma gösteren sevk yeri adresi kullan"
        await self.click_element(self.SELECTORS["address_radio"])
        await self.page.wait_for_timeout(500)

        # Select customer from dropdown
        try:
            await self.select_option(
                self.SELECTORS["customer_dropdown"],
                label=customer_code
            )
        except Exception:
            # Try clicking option
            selector = self.SELECTORS["customer_option"].format(customer_code=customer_code)
            await self.click_element(selector)

        await self.page.wait_for_timeout(500)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer selected: {customer_code}")

    async def submit_request(self) -> None:
        """TALEP butonu - Sipariş yükleme"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Submitting request (TALEP)...")

        # Click TALEP button
        await self.click_element(self.SELECTORS["request_button"])

        # Wait for loading
        try:
            await self.page.wait_for_selector(self.SELECTORS["loading"], state="visible", timeout=2000)
            await self.page.wait_for_selector(self.SELECTORS["loading"], state="hidden", timeout=60000)
        except PlaywrightTimeout:
            pass  # Loading indicator may not appear

        # Wait additional time for processing
        await self.page.wait_for_timeout(3000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Request submitted")

    async def submit_order(self) -> str:
        """
        SİPARİŞ butonu - Sipariş onaylama

        Returns:
            Portal sipariş numarası
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Submitting order (SİPARİŞ)...")

        # Click SİPARİŞ button
        await self.click_element(self.SELECTORS["order_button"])

        # Wait for loading
        try:
            await self.page.wait_for_selector(self.SELECTORS["loading"], state="visible", timeout=2000)
            await self.page.wait_for_selector(self.SELECTORS["loading"], state="hidden", timeout=60000)
        except PlaywrightTimeout:
            pass

        # Wait for order number
        await self.page.wait_for_timeout(5000)

        # Try to extract order number
        try:
            order_element = await self.page.query_selector(self.SELECTORS["order_number"])
            if order_element:
                self.portal_order_no = await order_element.text_content()
                self.portal_order_no = self.portal_order_no.strip() if self.portal_order_no else None
        except Exception as e:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not extract order number: {e}")

        # Check for errors
        error_el = await self.page.query_selector(self.SELECTORS["error_message"])
        if error_el:
            error_text = await error_el.text_content()
            raise RobotError(
                message=f"Order submission failed: {error_text}",
                step=RobotStep.ORDER_SUBMIT
            )

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order submitted. Portal order: {self.portal_order_no}")
        return self.portal_order_no or "UNKNOWN"

    async def process_order(self) -> RobotResult:
        """
        Sipariş işleme ana akışı

        Returns:
            RobotResult: İşlem sonucu
        """
        result = RobotResult(success=False, order_id=self.order.id)

        try:
            # Prepare CSV file
            items = [
                {
                    "product_code": item.product_code,
                    "quantity": item.quantity,
                    "product_name": item.product_name
                }
                for item in self.order_items
            ]

            if not items:
                raise RobotError(
                    message="No items to process",
                    step=RobotStep.INIT
                )

            csv_path = self.generate_csv(items)

            # Step 1: Login
            await self.execute_step(
                RobotStep.LOGIN,
                self.login,
                "Login to TecCom portal",
                max_attempts=settings.retry.login_max_attempts,
                wait_seconds=settings.retry.login_wait_seconds
            )

            # Step 2: Navigate to file upload
            await self.execute_step(
                RobotStep.MENU_NAVIGATE,
                self.navigate_to_file_upload,
                "Navigate to file upload",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 3: Upload CSV file
            await self.execute_step(
                RobotStep.FILE_UPLOAD,
                lambda: self.upload_csv_file(csv_path),
                "Upload CSV file",
                max_attempts=settings.retry.submit_max_attempts,
                wait_seconds=settings.retry.submit_wait_seconds
            )

            # Step 4: Select supplier
            await self.execute_step(
                RobotStep.SUPPLIER_SELECT,
                self.select_supplier,
                "Select supplier",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 5: Select customer
            customer_code = "TRM56062"  # TODO: Get from order/mapping
            await self.execute_step(
                RobotStep.CUSTOMER_SELECT,
                lambda: self.select_customer(customer_code),
                "Select customer",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 6: Submit request (TALEP)
            await self.execute_step(
                RobotStep.REQUEST_SUBMIT,
                self.submit_request,
                "Submit request (TALEP)",
                max_attempts=settings.retry.submit_max_attempts,
                wait_seconds=settings.retry.submit_wait_seconds
            )

            # Step 7: Submit order (SİPARİŞ)
            portal_order_no = await self.execute_step(
                RobotStep.ORDER_SUBMIT,
                self.submit_order,
                "Submit order (SİPARİŞ)",
                max_attempts=settings.retry.submit_max_attempts,
                wait_seconds=settings.retry.submit_wait_seconds,
                take_screenshot_on_error=True
            )

            # Success!
            result.success = True
            result.portal_order_no = portal_order_no
            result.message = f"Order successfully processed. Portal order: {portal_order_no}"
            result.steps_completed = self.steps_completed
            result.screenshot_paths = self.screenshot_paths

            self.log_step(RobotStep.COMPLETE, "SUCCESS", result.message)

        except RobotError as e:
            result.success = False
            result.error = e
            result.message = str(e)
            result.steps_completed = self.steps_completed
            result.screenshot_paths = self.screenshot_paths

            self.log_step(RobotStep.FAILED, "FAILED", str(e), screenshot_path=e.screenshot_path)
            raise

        finally:
            # Cleanup CSV file
            if self.csv_file_path:
                try:
                    Path(self.csv_file_path).unlink(missing_ok=True)
                except:
                    pass

        return result
