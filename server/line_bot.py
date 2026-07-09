import json
import urllib.request

from . import config


LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def is_enabled():
    return bool(config.LINE_CHANNEL_ACCESS_TOKEN)


def post_line(url, payload):
    if not is_enabled():
        return None
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def reply_text(reply_token, text):
    return post_line(
        LINE_REPLY_URL,
        {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text[:5000]}],
        },
    )


def push_text(user_id, text):
    return post_line(
        LINE_PUSH_URL,
        {
            "to": user_id,
            "messages": [{"type": "text", "text": text[:5000]}],
        },
    )


def notify_admin(text):
    if config.LINE_ADMIN_USER_ID:
        return push_text(config.LINE_ADMIN_USER_ID, text)
    return None


def order_summary(order):
    lines = [
        "稻花香顏料訂單",
        f"訂單編號：{order['id']}",
        f"狀態：{order['status']}",
        "",
        "商品：",
    ]
    for index, item in enumerate(order["items"], 1):
        product = item["product"]
        lines.append(
            f"{index}. {product['name']}（{product['color']} / 色號 {product['code']} / {product.get('weight', '')}） x {item['qty']} 包"
        )
    lines.extend(
        [
            "",
            f"總包數：{order['totalQty']} 包",
            f"應付金額：${order['totalPrice']}",
            "",
            f"收件人：{order['recipient']}",
            f"電話：{order['phone']}",
            f"地址：{order['address']}",
            f"備註：{order.get('note') or '無'}",
        ]
    )
    return "\n".join(lines)

