# mcp_a2a_weather_demo.py
import json
import requests
from flask import Flask, request, jsonify
import threading
import os

app = Flask(__name__)

OLLAMA_URL = "http://172.10.0.2:8080/api/chat/completions"
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763"
MODEL = "gemma4_e4b_ctx_2048:latest"

# ==================== MCP Tool (天氣工具) ====================
def get_weather(location: str):
    # 使用 Open-Meteo 免費 API（無需 Key）
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude=24.15&longitude=120.68&current=temperature_2m,weather_code"
        # 實際可動態抓經緯度，這裡簡化用台中座標
        resp = requests.get(url, timeout=5)
        data = resp.json()
        temp = data["current"]["temperature_2m"]
        return f"台中目前溫度約 {temp}°C"
    except:
        return "無法取得天氣資訊"

# ==================== A2A Weather Agent ====================
@app.route('/agent-card', methods=['GET'])
def agent_card():
    return jsonify({
        "name": "weather_specialist",
        "description": "專門處理天氣查詢的 Agent",
        "skills": ["get_current_weather"],
        "endpoint": "http://localhost:5001/a2a"
    })

@app.route('/a2a', methods=['POST'])
def a2a_handler():
    data = request.json
    task_input = data["task"]["input"]
    
    print(f"[Weather Agent] 收到任務: {task_input}")
    
    # 透過 MCP 概念呼叫工具（這裡簡化直接呼叫，實際應走 MCP Client）
    weather_info = get_weather("Taichung")
    
    return jsonify({
        "status": "completed",
        "output": f"天氣查詢結果：{weather_info}",
        "artifacts": [{"type": "weather_data", "content": weather_info}]
    })

# ==================== Orchestrator (主 Agent) ====================
def call_orchestrator(user_query):
    messages = [
        {"role": "system", "content": "你是總指揮 Agent，遇到專業任務就委派給其他 A2A Agent。"},
        {"role": "user", "content": user_query}
    ]
    
    # 簡化：直接假設需要委派給 weather agent
    print("\n[Orchestrator] 決定委派給 Weather Agent...")
    
    # 呼叫 A2A
    resp = requests.post("http://localhost:5001/a2a", json={
        "task": {"id": "task-weather-001", "input": user_query}
    })
    
    result = resp.json()
    print("\n=== 最終回覆 ===")
    print(result["output"])

# ==================== 啟動 ====================
if __name__ == "__main__":
    print("啟動 Weather A2A Agent (port 5001)...")
    threading.Thread(target=lambda: app.run(port=5001, debug=False), daemon=True).start()
    
    query = "台中今天天氣如何？"
    print(f"使用者問題：{query}")
    call_orchestrator(query)