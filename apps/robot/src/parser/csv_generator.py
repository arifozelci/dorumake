"""
KolayRobot CSV Generator
Generates CSV files in TecCom format for Mann & Hummel orders
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.utils.logger import logger
from .excel_parser import OrderData, OrderItemData


class CsvGenerator:
    """
    CSV generator for TecCom portal (Mann & Hummel)

    Generates CSV files in the format expected by TecCom:
    Siparis_formu_TecOrder_2018.csv

    Format structure:
    - Uses comma (,) as delimiter
    - leer prefix for empty/info rows
    - head prefix for header area
    - POS prefix for product/data rows
    - 8 columns total
    """

    # TecCom CSV format settings
    DELIMITER = ','
    ENCODING = 'iso-8859-9'  # ISO-8859-9 (Latin-5/Turkish) encoding - supports Turkish characters

    # Header template
    HEADER_TITLE = "TecLocal/TecWeb Kanalıyla Sipariş Formu"

    # Row prefixes
    PREFIX_EMPTY = "leer"
    PREFIX_HEAD = "head"
    PREFIX_DATA = "POS"

    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _empty_row(self) -> List[str]:
        """Generate empty leer row with 8 columns"""
        return [self.PREFIX_EMPTY, "", "", "", "", "", "", ""]

    def generate_from_order(
        self,
        order: OrderData,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate CSV file from OrderData in TecCom format

        Args:
            order: OrderData object
            filename: Optional custom filename

        Returns:
            Path to generated CSV file
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"teccom_order_{order.order_code}_{timestamp}.csv"

        file_path = self.output_dir / filename

        logger.info(f"Generating TecCom CSV: {file_path}")

        with open(file_path, 'w', newline='', encoding=self.ENCODING) as f:
            writer = csv.writer(f, delimiter=self.DELIMITER)

            # 5 empty leer rows
            for _ in range(5):
                writer.writerow(self._empty_row())

            # Title row
            writer.writerow([self.PREFIX_EMPTY, self.HEADER_TITLE, "", "", "", "", "", ""])

            # Empty row
            writer.writerow(self._empty_row())

            # Tracking number row (optional - can be filled with order code)
            writer.writerow([
                self.PREFIX_EMPTY,
                f"Siparişimiz için Belirlediğimiz Takip Numaramız",
                f"Kurumumuz Adına \nSipariş Veren Kişi",
                "", "", "", "", ""
            ])

            # Head row
            writer.writerow([self.PREFIX_HEAD, "", "", "", "", "", "", ""])

            # 3 empty rows
            for _ in range(3):
                writer.writerow(self._empty_row())

            # Instruction row 1
            writer.writerow([
                self.PREFIX_EMPTY,
                "Kırmızı ile işaretli alanlar zorunludur,yoksa hata verir",
                "", "", "", "", "", ""
            ])

            # Instruction row 2
            writer.writerow([
                self.PREFIX_EMPTY,
                "Bir seferde en fazla 750 kalem ürün için kullanılması uygundur",
                "", "", "", "", "", ""
            ])

            # Empty row
            writer.writerow(self._empty_row())

            # Column headers row
            writer.writerow([
                self.PREFIX_EMPTY,
                "Sıra No",
                "Parça No",
                "Adet",
                "", "", "",
                "Parça Adı"
            ])

            # Data rows with POS prefix
            row_num = 1
            for item in order.items:
                if item.quantity <= 0:
                    continue

                writer.writerow([
                    self.PREFIX_DATA,
                    str(row_num),
                    item.product_code,
                    str(item.quantity),
                    "", "", "",
                    item.product_name or ""
                ])
                row_num += 1

        logger.info(
            f"Generated CSV with {row_num - 1} items: {file_path}"
        )

        return str(file_path)

    def generate_from_items(
        self,
        items: List[Dict[str, Any]],
        order_code: str = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate CSV file from item list in TecCom format

        Args:
            items: List of item dicts with product_code and quantity
            order_code: Order code for filename
            filename: Optional custom filename

        Returns:
            Path to generated CSV file
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            code = order_code or "manual"
            filename = f"teccom_order_{code}_{timestamp}.csv"

        file_path = self.output_dir / filename

        logger.info(f"Generating TecCom CSV from items: {file_path}")

        with open(file_path, 'w', newline='', encoding=self.ENCODING) as f:
            writer = csv.writer(f, delimiter=self.DELIMITER)

            # 5 empty leer rows
            for _ in range(5):
                writer.writerow(self._empty_row())

            # Title row
            writer.writerow([self.PREFIX_EMPTY, self.HEADER_TITLE, "", "", "", "", "", ""])

            # Empty row
            writer.writerow(self._empty_row())

            # Tracking number row
            writer.writerow([
                self.PREFIX_EMPTY,
                f"Siparişimiz için Belirlediğimiz Takip Numaramız",
                f"Kurumumuz Adına \nSipariş Veren Kişi",
                "", "", "", "", ""
            ])

            # Head row
            writer.writerow([self.PREFIX_HEAD, "", "", "", "", "", "", ""])

            # 3 empty rows
            for _ in range(3):
                writer.writerow(self._empty_row())

            # Instruction row 1
            writer.writerow([
                self.PREFIX_EMPTY,
                "Kırmızı ile işaretli alanlar zorunludur,yoksa hata verir",
                "", "", "", "", "", ""
            ])

            # Instruction row 2
            writer.writerow([
                self.PREFIX_EMPTY,
                "Bir seferde en fazla 750 kalem ürün için kullanılması uygundur",
                "", "", "", "", "", ""
            ])

            # Empty row
            writer.writerow(self._empty_row())

            # Column headers row
            writer.writerow([
                self.PREFIX_EMPTY,
                "Sıra No",
                "Parça No",
                "Adet",
                "", "", "",
                "Parça Adı"
            ])

            # Data rows with POS prefix
            row_num = 1
            for item in items:
                quantity = item.get('quantity', 0)
                if quantity <= 0:
                    continue

                product_code = item.get('product_code') or item.get('code', '')
                product_name = item.get('product_name') or item.get('name', '')

                writer.writerow([
                    self.PREFIX_DATA,
                    str(row_num),
                    product_code,
                    str(quantity),
                    "", "", "",
                    product_name
                ])
                row_num += 1

        logger.info(
            f"Generated CSV with {row_num - 1} items: {file_path}"
        )

        return str(file_path)

    def validate_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a generated CSV file in TecCom format

        Args:
            file_path: Path to CSV file

        Returns:
            Validation result dict
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "item_count": 0,
            "total_quantity": 0
        }

        try:
            with open(file_path, 'r', encoding=self.ENCODING) as f:
                reader = csv.reader(f, delimiter=self.DELIMITER)
                rows = list(reader)

            # Check minimum rows (header structure + at least 1 data row)
            if len(rows) < 18:
                result["valid"] = False
                result["errors"].append("File too short - missing header or data rows")
                return result

            # Check title row (row 5, 0-indexed)
            title_found = False
            for row in rows[:10]:
                if self.HEADER_TITLE in str(row):
                    title_found = True
                    break
            if not title_found:
                result["warnings"].append("Missing or incorrect title row")

            # Check for head row
            head_found = False
            for row in rows:
                if row and row[0] == self.PREFIX_HEAD:
                    head_found = True
                    break
            if not head_found:
                result["warnings"].append("Missing head row")

            # Check data rows (rows with POS prefix)
            for row_idx, row in enumerate(rows):
                if not row or len(row) < 4:
                    continue

                # Check if this is a data row (POS prefix)
                if row[0] != self.PREFIX_DATA:
                    continue

                seq_no = row[1] if len(row) > 1 else ""
                product_code = row[2] if len(row) > 2 else ""
                quantity = row[3] if len(row) > 3 else ""

                # Check product code
                if not product_code.strip():
                    result["errors"].append(f"Row {row_idx + 1} missing product code")
                    result["valid"] = False
                    continue

                # Check quantity
                try:
                    qty = int(quantity)
                    if qty <= 0:
                        result["warnings"].append(f"Row {row_idx + 1} has zero or negative quantity")
                    else:
                        result["total_quantity"] += qty
                except ValueError:
                    result["errors"].append(f"Row {row_idx + 1} invalid quantity: {quantity}")
                    result["valid"] = False
                    continue

                result["item_count"] += 1

            # Check item count (TecCom limit is 750)
            if result["item_count"] > 750:
                result["errors"].append(f"Too many items ({result['item_count']}). TecCom limit is 750.")
                result["valid"] = False

            if result["item_count"] == 0:
                result["errors"].append("No data rows found (rows with POS prefix)")
                result["valid"] = False

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error reading file: {e}")

        return result
