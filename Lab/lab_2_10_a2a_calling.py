# a2a_simple_demo.py
#
# pip install flask
#
import json
import requests
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

# ==================== 配置 ====================
OLLAMA_URL = "http://172.10.0.2:8080/api/chat/completions"
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763"
MODEL = "gemma4_e4b_ctx_2048:latest"

# ==================== Agent Card (A2A 核心) ====================
AGENT_CARD = {
    "name": "local_file_agent",
    "description": "一個專門處理本地檔案讀取與分析的 Agent",
    "skills": ["read_file", "analyze_text"],
    "version": "1.0",
    "endpoint": "http://localhost:5000/a2a"
}

# ==================== 簡單工具 ====================
def read_file(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()[:1000]
            #return f.read()[:4000]
    except Exception as e:
        return f"Error: {str(e)}"

# ==================== A2A Server Endpoint ====================
@app.route('/a2a', methods=['POST'])
def a2a_handler():
    data = request.json
    task = data.get("task", {})
    user_input = task.get("input", "")

    print(f"\n[Server] 收到 A2A 任務: {user_input}")

    file_content = ""
    if "mcp.txt" in user_input:
        print("[Server] 偵測到讀取 mcp.txt 的請求，正在讀取檔案...")
        file_content = read_file("mcp.txt")
        prompt = f"使用者任務：{user_input}\n\n以下是讀取到的檔案內容：\n---\n{file_content}\n---\n請針對以上內容進行詳細的總結。"
    else:
        prompt = user_input

    # 呼叫本地 LLM 處理
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一個專業的檔案處理 Agent，請根據提供的檔案內容進行精準的分析與總結。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "stream": False  # 💡 確保關閉串流
    }

    resp = requests.post(OLLAMA_URL, json=payload, headers={"Authorization": f"Bearer {API_KEY}"})
    result = resp.json()

    # 💡 新增：在 Server 端主動印出 LLM 的完整回傳內容，方便我們抓漏
    print("\n[Server Debug] Ollama 完整回傳內容:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    return jsonify({
        "status": "completed",
        "output": result["choices"][0]["message"]["content"],
        "artifacts": []
    })

@app.route('/agent-card', methods=['GET'])
def get_agent_card():
    return jsonify(AGENT_CARD)

# ==================== A2A Client 示範 ====================
def call_remote_agent(agent_url: str, task: str):
    payload = {
        "task": {
            "id": "task-001",
            "input": task
        }
    }
    resp = requests.post(f"{agent_url}/a2a", json=payload)
    return resp.json()

# ==================== 啟動 ====================
if __name__ == "__main__":
    print("=== A2A Agent 示範 ===")
    print("Agent Card:", json.dumps(AGENT_CARD, indent=2, ensure_ascii=False))
    
    # 在背景啟動 Server
    threading.Thread(target=lambda: app.run(port=5000, debug=False), daemon=True).start()
    
    print("\nA2A Server 已啟動在 http://localhost:5000")
    print("Agent Card: http://localhost:5000/agent-card")
    
    # 模擬 Client 呼叫
    input("\n按 Enter 模擬另一個 Agent 委派任務...")
    result = call_remote_agent("http://localhost:5000", "請讀取 mcp.txt 並總結內容")
    print("\n=== 收到遠端 Agent 回應 ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))