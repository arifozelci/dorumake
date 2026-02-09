"""
KolayRobot Email Parser
Parses email content to extract supplier and order information
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from io import BytesIO

import openpyxl

from src.utils.logger import email_logger


class SupplierType(Enum):
    """Supported supplier types"""
    MUTLU_AKU = "MUTLU"
    MANN_HUMMEL = "MANN"
    UNKNOWN = "UNKNOWN"


class EmailParser:
    """
    Email content parser for order processing

    Analyzes email subject, body, and attachments to determine:
    - Which supplier the order is for
    - Customer information
    - Order reference numbers
    """

    # Keyword patterns for supplier detection
    SUPPLIER_PATTERNS = {
        SupplierType.MUTLU_AKU: [
            r'mutlu\s*ak[üu]',
            r'mutlu\s*battery',
            r'visionnext',
            r'castrol.*ak[üu]',
            r'efb|start.stop',
        ],
        SupplierType.MANN_HUMMEL: [
            r'mann.*hummel',
            r'filtron',
            r'teccom',
            r'tecalliance',
            r'hava\s*filtre',
            r'polen\s*filtre',
            r'ya[ğg]\s*filtre',
            r'air\s*filter',
            r'oil\s*filter',
        ]
    }

    # Caspar email patterns (source system)
    CASPAR_SENDER_PATTERNS = [
        r'caspar',
        r'info@caspar\.com\.tr',
        r'approved\s*purchase\s*order',
    ]

    # Excel-based supplier detection (Brand/Manufacturer columns)
    EXCEL_SUPPLIER_PATTERNS = {
        SupplierType.MANN_HUMMEL: [
            r'mann',
            r'hummel',
            r'mummel',  # Typo in some source data
            r'filtron',
        ],
        SupplierType.MUTLU_AKU: [
            r'mutlu',
            r'efb',
            r'start.stop',
            r'ak[üu]',
        ]
    }

    # Customer code patterns
    CUSTOMER_CODE_PATTERNS = [
        r'TRM\d{5}',  # Mann & Hummel customer code (TRM56062)
        r'CASTROL[_\s]?[\w]+',  # Castrol codes
        r'M\d{2}[A-Z]\d{1}-\d{9}',  # Order code pattern (M08D1-000001226)
    ]

    # Order number patterns
    ORDER_NUMBER_PATTERNS = [
        r'sipari[şs]\s*(?:no|numaras[ıi]|kodu?)[\s:]*([A-Z0-9\-]+)',
        r'order\s*(?:no|number|code)[\s:]*([A-Z0-9\-]+)',
        r'caspar[\s:]*([A-Z0-9\-]+)',
        r'M\d{2}[A-Z]\d{1}-\d{9}',  # Direct order code
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        self._supplier_regex = {}
        for supplier, patterns in self.SUPPLIER_PATTERNS.items():
            combined = '|'.join(f'({p})' for p in patterns)
            self._supplier_regex[supplier] = re.compile(combined, re.IGNORECASE)

        self._customer_regex = [
            re.compile(p, re.IGNORECASE) for p in self.CUSTOMER_CODE_PATTERNS
        ]

        self._order_regex = [
            re.compile(p, re.IGNORECASE) for p in self.ORDER_NUMBER_PATTERNS
        ]

    def detect_supplier(
        self,
        subject: str,
        body: str,
        attachments: List[Dict[str, Any]] = None
    ) -> Tuple[SupplierType, float]:
        """
        Detect which supplier this email is for

        Args:
            subject: Email subject
            body: Email body text
            attachments: List of attachment info

        Returns:
            Tuple of (supplier_type, confidence_score)
        """
        content = f"{subject} {body}".lower()

        # Also check attachment filenames
        if attachments:
            for att in attachments:
                content += f" {att.get('filename', '')}".lower()

        scores = {supplier: 0 for supplier in SupplierType}

        # Check each supplier's patterns
        for supplier, regex in self._supplier_regex.items():
            matches = regex.findall(content)
            scores[supplier] = len(matches)

        # Find best match
        best_supplier = max(scores, key=scores.get)
        best_score = scores[best_supplier]

        if best_score == 0:
            return SupplierType.UNKNOWN, 0.0

        # Calculate confidence (normalize by total matches)
        total_matches = sum(scores.values())
        confidence = best_score / total_matches if total_matches > 0 else 0.0

        email_logger.debug(f"Supplier detection: {best_supplier.value} (confidence: {confidence:.2f})")

        return best_supplier, confidence

    def is_caspar_email(self, sender: str, subject: str) -> bool:
        """Check if email is from Caspar system"""
        combined = f"{sender} {subject}".lower()
        for pattern in self.CASPAR_SENDER_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                return True
        return False

    def detect_supplier_from_excel(self, excel_data: bytes) -> Tuple[SupplierType, float]:
        """
        Detect supplier from Excel attachment content

        Looks at Brand and Manufacturer columns to determine supplier
        """
        try:
            wb = openpyxl.load_workbook(BytesIO(excel_data))
            sheet = wb.active

            supplier_counts = {SupplierType.MANN_HUMMEL: 0, SupplierType.MUTLU_AKU: 0}

            # Find header row and column indices
            brand_col = None
            manufacturer_col = None

            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if row and any('Brand' in str(cell) for cell in row if cell):
                    for j, cell in enumerate(row):
                        if cell and 'Brand' in str(cell):
                            brand_col = j
                        if cell and 'Manufacturer' in str(cell):
                            manufacturer_col = j
                    continue

                # Check brand/manufacturer values
                if brand_col is not None or manufacturer_col is not None:
                    brand_val = str(row[brand_col] or '').lower() if brand_col and brand_col < len(row) else ''
                    mfr_val = str(row[manufacturer_col] or '').lower() if manufacturer_col and manufacturer_col < len(row) else ''
                    combined = f'{brand_val} {mfr_val}'

                    for supplier, patterns in self.EXCEL_SUPPLIER_PATTERNS.items():
                        for pattern in patterns:
                            if re.search(pattern, combined, re.IGNORECASE):
                                supplier_counts[supplier] += 1

            # Determine supplier
            best_supplier = max(supplier_counts, key=supplier_counts.get)
            best_count = supplier_counts[best_supplier]

            if best_count == 0:
                return SupplierType.UNKNOWN, 0.0

            total = sum(supplier_counts.values())
            confidence = best_count / total if total > 0 else 0.0

            email_logger.info(f"Excel supplier detection: {best_supplier.value} (confidence: {confidence:.2f}, count: {best_count})")
            return best_supplier, confidence

        except Exception as e:
            email_logger.error(f"Error parsing Excel for supplier: {e}")
            return SupplierType.UNKNOWN, 0.0

    def extract_customer_codes(
        self,
        subject: str,
        body: str
    ) -> List[str]:
        """
        Extract customer codes from email

        Args:
            subject: Email subject
            body: Email body text

        Returns:
            List of found customer codes
        """
        content = f"{subject} {body}"
        codes = []

        for regex in self._customer_regex:
            matches = regex.findall(content)
            codes.extend(matches)

        # Remove duplicates while preserving order
        seen = set()
        unique_codes = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)

        return unique_codes

    def extract_order_numbers(
        self,
        subject: str,
        body: str
    ) -> List[str]:
        """
        Extract order numbers from email

        Args:
            subject: Email subject
            body: Email body text

        Returns:
            List of found order numbers
        """
        content = f"{subject} {body}"
        numbers = []

        for regex in self._order_regex:
            matches = regex.findall(content)
            if matches:
                # Handle groups
                for match in matches:
                    if isinstance(match, tuple):
                        numbers.extend([m for m in match if m])
                    else:
                        numbers.append(match)

        # Remove duplicates
        seen = set()
        unique_numbers = []
        for num in numbers:
            if num and num not in seen:
                seen.add(num)
                unique_numbers.append(num)

        return unique_numbers

    def parse_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse email and extract all relevant information

        Args:
            email_data: Email data dict from fetcher

        Returns:
            Parsed email info with supplier detection, customer codes, etc.
        """
        subject = email_data.get('subject', '')
        body_text = email_data.get('body_text', '')
        body_html = email_data.get('body_html', '')
        attachments = email_data.get('attachments', [])

        # Use text body, fall back to stripping HTML tags
        body = body_text
        if not body and body_html:
            # Simple HTML tag removal
            body = re.sub(r'<[^>]+>', ' ', body_html)
            body = re.sub(r'\s+', ' ', body).strip()

        from_address = email_data.get('from_address', '')

        # Check if this is a Caspar email - needs Excel parsing for supplier
        if self.is_caspar_email(from_address, subject):
            email_logger.info(f"Detected Caspar email, will use Excel content for supplier detection")
            # Try to detect supplier from Excel attachments
            supplier = SupplierType.UNKNOWN
            confidence = 0.0
            for att in attachments:
                if att.get('filename', '').lower().endswith(('.xlsx', '.xls')):
                    # Try to get raw data first, if not available read from file_path
                    excel_data = att.get('data')
                    if not excel_data and att.get('file_path'):
                        try:
                            with open(att['file_path'], 'rb') as f:
                                excel_data = f.read()
                        except Exception as e:
                            email_logger.error(f"Failed to read Excel file: {e}")
                            continue
                    if excel_data:
                        supplier, confidence = self.detect_supplier_from_excel(excel_data)
                        if supplier != SupplierType.UNKNOWN:
                            break
        else:
            # Detect supplier from email content
            supplier, confidence = self.detect_supplier(subject, body, attachments)

        # Extract codes and numbers
        customer_codes = self.extract_customer_codes(subject, body)
        order_numbers = self.extract_order_numbers(subject, body)

        # Find Excel attachments
        excel_attachments = [
            att for att in attachments
            if att.get('filename', '').lower().endswith(('.xlsx', '.xls'))
        ]

        # Determine if this is a valid order email
        is_valid_order = (
            supplier != SupplierType.UNKNOWN and
            len(excel_attachments) > 0
        )

        result = {
            "email_id": email_data.get('id'),
            "message_id": email_data.get('message_id'),
            "subject": subject,
            "from_address": email_data.get('from_address'),
            "to_address": email_data.get('to_address'),
            "received_at": email_data.get('received_at'),

            # Parsed data
            "supplier_type": supplier.value,
            "supplier_confidence": confidence,
            "customer_codes": customer_codes,
            "order_numbers": order_numbers,

            # Attachments
            "excel_attachments": excel_attachments,
            "attachment_count": len(attachments),

            # Validation
            "is_valid_order": is_valid_order,
            "validation_errors": []
        }

        # Add validation errors
        if supplier == SupplierType.UNKNOWN:
            result["validation_errors"].append("Could not determine supplier")
        if not excel_attachments:
            result["validation_errors"].append("No Excel attachment found")
        if not customer_codes and supplier == SupplierType.MANN_HUMMEL:
            result["validation_errors"].append("No customer code (TRM) found for Mann & Hummel")

        email_logger.info(
            f"Parsed email: supplier={supplier.value}, "
            f"confidence={confidence:.2f}, "
            f"valid={is_valid_order}, "
            f"attachments={len(excel_attachments)}"
        )

        return result

    def get_supplier_robot_type(self, supplier_type: str) -> Optional[str]:
        """
        Get robot class name for supplier type

        Args:
            supplier_type: Supplier type string

        Returns:
            Robot class name or None
        """
        mapping = {
            SupplierType.MUTLU_AKU.value: "MutluAkuRobot",
            SupplierType.MANN_HUMMEL.value: "MannHummelRobot",
        }
        return mapping.get(supplier_type)
