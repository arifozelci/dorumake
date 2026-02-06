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

    # Selectors - Updated based on TecCom portal screenshots (2025-12-22)
    SELECTORS = {
        # Welcome page - Login button to start Okta flow (button text is "Log In" with space)
        "welcome_login_button": "button.log-in-button, button:has-text('Log In'), button:has-text('Login'), a:has-text('Log In')",

        # Login - Okta two-step login (login.tecalliance.net)
        "username_input": "input[name='identifier'], input[name='username'], input[id='idp-discovery-username'], input[id='okta-signin-username']",
        "next_button": "input[type='submit'][value='İleri'], input[type='submit'][value='Next'], button:has-text('İleri'), button:has-text('Next'), input.button-primary",
        "password_input": "input[name='credentials.passcode'], input[name='password'], input[id='okta-signin-password'], input[type='password']",
        "okta_login_button": "input[type='submit'][value='Oturum Aç'], input[type='submit'][value='Sign In'], button:has-text('Oturum'), button:has-text('Sign In'), input.button-primary",

        # Menu - "Sorgulama ve sipariş" expands to show submenu
        "menu_query_order": "text=Sorgulama ve sipariş, button:has-text('Sorgulama ve sipariş')",
        "menu_file_upload": "text=Dosyayı yükle, button:has-text('Dosyayı yükle')",
        "menu_file_upload_en": "text=Import Data File, button:has-text('Import Data File')",

        # File upload page - "Sipariş dosyası seç" button (blue)
        "file_input": "input[type='file']",
        "file_select_button": "text=Sipariş dosyası seç, button:has-text('Sipariş dosyası seç'), button:has-text('Dosyayı yükle')",

        # Supplier selection - dropdown shows "FILTRON-MANN+HUMMEL Türkiye"
        "supplier_dropdown": "select:near(text=Tedarikçi), [class*='select']:near(text=Tedarikçi)",
        "supplier_option": "text=FILTRON-MANN+HUMMEL Türkiye",

        # Customer selection (Sapma gösteren sevk yeri)
        # 1. First click radio: "Sapma gösteren sevk yeri adresini kullan:"
        # 2. Then select from "Sevk yeri" dropdown
        "address_radio_sapma": "text=Sapma gösteren sevk yeri adresini kullan",
        "address_radio_standard": "text=Standart teslimat adresini kullan",
        "customer_dropdown": "select:near(text=Sevk yeri), [class*='select']:near(text=Sevk yeri)",
        "customer_option": "text={customer_code}",

        # Product list (to check if CSV was processed)
        "product_list": "table:has-text('Ürün numarası'), .product-list, [class*='product'], [class*='grid']",

        # Submit buttons - TALEP first, then SİPARİŞ
        "request_button": "button:has-text('TALEP')",
        "order_button": "button:has-text('SİPARİŞ')",

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

        CSV Format: Original TecCom Siparis_formu_TecOrder_2018.csv structure:
        - Uses comma (,) as delimiter
        - ISO-8859-9 (Turkish Latin) encoding
        - leer prefix for empty/info rows
        - head prefix for header area
        - POS prefix for product/data rows
        - 8 columns total

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

        # TecCom format settings
        DELIMITER = ','
        ENCODING = 'iso-8859-9'
        PREFIX_EMPTY = 'leer'
        PREFIX_HEAD = 'head'
        PREFIX_DATA = 'POS'
        HEADER_TITLE = 'TecLocal/TecWeb Kanalıyla Sipariş Formu'

        def empty_row():
            return [PREFIX_EMPTY, '', '', '', '', '', '', '']

        with open(csv_path, 'w', newline='', encoding=ENCODING) as f:
            writer = csv.writer(f, delimiter=DELIMITER)

            # 5 empty leer rows
            for _ in range(5):
                writer.writerow(empty_row())

            # Title row
            writer.writerow([PREFIX_EMPTY, HEADER_TITLE, '', '', '', '', '', ''])

            # Empty row
            writer.writerow(empty_row())

            # Tracking number row
            writer.writerow([PREFIX_EMPTY, 'Siparişimiz için Belirlediğimiz Takip Numaramız',
                           'Kurumumuz Adına \nSipariş Veren Kişi', '', '', '', '', ''])

            # Head row
            writer.writerow([PREFIX_HEAD, '', '', '', '', '', '', ''])

            # 3 empty rows
            for _ in range(3):
                writer.writerow(empty_row())

            # Instruction rows
            writer.writerow([PREFIX_EMPTY, 'Kırmızı ile işaretli alanlar zorunludur,yoksa hata verir',
                           '', '', '', '', '', ''])
            writer.writerow([PREFIX_EMPTY, 'Bir seferde en fazla 750 kalem ürün için kullanılması uygundur',
                           '', '', '', '', '', ''])

            # Empty row
            writer.writerow(empty_row())

            # Column headers row
            writer.writerow([PREFIX_EMPTY, 'Sıra No', 'Parça No', 'Adet', '', '', '', 'Parça Adı'])

            # Data rows with POS prefix
            row_num = 1
            for item in items:
                product_code = item.get("product_code") or item.get("code", "")
                quantity = item.get("quantity", 0)
                product_name = item.get("product_name") or item.get("name", "")

                if quantity > 0:
                    writer.writerow([PREFIX_DATA, str(row_num), product_code, str(quantity),
                                   '', '', '', product_name])
                    row_num += 1

        self.csv_file_path = str(csv_path)
        robot_logger.info(f"[{self.SUPPLIER_NAME}] CSV file generated: {self.csv_file_path}")

        return self.csv_file_path

    async def login(self) -> None:
        """Portal'a giriş yap - Okta two-step login"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Logging in via Okta...")

        # Wait for welcome page to load
        await self.page.wait_for_timeout(2000)

        # Handle cookie consent popup if present
        try:
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
                    consent_btn = await self.page.wait_for_selector(selector, timeout=2000)
                    if consent_btn:
                        await consent_btn.click()
                        robot_logger.info(f"[{self.SUPPLIER_NAME}] Dismissed cookie consent popup")
                        await self.page.wait_for_timeout(1000)
                        break
                except:
                    continue
        except Exception as e:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] No cookie popup found: {e}")

        # Click Login button on welcome page to start Okta authentication flow
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicking Login button on welcome page...")
        try:
            login_btn = await self.page.wait_for_selector(
                self.SELECTORS["welcome_login_button"],
                timeout=10000,
                state="visible"
            )
            if login_btn:
                await login_btn.click()
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked Login button, waiting for Okta redirect...")
                # Wait for redirect to Okta login page
                await self.page.wait_for_timeout(5000)
        except Exception as e:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not find Login button, checking if already on Okta: {e}")

        # STEP 1: Enter username on Okta page
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Step 1: Entering username on Okta...")

        # Wait for username input field (Okta login page)
        username_input = await self.page.wait_for_selector(
            self.SELECTORS["username_input"],
            timeout=30000,
            state="visible"
        )
        if not username_input:
            raise RobotError(message="Username input not found", step=RobotStep.LOGIN)

        # Clear and fill username
        await username_input.fill("")
        await username_input.fill(settings.mann_hummel.username)
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Username entered: {settings.mann_hummel.username}")

        # Click "İleri" (Next) button
        await self.page.wait_for_timeout(500)
        next_btn = await self.page.wait_for_selector(
            self.SELECTORS["next_button"],
            timeout=5000,
            state="visible"
        )
        if next_btn:
            await next_btn.click()
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked Next button")
        else:
            # Try pressing Enter
            await username_input.press("Enter")
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Pressed Enter to proceed")

        # Wait for password page to load
        await self.page.wait_for_timeout(3000)

        # STEP 2: Enter password
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Step 2: Entering password...")

        # Wait for password input field
        password_input = await self.page.wait_for_selector(
            self.SELECTORS["password_input"],
            timeout=30000,
            state="visible"
        )
        if not password_input:
            raise RobotError(message="Password input not found", step=RobotStep.LOGIN)

        # Fill password
        await password_input.fill(settings.mann_hummel.password)
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Password entered")

        # Click "Oturum Aç" (Sign In) button
        await self.page.wait_for_timeout(500)
        okta_login_btn = await self.page.wait_for_selector(
            self.SELECTORS["okta_login_button"],
            timeout=5000,
            state="visible"
        )
        if okta_login_btn:
            await okta_login_btn.click()
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked Sign In button")
        else:
            # Try pressing Enter
            await password_input.press("Enter")
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Pressed Enter to login")

        # Wait for redirect back to TecCom portal
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Waiting for redirect to portal...")
        await self.page.wait_for_timeout(5000)

        # Verify login success - should be redirected back to teccom
        current_url = self.page.url
        if "login.tecalliance.net" in current_url:
            # Still on login page - check for error
            error_el = await self.page.query_selector(".okta-form-infobox-error, .o-form-error-container")
            if error_el:
                error_text = await error_el.text_content()
                raise RobotError(
                    message=f"Login failed: {error_text}",
                    step=RobotStep.LOGIN
                )
            raise RobotError(
                message="Login failed - still on login page",
                step=RobotStep.LOGIN
            )

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Login successful! Redirected to: {current_url}")

    async def navigate_to_file_upload(self) -> None:
        """Dosya yükleme ekranına git"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Navigating to file upload...")

        # First, close any popup dialogs (e.g., "Yenilikler" news popup)
        try:
            popup_close_selectors = [
                "button:has-text('Kapat')",
                "button:has-text('Close')",
                "button:has-text('OK')",
                ".mat-dialog-container button.mat-button",
                "mat-dialog-actions button",
                "[mat-dialog-close]",
                ".cdk-overlay-backdrop",
            ]
            for selector in popup_close_selectors:
                try:
                    popup_btn = await self.page.wait_for_selector(selector, timeout=3000)
                    if popup_btn:
                        await popup_btn.click()
                        robot_logger.info(f"[{self.SUPPLIER_NAME}] Closed popup dialog")
                        await self.page.wait_for_timeout(1000)
                        break
                except:
                    continue
        except Exception as e:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] No popup to close: {e}")

        # Wait for page to stabilize
        await self.page.wait_for_timeout(2000)

        # Try multiple approaches to get to file upload
        # Approach 1: Click the blue "Dosyayı yükle" button with + icon (if on order form page)
        dosya_yukle_selectors = [
            "button:has-text('Dosyayı yükle')",
            "text=Dosyayı yükle >> visible=true",
            ".btn:has-text('Dosyayı yükle')",
            "[class*='upload']:has-text('Dosyayı yükle')",
        ]

        for selector in dosya_yukle_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=3000, state="visible")
                if btn:
                    await btn.click()
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked 'Dosyayı yükle' button directly")
                    await self.page.wait_for_timeout(1000)

                    # Handle "Değişiklikler iptal edilsin mi?" dialog
                    try:
                        discard_dialog_selectors = [
                            "button:has-text('Evet')",
                            "text=Evet >> visible=true",
                            ".btn:has-text('Evet')",
                        ]
                        for discard_selector in discard_dialog_selectors:
                            try:
                                discard_btn = await self.page.wait_for_selector(discard_selector, timeout=3000, state="visible")
                                if discard_btn:
                                    await discard_btn.click()
                                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked 'Evet' to discard previous changes")
                                    await self.page.wait_for_timeout(1000)
                                    break
                            except:
                                continue
                    except Exception as e:
                        robot_logger.debug(f"[{self.SUPPLIER_NAME}] No discard dialog: {e}")

                    return
            except:
                continue

        # Approach 2: Navigate via menu
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Trying menu navigation...")

        # Click Request & Order menu to expand it
        menu_selectors = [
            "text=Sorgulama ve sipariş",
            "button:has-text('Sorgulama ve sipariş')",
            "[class*='menu']:has-text('Sorgulama')",
        ]

        menu_clicked = False
        for selector in menu_selectors:
            try:
                menu = await self.page.wait_for_selector(selector, timeout=5000)
                if menu:
                    await menu.click()
                    menu_clicked = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked Request & Order menu")
                    await self.page.wait_for_timeout(1000)
                    break
            except:
                continue

        if not menu_clicked:
            raise RobotError(
                message="Could not find 'Sorgulama ve sipariş' menu",
                step=RobotStep.MENU_NAVIGATE
            )

        # Now look for file upload option in the expanded menu
        submenu_selectors = [
            "text=Dosyayı yükle",
            "a:has-text('Dosyayı yükle')",
            "button:has-text('Dosyayı yükle')",
            "[class*='submenu'] >> text=Dosyayı yükle",
        ]

        for selector in submenu_selectors:
            try:
                submenu = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                if submenu:
                    await submenu.click()
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked 'Dosyayı yükle' submenu")
                    break
            except:
                continue

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

        # Wait for page to stabilize after navigation
        await self.page.wait_for_timeout(2000)

        # Try multiple selectors for the file select button
        file_btn_selectors = [
            "text=Sipariş dosyası seç",
            "button:has-text('Sipariş dosyası seç')",
            ".btn:has-text('Sipariş')",
            "button:has-text('Select Order File')",
        ]

        clicked = False
        for selector in file_btn_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                if btn:
                    await btn.click()
                    clicked = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked file select button: {selector}")
                    break
            except:
                continue

        if not clicked:
            raise RobotError(
                message="Could not find 'Sipariş dosyası seç' button",
                step=RobotStep.FILE_UPLOAD
            )

        await self.page.wait_for_timeout(1000)

        # Handle "Discard changes?" dialog if it appears
        try:
            discard_btn = await self.page.wait_for_selector(
                "button:has-text('Evet'), button:has-text('Yes')",
                timeout=3000,
                state="visible"
            )
            if discard_btn:
                await discard_btn.click()
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked Yes to discard previous data")
                await self.page.wait_for_timeout(1000)
        except:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] No discard dialog appeared")

        # Now handle the file chooser
        # Find file input (may be hidden)
        file_input = await self.page.query_selector(self.SELECTORS["file_input"])

        if file_input:
            # Direct file input available
            await file_input.set_input_files(file_path)
            robot_logger.info(f"[{self.SUPPLIER_NAME}] File set via input element")
        else:
            # Need to click button again and handle file chooser
            try:
                async with self.page.expect_file_chooser(timeout=10000) as fc_info:
                    await self.click_element(self.SELECTORS["file_select_button"])

                file_chooser = await fc_info.value
                await file_chooser.set_files(file_path)
                robot_logger.info(f"[{self.SUPPLIER_NAME}] File set via file chooser")
            except Exception as e:
                # Try looking for hidden input as fallback
                robot_logger.warning(f"[{self.SUPPLIER_NAME}] File chooser failed, trying hidden input: {e}")
                file_input = await self.page.query_selector("input[type='file']")
                if file_input:
                    await file_input.set_input_files(file_path)

        # Wait for upload processing
        await self.page.wait_for_timeout(3000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] CSV file uploaded")

    async def select_supplier(self) -> None:
        """Tedarikçi seç (FILTRON-MANN+HUMMEL Türkiye)"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selecting supplier...")

        # Wait for page to load after CSV upload
        await self.page.wait_for_timeout(2000)

        supplier_name = settings.mann_hummel.default_tedarikci

        # Try multiple approaches to select supplier
        # Approach 1: Click the dropdown to open it, then select option
        dropdown_selectors = [
            "select:near(:text('Tedarikçi'))",
            "[class*='select']:near(:text('Tedarikçi'))",
            "div:near(:text('Tedarikçi')) >> select",
            "select >> nth=0",  # First select on page
        ]

        selected = False
        for dropdown_sel in dropdown_selectors:
            try:
                dropdown = await self.page.wait_for_selector(dropdown_sel, timeout=5000)
                if dropdown:
                    # Try to select by label
                    await dropdown.select_option(label=supplier_name)
                    selected = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Supplier selected via dropdown: {dropdown_sel}")
                    break
            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Dropdown selector failed: {dropdown_sel} - {e}")
                continue

        if not selected:
            # Approach 2: Click the dropdown area to open, then click option
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Trying click approach for supplier...")
            try:
                # Click the Tedarikçi dropdown area
                tedarikci_area = await self.page.wait_for_selector(
                    "text=Tedarikçi >> .. >> select, div:has-text('Tedarikçi') >> select",
                    timeout=5000
                )
                if tedarikci_area:
                    await tedarikci_area.click()
                    await self.page.wait_for_timeout(500)

                    # Now click the supplier option
                    option = await self.page.wait_for_selector(f"text={supplier_name}", timeout=5000)
                    if option:
                        await option.click()
                        selected = True
                        robot_logger.info(f"[{self.SUPPLIER_NAME}] Supplier selected via click")
            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Click approach failed: {e}")

        if not selected:
            # Approach 3: Use page.select_option with various selectors
            for sel in ["select", "select.form-control", "[name*='supplier']", "[id*='supplier']"]:
                try:
                    await self.page.select_option(sel, label=supplier_name)
                    selected = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Supplier selected via page.select_option: {sel}")
                    break
                except:
                    continue

        if not selected:
            raise RobotError(
                message=f"Could not select supplier: {supplier_name}",
                step=RobotStep.SUPPLIER_SELECT
            )

        await self.page.wait_for_timeout(1000)
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Supplier selection completed")

    async def select_customer(self, customer_code: str) -> None:
        """
        Müşteri seç (Sapma gösteren sevk yeri adresi) - ZORUNLU ADIM

        PDF'e göre akış:
        1. "Sapma gösteren sevk yeri adresini kullan:" radio butonuna tıkla
        2. "Sevk yeri" dropdown'ından müşteriyi seç
        3. Müşteri kodu "Numara" alanında görünür

        Args:
            customer_code: Müşteri kodu (TRM56018, TRM56062 vb.)
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selecting customer: {customer_code}")

        # Wait for page to stabilize after supplier selection
        await self.page.wait_for_timeout(2000)

        # STEP 1: Click "Sapma gösteren sevk yeri adresini kullan:" radio button
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Step 1: Clicking 'Sapma gösteren' radio button...")

        radio_selectors = [
            "text=Sapma gösteren sevk yeri adresini kullan",
            "label:has-text('Sapma gösteren sevk yeri')",
            "input[type='radio'] >> nth=1",  # Second radio button (first is Standart teslimat)
            "//input[@type='radio']/following-sibling::*[contains(text(),'Sapma')]",
        ]

        clicked = False
        for selector in radio_selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=5000, state="visible")
                if element:
                    await element.click()
                    clicked = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked 'Sapma gösteren' radio with: {selector}")
                    break
            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Radio selector failed: {selector} - {e}")
                continue

        if not clicked:
            # Take screenshot and raise error
            raise RobotError(
                message="Could not find 'Sapma gösteren sevk yeri' radio button",
                step=RobotStep.CUSTOMER_SELECT
            )

        # Wait for "Sevk yeri" dropdown to appear
        await self.page.wait_for_timeout(1500)

        # STEP 2: Select customer from "Sevk yeri" dropdown
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Step 2: Selecting customer from 'Sevk yeri' dropdown...")

        # The dropdown contains customer names like "DALAY PETROL ÜRÜNLERİ NAKLİYE SAN., 72000"
        # We need to find the option that contains the customer code (TRM56018)
        dropdown_selectors = [
            "select:near(:text('Sevk yeri'))",
            "[class*='select']:near(:text('Sevk yeri'))",
            "select >> nth=1",  # Second select on page (first is Tedarikçi)
        ]

        selected = False
        for dropdown_selector in dropdown_selectors:
            try:
                # First try to click the dropdown to open it
                dropdown = await self.page.wait_for_selector(dropdown_selector, timeout=5000)
                if dropdown:
                    await dropdown.click()
                    await self.page.wait_for_timeout(500)

                    # Look for option containing customer code or name
                    option_selectors = [
                        f"option:has-text('{customer_code}')",
                        f"text={customer_code}",
                        "option >> nth=0",  # First option if only one customer
                    ]

                    for opt_selector in option_selectors:
                        try:
                            option = await self.page.wait_for_selector(opt_selector, timeout=3000)
                            if option:
                                await option.click()
                                selected = True
                                robot_logger.info(f"[{self.SUPPLIER_NAME}] Selected customer option with: {opt_selector}")
                                break
                        except:
                            continue

                    if selected:
                        break
            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Dropdown selector failed: {dropdown_selector} - {e}")
                continue

        if not selected:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not select customer {customer_code} from dropdown, trying direct text click...")
            # Try clicking any element containing customer code
            try:
                await self.page.click(f"text={customer_code}")
                selected = True
            except:
                pass

        await self.page.wait_for_timeout(1000)

        # Verify selection by checking "Numara" field
        try:
            numara_field = await self.page.query_selector(f"text={customer_code}")
            if numara_field:
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer code {customer_code} verified in Numara field")
        except:
            pass

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer selection completed")

    async def submit_request(self) -> None:
        """TALEP butonu - Sipariş yükleme"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Submitting request (TALEP)...")

        # Click TALEP button - try multiple selectors
        talep_selectors = [
            "button:has-text('TALEP')",
            "text=TALEP",
            "button >> text=TALEP",
            "[class*='button']:has-text('TALEP')",
        ]

        clicked = False
        for selector in talep_selectors:
            try:
                await self.page.wait_for_selector(selector, state="visible", timeout=3000)
                await self.page.click(selector)
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked TALEP button with: {selector}")
                clicked = True
                break
            except PlaywrightTimeout:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] TALEP selector not found: {selector}")
                continue

        if not clicked:
            raise RobotError(message="Could not find TALEP button", step=RobotStep.REQUEST_SUBMIT)

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

        # Wait for page to settle after TALEP
        await self.page.wait_for_timeout(2000)

        # Log all visible buttons for debugging
        try:
            buttons = await self.page.query_selector_all("button")
            button_texts = []
            for btn in buttons:
                text = await btn.text_content()
                if text:
                    button_texts.append(text.strip())
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Visible buttons on page: {button_texts[:20]}")
        except Exception as e:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] Could not enumerate buttons: {e}")

        # Click SİPARİŞ button - try multiple selectors with different variations
        # PDF'e göre: TALEP yanında, sağ üst köşede, Alışveriş sepeti yöneticisi solunda
        siparis_selectors = [
            # Exact text matches (Turkish characters)
            "button:has-text('SİPARİŞ')",
            "button:has-text('SIPARIS')",  # Without Turkish İ
            "button:has-text('Sipariş')",
            "button:has-text('Siparis')",  # Without Turkish ş
            # Text-only selectors
            "text=SİPARİŞ",
            "text=SIPARIS",
            "text=Sipariş",
            # Near TALEP button (they're side by side per PDF)
            "button:near(button:has-text('TALEP')):has-text('SİPARİŞ')",
            "button:right-of(button:has-text('TALEP'))",
            # Look for any button with partial match
            "*:has-text('SİPARİŞ')",
            "*:has-text('SIPARIS')",
            # Div or span that might contain the text
            "div:has-text('SİPARİŞ')",
            "span:has-text('SİPARİŞ')",
            # Case insensitive approach with regex
            "button:text-matches('sipari', 'i')",
            "button:text-matches('SIPARI', 'i')",
            # Data attributes
            "[data-test-id*='order']",
            "[data-test-id*='siparis']",
            "[data-test*='siparis']",
            # Class-based
            "[class*='order-button']",
            "[class*='siparis']",
            "button.btn-danger",  # Red button per PDF
            "button.btn-warning",
        ]

        clicked = False
        for selector in siparis_selectors:
            try:
                await self.page.wait_for_selector(selector, state="visible", timeout=2000)
                await self.page.click(selector)
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked SİPARİŞ button with: {selector}")
                clicked = True
                break
            except PlaywrightTimeout:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] SİPARİŞ selector not found: {selector}")
                continue

        if not clicked:
            # Log page HTML for debugging
            try:
                # Find all elements with "sipari" text (case insensitive)
                all_elements = await self.page.query_selector_all("*")
                siparis_elements = []
                for el in all_elements[:500]:  # Limit to first 500 elements
                    try:
                        text = await el.text_content()
                        tag = await el.evaluate("el => el.tagName")
                        if text and ("sipari" in text.lower() or "order" in text.lower()):
                            class_name = await el.evaluate("el => el.className")
                            siparis_elements.append(f"{tag}.{class_name}: {text[:50]}")
                    except:
                        continue
                robot_logger.error(f"[{self.SUPPLIER_NAME}] Elements containing 'sipari/order': {siparis_elements[:10]}")

                # Also log the page URL for context
                current_url = self.page.url
                robot_logger.error(f"[{self.SUPPLIER_NAME}] Current page URL: {current_url}")
            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Could not log page elements: {e}")

            raise RobotError(message="Could not find SİPARİŞ button", step=RobotStep.ORDER_SUBMIT)

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

            # Step 5: Select customer (REQUIRED - Sapma gösteren sevk yeri)
            # Get customer code from customer relationship or use default mapping
            # TRM56018 = DALAY PETROL (Batman) - default for Mann & Hummel
            customer_code = "TRM56018"  # Default to DALAY PETROL
            if self.order.customer:
                # Try to get the supplier-specific customer code from mapping
                # For now, use customer.code as fallback
                customer_code = getattr(self.order.customer, 'code', customer_code) or customer_code
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Using customer code: {customer_code}")

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
