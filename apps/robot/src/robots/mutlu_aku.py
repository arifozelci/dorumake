"""
KolayRobot Mutlu Akü Robot
VisionNext PRM Portal automation for Mutlu Akü orders
"""

from typing import Any, Dict, List, Optional
from playwright.async_api import TimeoutError as PlaywrightTimeout

from src.config import settings
from src.utils.logger import robot_logger
from src.db.models import Order, OrderItem

from .base import BaseRobot, RobotStep, RobotError, RobotResult


class MutluAkuRobot(BaseRobot):
    """
    Mutlu Akü sipariş robotu

    VisionNext PRM portalında form doldurarak sipariş oluşturur.
    11 adımlık karmaşık bir süreç.
    """

    SUPPLIER_NAME = "Mutlu Akü"
    SUPPLIER_CODE = "MUTLU"
    PORTAL_URL = settings.mutlu_aku.portal_url

    # Customer name mapping: keyword from order customer_name → portal branch name
    CUSTOMER_MAP = {
        "DALAY": "CASTROL BATMAN DALAY PETROL",
        "BİLMAKSAN": "CASTROL TRAKYA BİLMAKSAN",
        "HNR": "CASTROL DİYARBAKIR HNR",
        "ALGÜNLER": "CASTROL MARDİN ALGÜNLER",
        "BİLGE": "CASTROL ÇORUM BİLGE OTOMOTİV",
        "YILMAZ PETROL": "CASTROL KONYA YILMAZ PETROL",
        "MAY AKARYAKIT": "CASTROL MERSİN MAY AKARYAKIT",
        "AKILLAR": "CASTROL ANTALYA AKILLAR",
        "İDUĞ": "CASTROL İZMİR İDUĞ",
        "VİS ENERJİ": "CASTROL İSTANBUL VİS ENERJİ",
        "YD DENİZ": "CASTROL ANKARA YD DENİZ",
        "YAĞPET": "CASTROL BURSA YAĞPET",
        "ÖMÜR": "CASTROL DENİZLİ ÖMÜR",
        "POLAT GIDA": "CASTROL ELAZIĞ POLAT GIDA",
        "CİNDİLLİ": "CASTROL ERZURUM CİNDİLLİ",
        "ELBEYLİ": "CASTROL GAZİANTEP ELBEYLİ PETROL",
        "ÖZTOPRAK": "CASTROL HATAY VEDİ ÖZTOPRAK",
        "KARABULUT": "CASTROL KAYSERİ KARABULUT",
        "ŞİRİNAT": "CASTROL SAKARYA ŞİRİNAT",
        "TUNALAR": "CASTROL SAMSUN TUNALAR",
        "SEFER": "CASTROL TRABZON SEFER TİC.",
        "TEKİN": "CASTROL VAN TEKİN TİC.",
        "ÖCALLAR": "CASTROL ZONGULDAK ÖCALLAR",
    }

    # Selectors
    SELECTORS = {
        # Login
        "username_input": "input[name='UserName'], input[id='UserName'], input[type='email']",
        "password_input": "input[name='Password'], input[id='Password'], input[type='password']",
        "login_button": "button[type='submit'], input[type='submit'], .login-btn",

        # Customer selection (sağ üst köşe - VisionNext PRM dropdown)
        "customer_dropdown": "button#dLabel2, .leftNav button[data-toggle='dropdown']:nth-of-type(2)",
        "customer_option": "a[href*='ChangeActiveBranch']:has-text('{customer_name}')",

        # Menu navigation
        "menu_satis_satinalma": "text=Satış / Satın Alma, text=Satış/Satın Alma",
        "menu_satinalma_siparisi": "text=Satın Alma Siparişi",

        # Order creation
        "create_button": "text=Oluştur, button:has-text('Oluştur'), .btn-create",

        # Form fields
        "depo_select": "[name='Depo'], [id*='Depo'], select:has-text('Depo')",
        "musteri_select": "[name='Musteri'], [id*='Musteri'], input[placeholder*='Müşteri']",
        "personel_select": "[name='Personel'], [id*='Personel'], select:has-text('Personel')",
        "fiyat_listesi_select": "[name='FiyatListesi'], [id*='FiyatListesi'], select:has-text('Fiyat')",
        "odeme_tipi_select": "[name='OdemeTipi'], [id*='OdemeTipi'], select:has-text('Ödeme Tipi')",
        "odeme_vadesi_select": "[name='OdemeVadesi'], [id*='OdemeVadesi'], select:has-text('Ödeme Vadesi')",
        "aciklama_input": "[name='Aciklama'], [id*='Aciklama'], textarea:has-text('Açıklama')",

        # Products tab
        "products_tab": "text=Ürünler, .tab-products, button:has-text('Ürünler')",
        "search_button": "text=ARA, button:has-text('ARA'), button:has-text('Ara')",
        "product_table": ".product-table, table, .grid",
        "quantity_input": "input[type='number'], input[class*='quantity'], input[class*='adet']",
        "save_products_button": "text=Kaydet, button:has-text('Kaydet')",

        # Order save
        "save_order_button": ".save-btn, button:has-text('Kaydet'), [class*='save']",

        # SAP Confirm
        "confirm_button": "text=Siparişi Onayla, button:has-text('Onayla'), .confirm-btn",

        # Messages
        "success_message": "text=Kaydedildi, text=Başarılı, .success-message",
        "error_message": ".error-message, .alert-danger, text=Hata"
    }

    def __init__(self, order: Order, order_items: List[OrderItem] = None, session: Any = None):
        super().__init__(order, session)
        self.order_items = order_items or []
        self.portal_order_no: Optional[str] = None

    async def _js_click(self, pattern: str, tags: str = "a, button, span, input[type='submit']") -> bool:
        """Click element by regex text pattern using JS (bypasses Playwright text= issues in VisionNext PRM)"""
        result = await self.page.evaluate(
            """([pattern, tags]) => {
                const els = document.querySelectorAll(tags);
                const regex = new RegExp(pattern, 'i');
                for (const el of els) {
                    const text = (el.textContent || '').trim();
                    if (regex.test(text)) {
                        el.click();
                        return { clicked: true, text: text };
                    }
                }
                return { clicked: false };
            }""",
            [pattern, tags]
        )
        if result.get('clicked'):
            robot_logger.debug(f"[{self.SUPPLIER_NAME}] JS click matched: '{result.get('text')}' (pattern: {pattern})")
            return True
        return False

    async def login(self) -> None:
        """Portal'a giriş yap"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Logging in...")

        # Wait for login form
        await self.wait_for_element(self.SELECTORS["username_input"])

        # Fill credentials
        await self.fill_input(self.SELECTORS["username_input"], settings.mutlu_aku.username)
        await self.fill_input(self.SELECTORS["password_input"], settings.mutlu_aku.password)

        # Click login
        await self.click_element(self.SELECTORS["login_button"])

        # Wait for navigation
        await self.wait_for_navigation()

        # Verify login success (should not see login form anymore)
        try:
            await self.page.wait_for_selector(self.SELECTORS["username_input"], state="hidden", timeout=5000)
        except PlaywrightTimeout:
            # Login form still visible = login failed
            raise RobotError(
                message="Login failed - credentials may be invalid",
                step=RobotStep.LOGIN
            )

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Login successful")

    def _resolve_customer_name(self) -> str:
        """Resolve order customer_name to portal branch name using CUSTOMER_MAP"""
        # customer_name is set as _excel_customer_name by OrderWorker._create_order_object
        order_customer = getattr(self.order, '_excel_customer_name', '') or getattr(self.order, 'customer_name', '') or ""
        order_customer_upper = order_customer.upper()

        for keyword, portal_name in self.CUSTOMER_MAP.items():
            if keyword.upper() in order_customer_upper:
                robot_logger.info(
                    f"[{self.SUPPLIER_NAME}] Customer mapped: '{order_customer}' → '{portal_name}' (keyword: {keyword})"
                )
                return portal_name

        # Fallback: default customer
        default = "CASTROL BATMAN DALAY PETROL"
        robot_logger.warning(
            f"[{self.SUPPLIER_NAME}] No customer mapping found for '{order_customer}', using default: {default}"
        )
        return default

    async def select_customer(self, customer_name: str) -> None:
        """Müşteri seç (sağ üst dropdown - VisionNext PRM ChangeActiveBranch)"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Selecting customer: {customer_name}")

        # Wait for page to fully load after login
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)

        # Click customer dropdown button (#dLabel2)
        dropdown_btn = await self.page.wait_for_selector(
            self.SELECTORS["customer_dropdown"], timeout=15000
        )
        await dropdown_btn.click()

        # Wait for dropdown menu to appear
        await self.page.wait_for_timeout(1000)

        # Find and click the customer option
        selector = self.SELECTORS["customer_option"].format(customer_name=customer_name)
        customer_link = await self.page.wait_for_selector(selector, timeout=10000)

        if customer_link:
            # Scroll into view if needed (long customer list)
            await customer_link.scroll_into_view_if_needed()
            await customer_link.click()
        else:
            raise Exception(f"Customer not found: {customer_name}")

        # Wait for page reload after branch change
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Customer selected: {customer_name}")

    async def navigate_to_order_screen(self) -> None:
        """Sipariş ekranına git"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Navigating to order screen...")

        # Click "Satış / Satın Alma" menu using JS (Playwright text= selectors fail in VisionNext)
        if not await self._js_click(r"Sat[ıi][şs].*Sat[ıi]n.*Alma"):
            raise Exception("Could not find 'Satış / Satın Alma' menu")

        await self.page.wait_for_timeout(1500)

        # Click "Satın Alma Siparişi" submenu
        for attempt in range(3):
            if await self._js_click(r"Sat[ıi]n.*Alma.*Sipari[şs]"):
                break
            if attempt < 2:
                await self.page.wait_for_timeout(1000)
        else:
            raise Exception("Could not find 'Satın Alma Siparişi' submenu")

        # Wait for page load
        await self.wait_for_navigation()
        await self.page.wait_for_timeout(2000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order screen loaded")

    async def create_new_order(self) -> None:
        """Yeni sipariş oluştur"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Creating new order...")

        # Wait for page to be fully ready
        await self.page.wait_for_load_state("networkidle")
        await self.page.wait_for_timeout(2000)

        # Click "Oluştur" button - use ^Olu to avoid matching "KISAYOL OLUŞTUR"
        if not await self._js_click(r"^Olu[şs]tur"):
            raise Exception("Could not find 'Oluştur' button")

        # Wait for form to load
        await self.wait_for_navigation()
        await self.page.wait_for_timeout(1000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] New order form opened")

    async def fill_order_form(self, caspar_order_no: str) -> None:
        """
        Sipariş formunu doldur

        VisionNext PRM pre-fills most fields (Depo, Müşteri, Fiyat Listesi, Ödeme Tipi).
        We need to fill: Ödeme Vadesi (required), Açıklama/Müşteri Sipariş No.
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Filling order form...")

        # Wait for form to fully render
        await self.page.wait_for_timeout(2000)

        # 1. Fill Ödeme Vadesi (required field) - it's a select/dropdown
        odeme_filled = await self.page.evaluate("""() => {
            // Find all select elements and check labels
            const selects = document.querySelectorAll('select');
            for (const sel of selects) {
                // Check if this select has "Seçiniz" as default and is near "Ödeme Vadesi" label
                const parent = sel.closest('.form-group, .col-md-6, .col-md-4, .col-sm-6, div');
                if (parent) {
                    const labelText = parent.textContent || '';
                    if (/[ÖO]deme.*Vade/i.test(labelText)) {
                        // Find the option with "60" in it
                        for (const opt of sel.options) {
                            if (opt.text.includes('60') || opt.value.includes('60')) {
                                sel.value = opt.value;
                                sel.dispatchEvent(new Event('change', { bubbles: true }));
                                return 'select_60_gun';
                            }
                        }
                        // If no "60" option, select the first non-empty option
                        for (const opt of sel.options) {
                            if (opt.value && opt.text !== 'Seçiniz') {
                                sel.value = opt.value;
                                sel.dispatchEvent(new Event('change', { bubbles: true }));
                                return 'select_first: ' + opt.text;
                            }
                        }
                    }
                }
            }

            // Try select2 style dropdowns
            const spans = document.querySelectorAll('span, div, label');
            for (const span of spans) {
                const text = (span.textContent || '').trim();
                if (/[ÖO]deme.*Vade/i.test(text) && text.length < 30) {
                    const container = span.closest('.form-group, .col-md-6, .col-md-4, div');
                    if (container) {
                        const select = container.querySelector('select');
                        if (select) {
                            for (const opt of select.options) {
                                if (opt.text.includes('60') || opt.value.includes('60')) {
                                    select.value = opt.value;
                                    select.dispatchEvent(new Event('change', { bubbles: true }));
                                    return 'select2_60_gun';
                                }
                            }
                        }
                    }
                }
            }
            return null;
        }""")

        if odeme_filled:
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Ödeme Vadesi filled: {odeme_filled}")
        else:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not fill Ödeme Vadesi")

        # 2. Fill "Müşteri Sipariş Numarası" and/or "Açıklama" with Caspar order no
        filled = await self.page.evaluate(
            """([orderNo]) => {
                const results = [];

                // Fill "Müşteri Sipariş Numarası" input
                const labels = document.querySelectorAll('label, span, div');
                for (const label of labels) {
                    const text = (label.textContent || '').trim();
                    if (/M[üu][şs]teri.*Sipari[şs].*Numaras/i.test(text) && text.length < 40) {
                        const parent = label.closest('.form-group, .col-md-6, .col-md-4, div');
                        if (parent) {
                            const input = parent.querySelector('input:not([type="hidden"]), textarea');
                            if (input) {
                                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                setter.call(input, orderNo);
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                results.push('musteri_siparis');
                            }
                        }
                    }
                }

                // Fill "Açıklama" textarea
                for (const label of labels) {
                    const text = (label.textContent || '').trim();
                    if (/^A[çc][ıi]klama$/i.test(text)) {
                        const parent = label.closest('.form-group, .col-md-12, div');
                        if (parent) {
                            const ta = parent.querySelector('textarea');
                            if (ta) {
                                ta.value = orderNo;
                                ta.dispatchEvent(new Event('input', { bubbles: true }));
                                ta.dispatchEvent(new Event('change', { bubbles: true }));
                                results.push('aciklama');
                            }
                        }
                    }
                }

                // Fallback: find any empty visible textarea
                if (results.length === 0) {
                    const textareas = document.querySelectorAll('textarea');
                    for (const ta of textareas) {
                        if (ta.offsetParent !== null && !ta.value) {
                            ta.value = orderNo;
                            ta.dispatchEvent(new Event('input', { bubbles: true }));
                            ta.dispatchEvent(new Event('change', { bubbles: true }));
                            results.push('textarea_fallback');
                            break;
                        }
                    }
                }

                return results.length > 0 ? results.join(', ') : null;
            }""",
            [caspar_order_no]
        )

        if filled:
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Order number filled via: {filled}")
        else:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not fill order number field")

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order form filled")

    async def open_products_tab(self) -> None:
        """Ürünler sekmesini aç - click 'Ürün' tab in the form"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Opening products tab...")

        # Click the "Ürün" tab (second tab next to "Sipariş" tab)
        # Use JS to find the tab by text
        clicked = await self.page.evaluate("""() => {
            // Find tab elements
            const tabs = document.querySelectorAll('a[data-toggle="tab"], li a, .nav-tabs a, .tab-pane, a[role="tab"]');
            for (const tab of tabs) {
                const text = (tab.textContent || '').trim();
                if (/^[ÜU]r[üu]n$/i.test(text)) {
                    tab.click();
                    return { clicked: true, text: text };
                }
            }
            // Try broader search
            const links = document.querySelectorAll('a, span, li');
            for (const el of links) {
                const text = (el.textContent || '').trim();
                if (/^[ÜU]r[üu]n$/i.test(text)) {
                    el.click();
                    return { clicked: true, text: text };
                }
            }
            return { clicked: false };
        }""")

        if not clicked.get('clicked'):
            # Try clicking the "Ürünler" button (top right, with magnifier icon)
            if not await self._js_click(r"[ÜU]r[üu]nler"):
                raise Exception("Could not find 'Ürün' tab or 'Ürünler' button")

        # Wait for tab content
        await self.page.wait_for_timeout(2000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Products tab opened")

    async def search_products(self) -> None:
        """Ürün listesini getir (ARA butonu)"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Searching products...")

        # Click "ARA" button using JS
        if not await self._js_click(r"^ARA$|^Ara$"):
            raise Exception("Could not find 'ARA' button")

        # Wait for product list to load
        await self.page.wait_for_timeout(3000)  # Wait for full load

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Products loaded")

    async def add_products(self, items: List[Dict[str, Any]]) -> None:
        """
        Ürünleri ekle (adet gir)

        Args:
            items: Ürün listesi [{"code": "...", "quantity": 10}, ...]
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Adding {len(items)} products...")

        for item in items:
            product_code = item.get("product_code") or item.get("code")
            quantity = item.get("quantity", 0)

            if quantity <= 0:
                continue

            try:
                # Find product row by code and fill quantity using JS
                filled = await self.page.evaluate(
                    """([code, qty]) => {
                        const rows = document.querySelectorAll('tr, .row');
                        for (const row of rows) {
                            if (row.textContent && row.textContent.includes(code)) {
                                const input = row.querySelector("input[type='number'], input[class*='adet'], input[class*='quantity'], input[type='text']");
                                if (input) {
                                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                    nativeInputValueSetter.call(input, qty);
                                    input.dispatchEvent(new Event('input', { bubbles: true }));
                                    input.dispatchEvent(new Event('change', { bubbles: true }));
                                    return true;
                                }
                            }
                        }
                        return false;
                    }""",
                    [product_code, str(quantity)]
                )

                if filled:
                    robot_logger.debug(f"[{self.SUPPLIER_NAME}] Added product {product_code}: {quantity}")
                else:
                    robot_logger.warning(f"[{self.SUPPLIER_NAME}] Product row not found: {product_code}")

            except Exception as e:
                robot_logger.warning(f"[{self.SUPPLIER_NAME}] Failed to add product {product_code}: {e}")

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Products added")

    async def save_products(self) -> None:
        """Ürünleri kaydet"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Saving products...")

        # Click "Kaydet" button using JS
        if not await self._js_click(r"Kaydet"):
            raise Exception("Could not find 'Kaydet' button")

        # Wait for save to complete
        await self.page.wait_for_timeout(3000)

        # Check for success message using JS
        has_success = await self.page.evaluate("""() => {
            const body = document.body.textContent || '';
            return /Kaydedildi|Ba[şs]ar[ıi]l[ıi]/i.test(body);
        }""")

        if not has_success:
            # Check for error
            has_error = await self.page.evaluate("""() => {
                const el = document.querySelector('.error-message, .alert-danger');
                return el ? el.textContent.trim() : null;
            }""")
            if has_error:
                raise RobotError(
                    message=f"Product save failed: {has_error}",
                    step=RobotStep.PRODUCTS_SAVE
                )

        # Wait a bit then close the modal/popup
        await self.page.wait_for_timeout(1000)

        # Try to close product popup (press Escape or click close)
        try:
            await self.page.keyboard.press("Escape")
        except:
            pass

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Products saved")

    async def save_order(self) -> None:
        """Siparişi kaydet"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Saving order...")

        # Click "Kaydet" button (green button in top right, seen in VisionNext screenshots)
        if not await self._js_click(r"^Kaydet$"):
            # Fallback: try broader match
            if not await self._js_click(r"Kaydet"):
                raise Exception("Could not find 'Kaydet' button")

        # Wait for save
        await self.page.wait_for_timeout(3000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order saved")

    async def confirm_order_sap(self) -> str:
        """
        Siparişi SAP'e onayla (KRİTİK!)

        Returns:
            Portal sipariş numarası
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Confirming order to SAP (CRITICAL STEP)...")

        # Click "Siparişi Onayla" button using JS
        if not await self._js_click(r"Sipari[şs]i Onayla|Onayla"):
            raise Exception("Could not find 'Siparişi Onayla' button")

        # Wait for confirmation
        await self.page.wait_for_timeout(5000)

        # Try to get order number from the page
        try:
            order_no = await self.page.evaluate("""() => {
                const body = document.body.textContent || '';
                // Look for order number patterns (digits, usually 10+ chars)
                const match = body.match(/(\\d{10,})/);
                return match ? match[1] : null;
            }""")
            if order_no:
                self.portal_order_no = order_no
            else:
                # Try to get from URL or page title
                url = await self.page.evaluate("() => window.location.href")
                robot_logger.info(f"[{self.SUPPLIER_NAME}] Page URL after confirm: {url}")
                self.portal_order_no = "CONFIRMED"
        except Exception as e:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not extract order number: {e}")
            self.portal_order_no = "CONFIRMED"

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order confirmed to SAP. Portal order: {self.portal_order_no}")
        return self.portal_order_no

    async def process_order(self) -> RobotResult:
        """
        Sipariş işleme ana akışı

        Returns:
            RobotResult: İşlem sonucu
        """
        result = RobotResult(success=False, order_id=self.order.id)

        try:
            # Step 1: Login
            await self.execute_step(
                RobotStep.LOGIN,
                self.login,
                "Login to Mutlu Akü portal",
                max_attempts=settings.retry.login_max_attempts,
                wait_seconds=settings.retry.login_wait_seconds
            )

            # Step 2: Customer selection - match order customer to portal branch
            customer_name = self._resolve_customer_name()
            robot_logger.info(f"[{self.SUPPLIER_NAME}] Resolved customer: {customer_name}")
            await self.execute_step(
                RobotStep.CUSTOMER_SELECT,
                lambda: self.select_customer(customer_name),
                "Select customer",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 3: Navigate to order screen
            await self.execute_step(
                RobotStep.MENU_NAVIGATE,
                self.navigate_to_order_screen,
                "Navigate to order screen",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 4: Create new order
            await self.execute_step(
                RobotStep.ORDER_CREATE,
                self.create_new_order,
                "Create new order",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 5: Fill form
            caspar_order_no = self.order.caspar_order_no or self.order.order_code
            await self.execute_step(
                RobotStep.FORM_FILL,
                lambda: self.fill_order_form(caspar_order_no),
                "Fill order form",
                max_attempts=settings.retry.form_fill_max_attempts,
                wait_seconds=settings.retry.form_fill_wait_seconds
            )

            # Step 6: Open products tab
            await self.execute_step(
                RobotStep.PRODUCTS_TAB,
                self.open_products_tab,
                "Open products tab",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 7: Search products (ARA)
            await self.execute_step(
                RobotStep.PRODUCTS_SEARCH,
                self.search_products,
                "Search products",
                max_attempts=settings.retry.navigation_max_attempts,
                wait_seconds=settings.retry.navigation_wait_seconds
            )

            # Step 8: Add products
            items = [
                {"product_code": item.product_code, "quantity": item.quantity}
                for item in self.order_items
            ]
            await self.execute_step(
                RobotStep.PRODUCTS_ADD,
                lambda: self.add_products(items),
                "Add products",
                max_attempts=settings.retry.form_fill_max_attempts,
                wait_seconds=settings.retry.form_fill_wait_seconds
            )

            # Step 9: Save products
            await self.execute_step(
                RobotStep.PRODUCTS_SAVE,
                self.save_products,
                "Save products",
                max_attempts=settings.retry.submit_max_attempts,
                wait_seconds=settings.retry.submit_wait_seconds
            )

            # Step 10: Save order
            await self.execute_step(
                RobotStep.ORDER_SAVE,
                self.save_order,
                "Save order",
                max_attempts=settings.retry.submit_max_attempts,
                wait_seconds=settings.retry.submit_wait_seconds
            )

            # Step 11: Confirm to SAP (CRITICAL!)
            portal_order_no = await self.execute_step(
                RobotStep.ORDER_CONFIRM,
                self.confirm_order_sap,
                "Confirm order to SAP",
                max_attempts=settings.retry.submit_max_attempts,
                wait_seconds=settings.retry.submit_wait_seconds,
                take_screenshot_on_error=True  # Always screenshot on SAP errors
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

        return result
