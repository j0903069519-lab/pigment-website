import hashlib
import hmac
import json
import mimetypes
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import config, db, line_bot, line_pay


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS_PATH = ROOT / "data" / "pigments.json"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_products():
    return json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))


def json_response(handler, status, payload):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, X-Line-Signature")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def build_order(payload):
    products = {product["id"]: product for product in load_products()}
    items = []
    for raw_item in payload.get("items", []):
        product = products.get(raw_item.get("id"))
        qty = int(raw_item.get("qty", 0))
        if product and qty > 0:
            items.append({"product": product, "qty": qty})
    if not items:
        raise ValueError("請先選擇至少一款顏料")

    total_qty = sum(item["qty"] for item in items)
    total_price = sum(item["product"]["price"] * item["qty"] for item in items)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    order_id = f"IH{timestamp}-{secrets.token_hex(2).upper()}"
    created_at = now_iso()
    return {
        "id": order_id,
        "lineUserId": payload.get("lineUserId", ""),
        "lineDisplayName": payload.get("lineDisplayName", ""),
        "recipient": payload.get("recipient", "").strip(),
        "phone": payload.get("phone", "").strip(),
        "address": payload.get("address", "").strip(),
        "note": payload.get("note", "").strip(),
        "items": items,
        "totalQty": total_qty,
        "totalPrice": total_price,
        "status": "pending_payment",
        "paymentMethod": "line_pay",
        "createdAt": created_at,
        "updatedAt": created_at,
    }


def verify_line_signature(headers, body):
    if not config.LINE_CHANNEL_SECRET:
        return config.APP_ENV == "development"
    signature = headers.get("X-Line-Signature", "")
    digest = hmac.new(
        config.LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    expected = __import__("base64").b64encode(digest).decode("utf-8")
    return hmac.compare_digest(signature, expected)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Line-Signature")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/products":
            json_response(self, 200, {"products": load_products()})
            return
        if parsed.path == "/api/config":
            json_response(self, 200, {"lineLiffId": config.LINE_LIFF_ID})
            return
        if parsed.path == "/api/orders":
            json_response(self, 405, {"error": "請使用 POST 建立訂單"})
            return
        if parsed.path == "/linepay/confirm":
            self.handle_linepay_confirm(parsed)
            return
        if parsed.path == "/linepay/cancel":
            self.serve_message_page("付款已取消", "你的訂單尚未付款，可以回到 LINE 重新操作。")
            return
        if parsed.path == "/admin/setup-rich-menu":
            self.handle_setup_rich_menu(parsed)
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/orders":
            self.handle_create_order()
            return
        if parsed.path == "/line/webhook":
            self.handle_line_webhook()
            return
        json_response(self, 404, {"error": "找不到這個 API"})

    def handle_create_order(self):
        try:
            payload = read_json(self)
            order = build_order(payload)
            db.save_order(order)
            payment = None
            payment_url = ""
            if line_pay.is_enabled():
                payment = line_pay.create_payment(order)
                payment_url = payment.get("info", {}).get("paymentUrl", {}).get("web", "")
            line_bot.notify_admin(line_bot.order_summary(order))
            json_response(
                self,
                201,
                {
                    "order": order,
                    "paymentUrl": payment_url,
                    "linePay": payment,
                },
            )
        except Exception as error:
            json_response(self, 400, {"error": str(error)})

    def handle_linepay_confirm(self, parsed):
        params = parse_qs(parsed.query)
        order_id = params.get("orderId", [""])[0]
        transaction_id = params.get("transactionId", [""])[0]
        order = db.get_order(order_id)
        if not order:
            self.serve_message_page("找不到訂單", "請回到 LINE 聯絡客服。")
            return
        try:
            if line_pay.is_enabled() and transaction_id:
                line_pay.confirm_payment(transaction_id, order)
            db.update_order_status(order_id, "paid", transaction_id, now_iso())
            order["status"] = "paid"
            line_bot.notify_admin("付款完成\n\n" + line_bot.order_summary(order))
            if order.get("line_user_id"):
                line_bot.push_text(order["line_user_id"], "付款完成，謝謝你的訂購。\n\n" + line_bot.order_summary(order))
            self.serve_message_page("付款完成", "你的訂單已成立，請回到 LINE 查看訂單確認訊息。")
        except Exception as error:
            json_response(self, 400, {"error": str(error)})

    def handle_line_webhook(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not verify_line_signature(self.headers, raw):
            json_response(self, 403, {"error": "LINE 簽章驗證失敗"})
            return
        payload = json.loads(raw.decode("utf-8") or "{}")
        for event in payload.get("events", []):
            if event.get("type") == "message" and event.get("message", {}).get("type") == "text":
                text = event["message"].get("text", "")
                if "客服" in text:
                    line_bot.reply_text(event["replyToken"], "客服已收到訊息，我們會盡快回覆。")
                elif "付款" in text:
                    line_bot.reply_text(
                        event["replyToken"],
                        "付款說明\n\n目前 LINE Pay 串接入口已預留，正式收款資料開通後就能直接線上付款。\n\n"
                        "現階段可先送出訂單，我們確認後會在 LINE 回覆付款方式。\n\n"
                        "顏料：每包 $120 / 15克",
                    )
                elif "選購" in text or "下單" in text:
                    if config.LINE_LIFF_ID:
                        line_bot.reply_text(event["replyToken"], f"請點這裡開始選購：\nhttps://liff.line.me/{config.LINE_LIFF_ID}")
                    else:
                        line_bot.reply_text(event["replyToken"], "請點下方選單「選購顏料」開始下單。")
                else:
                    line_bot.reply_text(event["replyToken"], "請點下方選單「選購顏料」開始下單，或輸入「客服」留下問題。")
        json_response(self, 200, {"ok": True})

    def handle_setup_rich_menu(self, parsed):
        params = parse_qs(parsed.query)
        token = params.get("token", [""])[0]
        if config.APP_ENV == "production":
            if not config.RICH_MENU_SETUP_TOKEN:
                json_response(self, 403, {"error": "請先在 Render 設定 RICH_MENU_SETUP_TOKEN"})
                return
            if not hmac.compare_digest(token, config.RICH_MENU_SETUP_TOKEN):
                json_response(self, 403, {"error": "管理密碼不正確"})
                return
        try:
            result = line_bot.setup_rich_menu()
            json_response(self, 200, {"ok": True, **result})
        except Exception as error:
            json_response(self, 400, {"error": str(error)})

    def serve_static(self, path):
        clean_path = path.lstrip("/") or "index.html"
        file_path = (ROOT / clean_path).resolve()
        if ROOT not in file_path.parents and file_path != ROOT:
            json_response(self, 403, {"error": "禁止存取"})
            return
        if not file_path.exists() or not file_path.is_file():
            json_response(self, 404, {"error": "找不到檔案"})
            return
        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_message_page(self, title, message):
        body = f"""<!doctype html>
<html lang="zh-Hant">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Noto Sans TC',sans-serif;padding:28px;line-height:1.7">
<h1>{title}</h1>
<p>{message}</p>
</body>
</html>""".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(port=None):
    if port is None:
        port = int(__import__("os").getenv("PORT", "8787"))
    db.connect().close()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"稻花香 LINE 商店後端：http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
