# LINE 內商店上線設定

這份網站可以升級成 LINE 內完成選購、下單、付款與客服的系統。正式上線時需要以下外部設定。

## 需要申請

- LINE 官方帳號
- LINE Developers 的 Messaging API channel
- LINE Login channel 與 LIFF app
- LINE Pay 商家帳號
- 一個可以跑 Python 後端的主機

## LINE 官方帳號

1. 建立官方帳號。
2. 啟用 Messaging API。
3. 將 webhook URL 設成：

```text
https://你的後端網址/line/webhook
```

4. 將 Channel access token 填到環境變數：

```text
LINE_CHANNEL_ACCESS_TOKEN=
LINE_CHANNEL_SECRET=
```

## LINE 底部選單

網站後台可以自動建立官方帳號的 Rich Menu，不需要在 LINE 後台手動切圖與設定點擊範圍。

1. 在 Render 的 Environment 加入一組管理密碼：

```text
RICH_MENU_SETUP_TOKEN=自行設定一組長一點的密碼
```

2. Render 重新部署完成後，用瀏覽器打開：

```text
https://你的後端網址/admin/setup-rich-menu?token=你的管理密碼
```

3. 回傳 `ok: true` 後，LINE 官方帳號的底部選單會建立成三格：

- 選購顏料：開啟 LIFF 商店
- 客服：傳送客服訊息
- 付款說明：傳送付款說明訊息

## LIFF

1. 在 LINE Login channel 新增 LIFF app。
2. Endpoint URL 設為網站首頁：

```text
https://你的後端網址/
```

3. View size 建議選 Full。
4. 將 LIFF ID 填到：

```text
LINE_LIFF_ID=
```

## LINE Pay

取得 LINE Pay 商家資訊後填入：

```text
LINE_PAY_CHANNEL_ID=
LINE_PAY_CHANNEL_SECRET=
LINE_PAY_SANDBOX=false
LINE_PAY_CONFIRM_URL=https://你的後端網址/linepay/confirm
LINE_PAY_CANCEL_URL=https://你的後端網址/linepay/cancel
```

測試時可先使用 sandbox：

```text
LINE_PAY_SANDBOX=true
```

## 本機啟動

```sh
python3 -m server.app
```

本機網址：

```text
http://127.0.0.1:8787/
```

## 客人流程

1. 加 LINE 官方帳號。
2. 點 Rich Menu 的「選購顏料」。
3. LIFF 開啟顏料選購頁。
4. 送出訂單。
5. 系統建立訂單並導向 LINE Pay。
6. 付款成功後，機器人傳送訂單確認。
7. 客服在同一個 LINE 對話裡接續處理。
