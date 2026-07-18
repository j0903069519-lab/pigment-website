import json
import struct
import urllib.request
import zlib

from . import config


LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"
LINE_RICH_MENU_URL = "https://api.line.me/v2/bot/richmenu"
LINE_RICH_MENU_DEFAULT_URL = "https://api.line.me/v2/bot/user/all/richmenu"
LINE_DATA_URL = "https://api-data.line.me/v2/bot/richmenu"


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


def request_line(url, method="GET", payload=None, content_type="application/json"):
    if not is_enabled():
        raise RuntimeError("LINE_CHANNEL_ACCESS_TOKEN 尚未設定")
    data = None
    if payload is not None:
        if content_type == "application/json":
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        else:
            data = payload
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": content_type,
            "Authorization": f"Bearer {config.LINE_CHANNEL_ACCESS_TOKEN}",
        },
        method=method,
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8")
        return json.loads(body or "{}")


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


def setup_rich_menu():
    if not config.LINE_LIFF_ID:
        raise RuntimeError("LINE_LIFF_ID 尚未設定")

    delete_existing_rich_menus("稻花香顏料選單")
    rich_menu = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "稻花香顏料選單",
        "chatBarText": "選單",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 834, "height": 843},
                "action": {"type": "uri", "uri": f"https://liff.line.me/{config.LINE_LIFF_ID}"},
            },
            {
                "bounds": {"x": 834, "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "客服"},
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
                "action": {"type": "message", "text": "付款說明"},
            },
        ],
    }
    created = request_line(LINE_RICH_MENU_URL, method="POST", payload=rich_menu)
    rich_menu_id = created["richMenuId"]
    image = build_rich_menu_image()
    request_line(
        f"{LINE_DATA_URL}/{rich_menu_id}/content",
        method="POST",
        payload=image,
        content_type="image/png",
    )
    request_line(f"{LINE_RICH_MENU_DEFAULT_URL}/{rich_menu_id}", method="POST", payload={})
    return {"richMenuId": rich_menu_id, "liffUrl": f"https://liff.line.me/{config.LINE_LIFF_ID}"}


def delete_existing_rich_menus(name):
    try:
        result = request_line(f"{LINE_RICH_MENU_URL}/list")
    except Exception:
        return
    for item in result.get("richmenus", []):
        if item.get("name") == name:
            request_line(f"{LINE_RICH_MENU_URL}/{item['richMenuId']}", method="DELETE")


def build_rich_menu_image():
    width = 2500
    height = 843
    sections = [
        ((246, 250, 246), (50, 111, 96), "SHOP", "Order pigments"),
        ((255, 253, 248), (200, 95, 59), "HELP", "Talk to us"),
        ((244, 239, 227), (66, 111, 159), "INFO", "Payment & shipping"),
    ]
    pixels = bytearray()
    for y in range(height):
        row = bytearray()
        for x in range(width):
            section_index = min(2, x * 3 // width)
            background, accent, title, subtitle = sections[section_index]
            color = background
            local_x = x - section_index * (width // 3)
            if y < 18 or y > height - 18 or local_x < 18 or local_x > (width // 3) - 18:
                color = accent
            row.extend(color)
        pixels.extend(b"\x00" + row)

    for index, (_, accent, title, subtitle) in enumerate(sections):
        center_x = int((index + 0.5) * width / 3)
        draw_text(pixels, width, height, center_x - len(title) * 28, 300, title, accent, scale=9)
        draw_text(pixels, width, height, center_x - len(subtitle) * 12, 455, subtitle, (60, 60, 60), scale=4)

    return encode_png(width, height, bytes(pixels))


FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def draw_text(pixels, width, height, x, y, text, color, scale=4):
    cursor = x
    for char in text.upper():
        glyph = FONT.get(char, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    fill_rect(pixels, width, height, cursor + gx * scale, y + gy * scale, scale, scale, color)
        cursor += 6 * scale


def fill_rect(pixels, width, height, x, y, rect_width, rect_height, color):
    for py in range(max(0, y), min(height, y + rect_height)):
        for px in range(max(0, x), min(width, x + rect_width)):
            offset = py * (1 + width * 3) + 1 + px * 3
            pixels[offset:offset + 3] = bytes(color)


def encode_png(width, height, raw_scanlines):
    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw_scanlines, 9))
        + chunk(b"IEND", b"")
    )


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
