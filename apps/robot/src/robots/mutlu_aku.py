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

        # Click "Satış / Satın Alma" menu
        await self.click_element(self.SELECTORS["menu_satis_satinalma"])
        await self.page.wait_for_timeout(500)

        # Click "Satın Alma Siparişi"
        await self.click_element(self.SELECTORS["menu_satinalma_siparisi"])

        # Wait for page load
        await self.wait_for_navigation()

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order screen loaded")

    async def create_new_order(self) -> None:
        """Yeni sipariş oluştur"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Creating new order...")

        # Click "Oluştur" button
        await self.click_element(self.SELECTORS["create_button"])

        # Wait for form to load
        await self.wait_for_navigation()

        robot_logger.info(f"[{self.SUPPLIER_NAME}] New order form opened")

    async def fill_order_form(self, caspar_order_no: str) -> None:
        """
        Sipariş formunu doldur

        Args:
            caspar_order_no: Caspar sipariş numarası (açıklama alanına yazılacak)
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Filling order form...")

        # Depo seçimi
        try:
            await self.select_option(
                self.SELECTORS["depo_select"],
                label=settings.mutlu_aku.default_depo
            )
        except Exception as e:
            robot_logger.warning(f"Depo selection failed (may be pre-filled): {e}")

        # Personel seçimi
        try:
            await self.select_option(
                self.SELECTORS["personel_select"],
                label=settings.mutlu_aku.default_personel
            )
        except Exception as e:
            robot_logger.warning(f"Personel selection failed (may be pre-filled): {e}")

        # Ödeme tipi
        try:
            await self.select_option(
                self.SELECTORS["odeme_tipi_select"],
                label=settings.mutlu_aku.default_odeme_tipi
            )
        except Exception as e:
            robot_logger.warning(f"Odeme tipi selection failed (may be pre-filled): {e}")

        # Ödeme vadesi
        try:
            await self.select_option(
                self.SELECTORS["odeme_vadesi_select"],
                label=settings.mutlu_aku.default_odeme_vadesi
            )
        except Exception as e:
            robot_logger.warning(f"Odeme vadesi selection failed (may be pre-filled): {e}")

        # Açıklama (Caspar sipariş numarası)
        await self.fill_input(self.SELECTORS["aciklama_input"], caspar_order_no)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order form filled")

    async def open_products_tab(self) -> None:
        """Ürünler sekmesini aç"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Opening products tab...")

        # Click "Ürünler" tab
        await self.click_element(self.SELECTORS["products_tab"])

        # Wait for tab content
        await self.page.wait_for_timeout(1000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Products tab opened")

    async def search_products(self) -> None:
        """Ürün listesini getir (ARA butonu)"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Searching products...")

        # Click "ARA" button
        await self.click_element(self.SELECTORS["search_button"])

        # Wait for product list to load
        await self.wait_for_element(self.SELECTORS["product_table"])
        await self.page.wait_for_timeout(2000)  # Wait for full load

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
                # Find product row by code
                row_selector = f"tr:has-text('{product_code}'), .row:has-text('{product_code}')"
                row = await self.page.wait_for_selector(row_selector, timeout=5000)

                if row:
                    # Find quantity input in this row
                    qty_input = await row.query_selector("input[type='number'], input[class*='adet']")
                    if qty_input:
                        await qty_input.fill(str(quantity))
                        robot_logger.debug(f"[{self.SUPPLIER_NAME}] Added product {product_code}: {quantity}")
                    else:
                        robot_logger.warning(f"[{self.SUPPLIER_NAME}] Quantity input not found for {product_code}")
                else:
                    robot_logger.warning(f"[{self.SUPPLIER_NAME}] Product row not found: {product_code}")

            except Exception as e:
                robot_logger.warning(f"[{self.SUPPLIER_NAME}] Failed to add product {product_code}: {e}")

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Products added")

    async def save_products(self) -> None:
        """Ürünleri kaydet"""
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Saving products...")

        # Click "Kaydet" button
        await self.click_element(self.SELECTORS["save_products_button"])

        # Wait for success message
        try:
            await self.wait_for_text("Kaydedildi", timeout=10000)
        except PlaywrightTimeout:
            # Check for error message
            error_el = await self.page.query_selector(self.SELECTORS["error_message"])
            if error_el:
                error_text = await error_el.text_content()
                raise RobotError(
                    message=f"Product save failed: {error_text}",
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

        # Click "Kaydet" button (top right)
        await self.click_element(self.SELECTORS["save_order_button"])

        # Wait for save
        await self.page.wait_for_timeout(2000)

        robot_logger.info(f"[{self.SUPPLIER_NAME}] Order saved")

    async def confirm_order_sap(self) -> str:
        """
        Siparişi SAP'e onayla (KRİTİK!)

        Returns:
            Portal sipariş numarası
        """
        robot_logger.info(f"[{self.SUPPLIER_NAME}] Confirming order to SAP (CRITICAL STEP)...")

        # Click "Siparişi Onayla" button
        await self.click_element(self.SELECTORS["confirm_button"])

        # Wait for confirmation
        await self.page.wait_for_timeout(3000)

        # Try to get order number from the page
        # This may vary based on portal response
        try:
            # Look for order number in page content
            page_content = await self.page.content()
            # Parse order number (implementation depends on portal response)
            # This is a placeholder - actual implementation needs portal testing
            self.portal_order_no = "PORTAL_ORDER_NO"  # TODO: Extract from page
        except Exception as e:
            robot_logger.warning(f"[{self.SUPPLIER_NAME}] Could not extract order number: {e}")

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
