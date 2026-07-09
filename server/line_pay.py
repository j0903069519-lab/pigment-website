import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request
import uuid

from . import config


def is_enabled():
    return bool(config.LINE_PAY_CHANNEL_ID and config.LINE_PAY_CHANNEL_SECRET)


def api_base():
    if config.LINE_PAY_SANDBOX:
        return "https://sandbox-api-pay.line.me"
    return "https://api-pay.line.me"


def sign(secret, uri, body, nonce):
    message = f"{secret}{uri}{body}{nonce}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def request_api(method, path, payload=None):
    if not is_enabled():
        raise RuntimeError("LINE Pay 尚未設定，請填入 LINE_PAY_CHANNEL_ID 與 LINE_PAY_CHANNEL_SECRET")
    body = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":"))
    nonce = str(uuid.uuid4())
    request = urllib.request.Request(
        f"{api_base()}{path}",
        data=body.encode("utf-8") if method != "GET" else None,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-LINE-ChannelId": config.LINE_PAY_CHANNEL_ID,
            "X-LINE-Authorization-Nonce": nonce,
            "X-LINE-Authorization": sign(config.LINE_PAY_CHANNEL_SECRET, path, body, nonce),
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def create_payment(order):
    payload = {
        "amount": order["totalPrice"],
        "currency": "TWD",
        "orderId": order["id"],
        "packages": [
            {
                "id": order["id"],
                "amount": order["totalPrice"],
                "name": "稻花香顏料",
                "products": [
                    {
                        "id": item["product"]["id"],
                        "name": f"{item['product']['name']} {item['product']['code']}",
                        "quantity": item["qty"],
                        "price": item["product"]["price"],
                    }
                    for item in order["items"]
                ],
            }
        ],
        "redirectUrls": {
            "confirmUrl": config.LINE_PAY_CONFIRM_URL,
            "cancelUrl": config.LINE_PAY_CANCEL_URL,
        },
        "options": {
            "payment": {
                "capture": True,
            }
        },
    }
    return request_api("POST", "/v3/payments/request", payload)


def confirm_payment(transaction_id, order):
    quoted_transaction_id = urllib.parse.quote(str(transaction_id), safe="")
    path = f"/v3/payments/{quoted_transaction_id}/confirm"
    payload = {
        "amount": order["totalPrice"],
        "currency": "TWD",
    }
    return request_api("POST", path, payload)

