import json
import sqlite3
from pathlib import Path

from . import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  line_user_id TEXT,
  line_display_name TEXT,
  recipient TEXT NOT NULL,
  phone TEXT NOT NULL,
  address TEXT NOT NULL,
  note TEXT,
  items_json TEXT NOT NULL,
  total_qty INTEGER NOT NULL,
  total_price INTEGER NOT NULL,
  status TEXT NOT NULL,
  payment_method TEXT NOT NULL,
  linepay_transaction_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def connect():
    db_path = Path(config.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    return conn


def save_order(order):
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO orders (
              id, line_user_id, line_display_name, recipient, phone, address,
              note, items_json, total_qty, total_price, status, payment_method,
              linepay_transaction_id, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order["id"],
                order.get("lineUserId"),
                order.get("lineDisplayName"),
                order["recipient"],
                order["phone"],
                order["address"],
                order.get("note", ""),
                json.dumps(order["items"], ensure_ascii=False),
                order["totalQty"],
                order["totalPrice"],
                order["status"],
                order["paymentMethod"],
                order.get("linepayTransactionId"),
                order["createdAt"],
                order["updatedAt"],
            ),
        )


def get_order(order_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not row:
        return None
    order = dict(row)
    order["items"] = json.loads(order.pop("items_json"))
    return order


def update_order_status(order_id, status, transaction_id=None, updated_at=None):
    with connect() as conn:
        if transaction_id:
            conn.execute(
                """
                UPDATE orders
                SET status = ?, linepay_transaction_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, transaction_id, updated_at, order_id),
            )
        else:
            conn.execute(
                "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                (status, updated_at, order_id),
            )

