# =====================================================================
# 核心教學：安裝與設定 line business account & local LLM pseudo code
# =====================================================================

# 【步驟 1：申請line business account】

# 【步驟 2：設定line develop & channel】

# 【步驟 3：安裝 Python 必備套件】
pip3 install flask requests

# 【步驟 4：建立設定目錄與環境變數檔】
mkdir -p ~/.config/rc-bot

cat > ~/.config/rc-bot/config.env << 'EOF'
LINE_CHANNEL_SECRET=貼上你的_LINE_Channel_Secret
LINE_CHANNEL_ACCESS_TOKEN=貼上你的_LINE_Channel_Access_Token
ALLOWED_UID=先留空
OPENWEBUI_API_KEY=sk-f60ffbf03ede457987a23650b8b11763
OPENWEBUI_API_URL=http://127.0.0.1:3000/api/chat/completions
LLM_MODEL=gemma4_e4b_nothink:latest
EOF

chmod 600 ~/.config/rc-bot/config.env

# 【步驟 5：啟動本機 Webhook 服務】
python lab_3_3_llmservice4line_v1.py

# 【步驟 6：取得Allowed UID】
# 用手機開啟 LINE，對著你的 LINE Bot 傳送：#uid
# Bot 會回傳一串 Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx 的號碼。
# 回到 Ubuntu，編輯設定檔
# 將 ALLOWED_UID= 後面填入你剛才收到的那串 U 開頭的 UID。儲存離開。
vi ~/.config/rc-bot/config.env

# 【步驟 7：重啟本機 Webhook 服務】
# Ctrl+C 強制停止原本服務, 然後重啟
python lab_3_3_llmservice4line_v1.py
