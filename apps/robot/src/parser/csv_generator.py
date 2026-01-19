"""
DoruMake CSV Generator
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
    """

    # TecCom CSV format settings
    DELIMITER = ';'
    ENCODING = 'utf-8-sig'  # BOM for Excel compatibility

    # Header template
    HEADER_TITLE = "TecLocal/TecWeb Kanalı ile Sipariş Formu"

    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_from_order(
        self,
        order: OrderData,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate CSV file from OrderData

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

            # Header row
            writer.writerow([self.HEADER_TITLE, "", "", ""])

            # Empty row
            writer.writerow([])

            # Column headers
            writer.writerow(["Sıra No", "Parça Numarası", "Miktar", "Parça Adı"])

            # Data rows
            for i, item in enumerate(order.items, 1):
                if item.quantity <= 0:
                    continue

                writer.writerow([
                    str(i),
                    item.product_code,
                    str(item.quantity),
                    item.product_name or ""
                ])

        logger.info(
            f"Generated CSV with {len(order.items)} items: {file_path}"
        )

        return str(file_path)

    def generate_from_items(
        self,
        items: List[Dict[str, Any]],
        order_code: str = None,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate CSV file from item list

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

            # Header row
            writer.writerow([self.HEADER_TITLE, "", "", ""])

            # Empty row
            writer.writerow([])

            # Column headers
            writer.writerow(["Sıra No", "Parça Numarası", "Miktar", "Parça Adı"])

            # Data rows
            row_num = 1
            for item in items:
                quantity = item.get('quantity', 0)
                if quantity <= 0:
                    continue

                product_code = item.get('product_code') or item.get('code', '')
                product_name = item.get('product_name') or item.get('name', '')

                writer.writerow([
                    str(row_num),
                    product_code,
                    str(quantity),
                    product_name
                ])
                row_num += 1

        logger.info(
            f"Generated CSV with {row_num - 1} items: {file_path}"
        )

        return str(file_path)

    def validate_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a generated CSV file

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

            # Check header
            if len(rows) < 3:
                result["valid"] = False
                result["errors"].append("File too short - missing header or data rows")
                return result

            # Check title row
            if self.HEADER_TITLE not in str(rows[0]):
                result["warnings"].append("Missing or incorrect title row")

            # Check column headers
            headers = rows[2] if len(rows) > 2 else []
            expected_headers = ["Sıra No", "Parça Numarası", "Miktar", "Parça Adı"]

            for i, expected in enumerate(expected_headers):
                if i >= len(headers) or expected not in headers[i]:
                    result["warnings"].append(f"Column {i+1} header mismatch")

            # Check data rows
            for row_idx, row in enumerate(rows[3:], 4):
                if len(row) < 3:
                    result["warnings"].append(f"Row {row_idx} has insufficient columns")
                    continue

                seq_no, product_code, quantity, *rest = row

                # Check sequence number
                expected_seq = row_idx - 3
                try:
                    if int(seq_no) != expected_seq:
                        result["warnings"].append(f"Row {row_idx} sequence mismatch")
                except ValueError:
                    result["warnings"].append(f"Row {row_idx} invalid sequence number")

                # Check product code
                if not product_code.strip():
                    result["errors"].append(f"Row {row_idx} missing product code")
                    result["valid"] = False

                # Check quantity
                try:
                    qty = int(quantity)
                    if qty <= 0:
                        result["warnings"].append(f"Row {row_idx} has zero or negative quantity")
                    else:
                        result["total_quantity"] += qty
                except ValueError:
                    result["errors"].append(f"Row {row_idx} invalid quantity")
                    result["valid"] = False

                result["item_count"] += 1

            # Check item count (TecCom limit is 750)
            if result["item_count"] > 750:
                result["errors"].append(f"Too many items ({result['item_count']}). TecCom limit is 750.")
                result["valid"] = False

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Error reading file: {e}")

        return result
