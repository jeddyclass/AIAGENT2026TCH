# =====================================================================
# 核心教學：安裝與設定 ngrok pseudo code
# =====================================================================

# 【步驟 1：安裝 ngrok】
# 在 Ubuntu 上執行以下指令安裝 ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && echo "deb [signed-by=/etc/apt/trusted.gpg.d/ngrok.asc] https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list && sudo apt update && sudo apt install ngrok


# 【步驟 2：驗證 ngrok 帳號（Authtoken）】
# 請到 ngrok Dashboard 登入後取得你的 Authtoken，並在 Ubuntu 執行
# https://dashboard.ngrok.com/get-started/your-authtoken
ngrok config add-authtoken <你的_NGROK_AUTHTOKEN>

# 【步驟 3：測試啟動 ngrok】
# 執行以下指令對外公開 5050 埠
# 畫面上會出現一個 https://xxxx.ngrok-free.app 的網址。請先複製這個網址（注意：免費版 ngrok 每次重新啟動網址都會變）
# 請留著啟動視窗, 本次課程將觀察它的作動
ngrok http 5050

# 【步驟 4：查詢 ngrok 目前對外的隨機網址】
# 執行以下指令查看 ngrok 給你的臨時網址
# 這會輸出類似：https://a1b2-c3d4-e5f6.ngrok-free.app 的網址。
curl -s http://127.0.0.1:4040/api/tunnels | grep -o 'https://[^"]*ngrok-free.app'

# 【步驟 5：填入 LINE Developer Console】
# 回到 LINE Developers Console → 你的 Bot Channel → Messaging API 頁籤。
# 找到 Webhook settings，點選 Edit。
#
# 填入：https://<你的ngrok網址>/webhook
#
# 開啟 Use webhook (enable)。
# 點選 Verify 按鈕。如果畫面顯示 Success，代表 LINE 已經成功穿透網際網路連到你家裡的 Ubuntu 了！
