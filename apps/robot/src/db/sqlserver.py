"""
SQL Server Database Helper for DoruMake
Provides direct database operations using pyodbc

This module does not depend on SQLAlchemy async engine or aioodbc.
It uses pyodbc for synchronous database connections.
"""

import pyodbc
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import uuid

# Import settings directly to avoid circular imports through db.__init__
from src.config.settings import settings


class SQLServerDB:
    """SQL Server database helper with direct pyodbc connections"""

    def __init__(self):
        self._connection_string = (
            f"DRIVER={{{settings.database.driver}}};"
            f"SERVER={settings.database.host},{settings.database.port};"
            f"DATABASE={settings.database.name};"
            f"UID={settings.database.user};"
            f"PWD={settings.database.password};"
            f"TrustServerCertificate=yes;"
        )

    def get_connection(self) -> pyodbc.Connection:
        """Get a new database connection"""
        return pyodbc.connect(self._connection_string)

    @contextmanager
    def get_cursor(self, commit: bool = False):
        """Context manager for database cursor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def _rows_to_dicts(self, cursor, rows) -> List[Dict[str, Any]]:
        """Convert cursor rows to list of dicts"""
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    # ============================================
    # USER OPERATIONS
    # ============================================

    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active,
                       receive_notifications, created_at
                FROM users
                ORDER BY created_at DESC
            """)
            rows = cursor.fetchall()
            users = self._rows_to_dicts(cursor, rows)
            for user in users:
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else str(user['created_at'])
            return users

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active,
                       receive_notifications, created_at, hashed_password
                FROM users
                WHERE username = ?
            """, (username,))
            row = cursor.fetchone()
            if row:
                user = dict(zip([column[0] for column in cursor.description], row))
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else str(user['created_at'])
                return user
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active,
                       receive_notifications, created_at
                FROM users
                WHERE email = ?
            """, (email,))
            row = cursor.fetchone()
            if row:
                user = dict(zip([column[0] for column in cursor.description], row))
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else str(user['created_at'])
                return user
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, full_name, role, is_active,
                       receive_notifications, created_at
                FROM users
                WHERE id = ?
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                user = dict(zip([column[0] for column in cursor.description], row))
                if user.get('created_at'):
                    user['created_at'] = user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else str(user['created_at'])
                return user
            return None

    def create_user(self, username: str, email: str, hashed_password: str,
                    full_name: str = "", role: str = "user") -> Dict[str, Any]:
        """Create a new user"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO users (username, email, hashed_password, full_name, role, is_active, receive_notifications, created_at)
                OUTPUT INSERTED.id, INSERTED.username, INSERTED.email, INSERTED.full_name, INSERTED.role, INSERTED.is_active, INSERTED.receive_notifications, INSERTED.created_at
                VALUES (?, ?, ?, ?, ?, 1, 1, GETDATE())
            """, (username, email, hashed_password, full_name, role))
            row = cursor.fetchone()
            user = dict(zip([column[0] for column in cursor.description], row))
            if user.get('created_at'):
                user['created_at'] = user['created_at'].isoformat() if isinstance(user['created_at'], datetime) else str(user['created_at'])
            return user

    def update_user(self, user_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Update user fields"""
        allowed_fields = ['email', 'full_name', 'role', 'is_active', 'receive_notifications', 'hashed_password']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

        if not updates:
            return self.get_user_by_id(user_id)

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]

        with self.get_cursor(commit=True) as cursor:
            cursor.execute(f"""
                UPDATE users SET {set_clause} WHERE id = ?
            """, values)

        return self.get_user_by_id(user_id)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return cursor.rowcount > 0

    # ============================================
    # EMAIL OPERATIONS
    # ============================================

    def get_emails(self, status: Optional[str] = None, page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """Get emails with pagination"""
        with self.get_cursor() as cursor:
            where_clause = ""
            params = []
            if status:
                where_clause = "WHERE status = ?"
                params.append(status.upper())

            # Get total count
            cursor.execute(f"SELECT COUNT(*) FROM emails {where_clause}", params)
            total = cursor.fetchone()[0]

            # Get paginated results
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT id, message_id, subject, from_address as [from], to_address as [to],
                       received_at, body_text, status, has_attachments, attachment_count, created_at
                FROM emails
                {where_clause}
                ORDER BY received_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, page_size])

            rows = cursor.fetchall()
            emails = self._rows_to_dicts(cursor, rows)

            for email in emails:
                if email.get('received_at'):
                    email['received_at'] = email['received_at'].isoformat() if isinstance(email['received_at'], datetime) else str(email['received_at'])
                if email.get('created_at'):
                    email['created_at'] = email['created_at'].isoformat() if isinstance(email['created_at'], datetime) else str(email['created_at'])
                if email.get('status'):
                    email['status'] = email['status'].lower()

            return emails, total

    def save_email(self, email_id: str, message_id: str, subject: str, from_address: str,
                   to_address: str, received_at: datetime, body_text: str = None,
                   status: str = "UNPROCESSED", has_attachments: bool = False) -> str:
        """Save a new email"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO emails (id, message_id, subject, from_address, to_address,
                                   received_at, body_text, status, has_attachments, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (email_id, message_id, subject, from_address, to_address,
                  received_at, body_text, status.upper(), 1 if has_attachments else 0))
        return email_id

    def update_email_status(self, email_id: str, status: str) -> bool:
        """Update email status"""
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE emails SET status = ? WHERE id = ?
            """, (status.upper(), email_id))
            return cursor.rowcount > 0

    # ============================================
    # ORDER OPERATIONS
    # ============================================

    def get_orders(self, status: Optional[str] = None, supplier: Optional[str] = None,
                   page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """Get orders with pagination"""
        with self.get_cursor() as cursor:
            where_conditions = []
            params = []

            if status:
                where_conditions.append("o.status = ?")
                params.append(status.upper())

            if supplier:
                supplier_code = supplier.upper().replace('_', '-')
                if 'MUTLU' in supplier_code:
                    supplier_code = 'MUTLU-AKU'
                elif 'MANN' in supplier_code:
                    supplier_code = 'MANN-HUMMEL'
                where_conditions.append("s.code = ?")
                params.append(supplier_code)

            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)

            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM orders o
                LEFT JOIN suppliers s ON o.supplier_id = s.id
                {where_clause}
            """, params)
            total = cursor.fetchone()[0]

            # Get paginated results
            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT o.id, o.order_code, o.caspar_order_no, o.status, o.error_message,
                       s.code as supplier_type, o.customer_name, o.item_count, o.total_amount,
                       o.portal_order_no, o.created_at, o.completed_at
                FROM orders o
                LEFT JOIN suppliers s ON o.supplier_id = s.id
                {where_clause}
                ORDER BY o.created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, page_size])

            rows = cursor.fetchall()
            orders = self._rows_to_dicts(cursor, rows)

            for order in orders:
                if order.get('created_at'):
                    order['created_at'] = order['created_at'].isoformat() if isinstance(order['created_at'], datetime) else str(order['created_at'])
                if order.get('completed_at'):
                    order['completed_at'] = order['completed_at'].isoformat() if isinstance(order['completed_at'], datetime) else str(order['completed_at'])
                if order.get('status'):
                    order['status'] = order['status'].lower()
                if order.get('supplier_type'):
                    order['supplier_type'] = order['supplier_type'].lower().replace('-', '_')
                if order.get('total_amount'):
                    order['total_amount'] = float(order['total_amount'])

            return orders, total

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT o.id, o.order_code, o.caspar_order_no, o.status, o.error_message,
                       s.code as supplier_type, o.customer_name, o.item_count, o.total_amount,
                       o.portal_order_no, o.created_at, o.completed_at
                FROM orders o
                LEFT JOIN suppliers s ON o.supplier_id = s.id
                WHERE o.id = ?
            """, (order_id,))
            row = cursor.fetchone()
            if row:
                order = dict(zip([column[0] for column in cursor.description], row))
                if order.get('created_at'):
                    order['created_at'] = order['created_at'].isoformat() if isinstance(order['created_at'], datetime) else str(order['created_at'])
                if order.get('completed_at'):
                    order['completed_at'] = order['completed_at'].isoformat() if isinstance(order['completed_at'], datetime) else str(order['completed_at'])
                if order.get('status'):
                    order['status'] = order['status'].lower()
                if order.get('supplier_type'):
                    order['supplier_type'] = order['supplier_type'].lower().replace('-', '_')
                if order.get('total_amount'):
                    order['total_amount'] = float(order['total_amount'])
                return order
            return None

    def create_order(self, order_code: str, supplier_id: str, customer_name: str,
                     item_count: int = 0, total_amount: float = 0,
                     caspar_order_no: str = None) -> Dict[str, Any]:
        """Create a new order"""
        order_id = str(uuid.uuid4())
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO orders (id, order_code, caspar_order_no, status, supplier_id,
                                   customer_name, item_count, total_amount, created_at)
                VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?, GETDATE())
            """, (order_id, order_code, caspar_order_no, supplier_id, customer_name, item_count, total_amount))
        return self.get_order_by_id(order_id)

    def update_order_status(self, order_id: str, status: str, error_message: str = None,
                            portal_order_no: str = None) -> bool:
        """Update order status"""
        with self.get_cursor(commit=True) as cursor:
            if status.upper() == 'COMPLETED':
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, error_message = NULL, portal_order_no = ?, completed_at = GETDATE()
                    WHERE id = ?
                """, (status.upper(), portal_order_no, order_id))
            elif error_message:
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, (status.upper(), error_message, order_id))
            else:
                cursor.execute("""
                    UPDATE orders
                    SET status = ?, error_message = NULL
                    WHERE id = ?
                """, (status.upper(), order_id))
            return cursor.rowcount > 0

    def get_order_logs(self, order_id: str) -> List[Dict[str, Any]]:
        """Get logs for an order"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, order_id, action, status, message, details, screenshot_path, created_at
                FROM order_logs
                WHERE order_id = ?
                ORDER BY created_at ASC
            """, (order_id,))
            rows = cursor.fetchall()
            logs = self._rows_to_dicts(cursor, rows)

            for i, log in enumerate(logs):
                log['step'] = i + 1
                if log.get('created_at'):
                    log['timestamp'] = log['created_at'].isoformat() if isinstance(log['created_at'], datetime) else str(log['created_at'])
                if log.get('screenshot_path'):
                    log['screenshot'] = log['screenshot_path']

            return logs

    def add_order_log(self, order_id: str, action: str, status: str, message: str,
                      details: str = None, screenshot_path: str = None) -> str:
        """Add a log entry for an order"""
        log_id = str(uuid.uuid4())
        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO order_logs (id, order_id, action, status, message, details, screenshot_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (log_id, order_id, action, status.upper(), message, details, screenshot_path))
        return log_id

    # ============================================
    # AUDIT LOG OPERATIONS
    # ============================================

    def get_audit_logs(self, user: Optional[str] = None, action: Optional[str] = None,
                       page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """Get audit logs with pagination"""
        with self.get_cursor() as cursor:
            where_conditions = []
            params = []

            if user:
                where_conditions.append("u.username = ?")
                params.append(user)

            if action:
                where_conditions.append("a.action = ?")
                params.append(action)

            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)

            cursor.execute(f"""
                SELECT COUNT(*)
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                {where_clause}
            """, params)
            total = cursor.fetchone()[0]

            offset = (page - 1) * page_size
            cursor.execute(f"""
                SELECT a.id, u.username as [user], a.action, a.resource_type,
                       a.resource_id, a.details, a.ip_address, a.created_at as timestamp
                FROM audit_logs a
                LEFT JOIN users u ON a.user_id = u.id
                {where_clause}
                ORDER BY a.created_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, page_size])

            rows = cursor.fetchall()
            logs = self._rows_to_dicts(cursor, rows)

            for log in logs:
                if log.get('timestamp'):
                    log['timestamp'] = log['timestamp'].isoformat() if isinstance(log['timestamp'], datetime) else str(log['timestamp'])

            return logs, total

    def create_audit_log(self, user_id: Optional[int], action: str, resource_type: str = None,
                         resource_id: str = None, details: str = None, ip_address: str = None) -> str:
        """Create an audit log entry"""
        log_id = str(uuid.uuid4())

        with self.get_cursor(commit=True) as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id,
                                        details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (log_id, user_id, action, resource_type, resource_id, details, ip_address))

        return log_id

    # ============================================
    # STATS OPERATIONS
    # ============================================

    def get_today_stats(self) -> Dict[str, int]:
        """Get today's statistics"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) as today_orders,
                    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as today_successful,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as today_failed
                FROM orders
                WHERE CAST(created_at AS DATE) = CAST(GETDATE() AS DATE)
            """)
            order_stats = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) FROM orders WHERE status IN ('PENDING', 'PROCESSING')
            """)
            pending = cursor.fetchone()[0]

            cursor.execute("""
                SELECT s.code, COUNT(*) as count
                FROM orders o
                JOIN suppliers s ON o.supplier_id = s.id
                WHERE o.status = 'PENDING'
                GROUP BY s.code
            """)
            queue_rows = cursor.fetchall()
            queue_counts = {row[0].lower().replace('-', '_'): row[1] for row in queue_rows}

            cursor.execute("""
                SELECT COUNT(*) FROM emails
                WHERE CAST(received_at AS DATE) = CAST(GETDATE() AS DATE)
            """)
            today_emails = cursor.fetchone()[0]

            return {
                'today_orders': order_stats[0] or 0,
                'today_successful': order_stats[1] or 0,
                'today_failed': order_stats[2] or 0,
                'pending_orders': pending or 0,
                'today_emails': today_emails or 0,
                'queue_mutlu': queue_counts.get('mutlu_aku', queue_counts.get('mutlu', 0)),
                'queue_mann': queue_counts.get('mann_hummel', queue_counts.get('mann', 0)),
            }

    # ============================================
    # SUPPLIER OPERATIONS
    # ============================================

    def get_suppliers(self) -> List[Dict[str, Any]]:
        """Get all suppliers"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, code, name, portal_url, is_active
                FROM suppliers
                ORDER BY name
            """)
            rows = cursor.fetchall()
            suppliers = self._rows_to_dicts(cursor, rows)
            for supplier in suppliers:
                if supplier.get('code'):
                    supplier['code'] = supplier['code'].lower().replace('-', '_')
            return suppliers

    def get_supplier_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get supplier by code"""
        code = code.upper().replace('_', '-')
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, code, name, portal_url, is_active
                FROM suppliers
                WHERE code = ?
            """, (code,))
            row = cursor.fetchone()
            if row:
                return dict(zip([column[0] for column in cursor.description], row))
            return None


# Global database instance
db = SQLServerDB()
