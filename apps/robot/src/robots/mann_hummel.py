"""
KolayRobot Mann & Hummel Robot
TecCom Portal automation for Mann & Hummel orders via CSV upload
"""

import csv
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional
from playwright.async_api import TimeoutError as PlaywrightTimeout

from src.config import settings
from src.utils.logger import robot_logger
from src.db.models import Order, OrderItem

from .base import BaseRobot, RobotStep, RobotError, RobotResult


def _normalize_turkish(text: str) -> str:
    """Normalize Turkish characters to ASCII for matching.

    TecCom portal stores customer names in ASCII (e.g. VEDI OZTOPRAK)
    but Excel uses Turkish chars (e.g. VEDİ ÖZTOPRAK). This function
    normalizes both to a common form for reliable comparison.
    """
    tr_map = str.maketrans(
        "çÇğĞıİöÖşŞüÜ",
        "cCgGiIoOsSuU",
    )
    return text.translate(tr_map).upper()


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

        # Submit buttons - TALEP first, then SİPARİŞ (mixed case on actual portal: "Talep", "Sipariş")
        "request_button": "button:has-text('Talep')",
        "order_button": "button:has-text('Sipariş')",

        # Messages - single selectors only (Playwright doesn't support comma-separated)
        "order_number": "[class*='order']",
        "success_message": ".success-message",
        "error_message": ".error-message",

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
                product_name = (item.get("product_name") or item.get("name", ""))[:40]

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

    async def select_customer(self, customer_name: str) -> None:
        """
        Müşteri seç (Sapma gösteren sevk yeri adresi) - ZORUNLU ADIM

        TecCom dropdown shows customer names with city, e.g.:
        "HNR OTOM. PETROL İNŞ. NAKL. TUR SAN, 21070, Diyarbakır"
        We match using the first few words of the customer name from the Excel.

        Args:
            customer_name: Excel'den gelen müşteri adı
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selecting customer: {customer_name}")

        # Wait for page to stabilize after supplier selection
        await self.page.wait_for_timeout(2000)

        # STEP 1: Click "Sapma gösteren sevk yeri adresini kullan:" radio button
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Step 1: Clicking 'Sapma gösteren' radio button...")

        radio_selectors = [
            "text=Sapma gösteren sevk yeri adresini kullan",
            "label:has-text('Sapma gösteren sevk yeri')",
            "input[type='radio'] >> nth=1",
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
            raise RobotError(
                message="Could not find 'Sapma gösteren sevk yeri' radio button",
                step=RobotStep.CUSTOMER_SELECT
            )

        # Wait for "Sevk yeri" dropdown to appear
        await self.page.wait_for_timeout(1500)

        # STEP 2: Select customer from "Sevk yeri" dropdown
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Step 2: Selecting customer from 'Sevk yeri' dropdown...")

        # Build search keywords from customer_name
        search_terms = []
        if customer_name:
            clean_name = customer_name.split('(')[0].strip()
            words = clean_name.split()
            if len(words) >= 2:
                search_terms.append(' '.join(words[:2]))
            if len(words) >= 1:
                search_terms.append(words[0])
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer search terms: {search_terms}")

        # Find the "Sevk yeri" dropdown
        dropdown_selectors = [
            "select[name='shipTo']",
            "select:near(:text('Sevk yeri'))",
            "div:near(:text('Sevk yeri')) >> select",
            "[class*='select']:near(:text('Sevk yeri'))",
        ]

        selected = False
        for dropdown_selector in dropdown_selectors:
            try:
                dropdown = await self.page.wait_for_selector(dropdown_selector, timeout=5000)
                if not dropdown:
                    continue

                # Get all options in the dropdown
                options = await dropdown.evaluate("""
                    (el) => Array.from(el.options).map((opt, i) => ({
                        index: i,
                        value: opt.value,
                        text: opt.textContent.trim()
                    }))
                """)
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Dropdown has {len(options)} options")

                # Find matching option by customer name (Turkish-normalized)
                matched_option = None
                for term in search_terms:
                    term_norm = _normalize_turkish(term)
                    for opt in options:
                        opt_norm = _normalize_turkish(opt['text'])
                        if term_norm in opt_norm:
                            matched_option = opt
                            robot_logger.info(f"[{self.SUPPLIER_NAME}] Matched customer: '{opt['text']}' with term '{term}' (normalized: '{term_norm}' in '{opt_norm}')")
                            break
                    if matched_option:
                        break

                if matched_option:
                    await dropdown.select_option(value=matched_option['value'])
                    selected = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Selected customer: {matched_option['text']}")
                    break
                else:
                    robot_logger.warning(f"[{self.SUPPLIER_NAME}] No matching customer in dropdown for: {search_terms}")
                    option_names = [opt['text'][:60] for opt in options[:25]]
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Available customers: {option_names}")

            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Dropdown selector failed: {dropdown_selector} - {e}")
                continue

        if not selected:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not select customer from dropdown, trying text click with normalized terms...")
            for term in search_terms:
                try:
                    # Try normalized version for text click
                    norm_term = _normalize_turkish(term)
                    await self.page.click(f"text={norm_term}", timeout=3000)
                    selected = True
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Selected customer via text click: {norm_term}")
                    break
                except:
                    try:
                        await self.page.click(f"text={term}", timeout=3000)
                        selected = True
                        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selected customer via text click: {term}")
                        break
                    except:
                        continue

        if not selected:
            raise RobotError(
                message=f"Could not select customer: {customer_name} (search terms: {search_terms})",
                step=RobotStep.CUSTOMER_SELECT
            )

        await self.page.wait_for_timeout(1000)
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer selection completed (selected={selected})")

    async def submit_request(self) -> None:
        """TALEP butonu - Sipariş yükleme

        After clicking TALEP, the portal processes the CSV and loads product details.
        This can take seconds to minutes depending on the number of products.
        We must wait until the content fully loads before proceeding to SİPARİŞ.
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Submitting request (TALEP)...")

        # Click TALEP button - use data-test-id (most reliable), fallback to text
        talep_selectors = [
            "[data-test-id='requestButton']",
            "button:has-text('TALEP')",
            "button:has-text('Talep')",
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

        # Wait for the page to fully load after TALEP
        # TALEP triggers server-side processing of CSV - this can take minutes for large orders
        # We must wait until the product content appears on screen
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Waiting for TALEP to process and content to load...")

        # Strategy 1: Wait for network to settle (all XHR/fetch requests complete)
        try:
            await self.page.wait_for_load_state("networkidle", timeout=120000)
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Network is idle after TALEP")
        except PlaywrightTimeout:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Network idle timeout after 120s, continuing...")

        # Strategy 2: Poll for content changes - wait for product table/data to appear
        # TecCom shows product details (Ürün numarası, prices, quantities) after TALEP
        content_loaded = False
        content_selectors = [
            "table",                          # Any table (product list)
            "[class*='product']",             # Product-related elements
            "[class*='grid']",                # Grid layout for products
            "[class*='article']",             # Article/product entries
            "tr:has-text('Ürün')",            # Table row with product text
            "[class*='item']",                # Item elements
            "[class*='result']",              # Result elements
        ]

        max_wait = 120  # seconds
        poll_interval = 2  # seconds
        elapsed = 0

        while elapsed < max_wait and not content_loaded:
            for selector in content_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            robot_logger.info(f"[{self.SUPPLIER_NAME}] Content loaded - found: {selector} (after {elapsed}s)")
                            content_loaded = True
                            break
                except Exception:
                    continue

            if not content_loaded:
                await self.page.wait_for_timeout(poll_interval * 1000)
                elapsed += poll_interval
                if elapsed % 10 == 0:
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Still waiting for content... ({elapsed}s)")

        if not content_loaded:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Content indicators not found after {max_wait}s, proceeding anyway")

        # Extra settle time after content appears
        await self.page.wait_for_timeout(2000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] TALEP processing complete, ready for SİPARİŞ")

    async def submit_order(self) -> str:
        """
        SİPARİŞ butonu - Sipariş onaylama

        After TALEP, the page shows request reference (e.g. "1").
        Clicking SİPARİŞ converts the request to an actual order
        and generates a real order number starting with "110...".

        Returns:
            Portal sipariş numarası (110xxx format)
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Submitting order (SİPARİŞ)...")

        # Take screenshot before SİPARİŞ to see TALEP result
        try:
            await self.take_screenshot("before_siparis")
        except Exception:
            pass

        # Click SİPARİŞ button - use data-test-id (most reliable), fallback to text
        siparis_selectors = [
            "[data-test-id='orderButton']",
            "button:has-text('SİPARİŞ')",
            "button:has-text('Sipariş')",
            "button:has-text('SIPARIS')",
        ]

        clicked = False
        for selector in siparis_selectors:
            try:
                await self.page.wait_for_selector(selector, state="visible", timeout=3000)
                await self.page.click(selector)
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Clicked SİPARİŞ button with: {selector}")
                clicked = True
                break
            except PlaywrightTimeout:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] SİPARİŞ selector not found: {selector}")
                continue

        if not clicked:
            raise RobotError(message="Could not find SİPARİŞ button", step=RobotStep.ORDER_SUBMIT)

        # Wait for SİPARİŞ to be processed - this converts TALEP to actual order
        # The order number (110xxx) should appear on the page
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Waiting for SİPARİŞ to process and order number to appear...")

        # Wait for network to settle
        try:
            await self.page.wait_for_load_state("networkidle", timeout=120000)
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Network is idle after SİPARİŞ")
        except PlaywrightTimeout:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Network idle timeout after 120s after SİPARİŞ")

        # Poll for real order number to appear on the page
        # After TALEP, "Tedarikçi sipariş referansı" shows "1" (just a request number)
        # After SİPARİŞ, this field should change to a real order number (e.g. 110xxx, 600xxx, etc.)
        # Key: the real order number is NOT "1" - it's a multi-digit number
        import re
        order_number = None
        max_wait = 180  # seconds - can take minutes for large orders
        poll_interval = 2  # seconds
        elapsed = 0

        while elapsed < max_wait and not order_number:
            try:
                body_text = await self.page.evaluate("() => document.body.innerText")

                # Look for "Tedarikçi sipariş referansı" with a real order number (not "1")
                patterns = [
                    r'[Tt]edarik[çc]i\s+sipari[şs]\s+referans[ıi]\s*[\n:]*\s*(\d{2,})',
                    r'[Ss]ipari[şs]\s*[Rr]eferans[ıi]\s*[\n:]*\s*(\d{2,})',
                ]

                for pattern in patterns:
                    match = re.search(pattern, body_text)
                    if match:
                        ref = match.group(1).strip()
                        # Must be at least 2 digits (not just "1" which is TALEP reference)
                        if ref and ref != "1":
                            order_number = ref
                            robot_logger.info(f"[{self.SUPPLIER_NAME}] Found order number: {order_number} (after {elapsed}s)")
                            break
            except Exception as e:
                robot_logger.debug(f"[{self.SUPPLIER_NAME}] Error checking for order number: {e}")

            if not order_number:
                await self.page.wait_for_timeout(poll_interval * 1000)
                elapsed += poll_interval
                if elapsed % 10 == 0:
                    robot_logger.info(f"[{self.SUPPLIER_NAME}] Still waiting for real order number (not '1')... ({elapsed}s)")

        # Take screenshot after SİPARİŞ
        try:
            screenshot_path = await self.take_screenshot("after_siparis")
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Screenshot after SİPARİŞ: {screenshot_path}")
        except Exception as e:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] Could not take screenshot: {e}")

        # Log page content for debugging
        try:
            body_text = await self.page.evaluate("() => document.body.innerText")
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Page content after SİPARİŞ (first 2000 chars): {body_text[:2000]}")
        except Exception as e:
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] Could not get page text: {e}")

        if order_number:
            self.portal_order_no = order_number
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Order submitted successfully. Portal order: {self.portal_order_no}")
        else:
            # Fallback: try to get any reference from the page that isn't "1"
            try:
                body_text = await self.page.evaluate("() => document.body.innerText")
                fallback_patterns = [
                    r'[Tt]edarik[çc]i\s+sipari[şs]\s+referans[ıi]\s*[\n:]*\s*(\S+)',
                    r'[Ss]ipari[şs]\s*[Nn]o[:\s]*(\d+)',
                ]
                for pattern in fallback_patterns:
                    match = re.search(pattern, body_text)
                    if match:
                        ref = match.group(1).strip()
                        if ref and ref != "1" and len(ref) < 50:
                            self.portal_order_no = ref
                            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Fallback order reference: {ref}")
                            break
            except Exception:
                pass

            if not self.portal_order_no:
                robot_logger.error(f"[{self.SUPPLIER_NAME}] Could not find real order number after {max_wait}s - still showing TALEP reference")

        # Check for errors
        error_selectors = [".error-message", ".alert-danger", "[class*='error']"]
        for selector in error_selectors:
            try:
                error_el = await self.page.query_selector(selector)
                if error_el:
                    error_text = await error_el.text_content()
                    if error_text and ("hata" in error_text.lower() or "error" in error_text.lower()):
                        raise RobotError(
                            message=f"Order submission failed: {error_text}",
                            step=RobotStep.ORDER_SUBMIT
                        )
            except RobotError:
                raise
            except Exception:
                continue

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
            # Get customer name from Excel parsing to match in TecCom dropdown
            # Dropdown shows customer names like "HNR OTOM. PETROL İNŞ. NAKL. TUR SAN, 21070, Diyarbakır"
            customer_name = getattr(self.order, '_excel_customer_name', '') or ''
            customer_code = getattr(self.order, '_excel_customer_code', '') or ''
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer from Excel - name: {customer_name}, code: {customer_code}")

            await self.execute_step(
                RobotStep.CUSTOMER_SELECT,
                lambda: self.select_customer(customer_name),
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

            # Success! Take final screenshot as proof
            success_screenshot = await self.take_screenshot("order_complete")

            result.success = True
            result.portal_order_no = portal_order_no
            result.message = f"Order successfully processed. Portal order: {portal_order_no}"
            result.steps_completed = self.steps_completed
            result.screenshot_paths = self.screenshot_paths

            self.log_step(RobotStep.COMPLETE, "SUCCESS", result.message, screenshot_path=success_screenshot)

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
