import os


def get_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


APP_ENV = os.getenv("APP_ENV", "development")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8787")
DATABASE_PATH = os.getenv("DATABASE_PATH", "server/orders.sqlite3")

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_LIFF_ID = os.getenv("LINE_LIFF_ID", "")
LINE_ADMIN_USER_ID = os.getenv("LINE_ADMIN_USER_ID", "")

LINE_PAY_CHANNEL_ID = os.getenv("LINE_PAY_CHANNEL_ID", "")
LINE_PAY_CHANNEL_SECRET = os.getenv("LINE_PAY_CHANNEL_SECRET", "")
LINE_PAY_CONFIRM_URL = os.getenv("LINE_PAY_CONFIRM_URL", f"{APP_BASE_URL}/linepay/confirm")
LINE_PAY_CANCEL_URL = os.getenv("LINE_PAY_CANCEL_URL", f"{APP_BASE_URL}/linepay/cancel")
LINE_PAY_SANDBOX = get_bool("LINE_PAY_SANDBOX", True)

