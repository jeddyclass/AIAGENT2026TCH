# lab_2_3_mcp_calling.py
import json
import requests
from typing import Dict, Any
import os

# ==================== 配置 ====================
OLLAMA_BASE_URL = "http://localhost:8080/"
API_KEY = "sk-1540f219fcb246b9bb55c7951491c01b" 
MODEL = "gemma4_e4b_ctx_128k_nothink:latest"

# ==================== 簡單 MCP Tool Server ====================
def read_file_tool(params: Dict) -> Dict:
    """讀取本地檔案的工具"""
    # 💥 極致防呆：把模型可能亂發明的參數名稱全部包容進來
    filepath = params.get("filepath") or params.get("file_path") or params.get("file_name")
    
    if not filepath:
        return {"error": "找不到參數 'filepath'、'file_path' 或 'file_name'"}
        
    try:
        if not os.path.exists(filepath):
            # 順便列出當前目錄有什麼檔案，幫 LLM 導航
            current_files = os.listdir('.')
            return {"error": f"檔案不存在: {filepath}。當前目錄下的檔案有: {current_files}"}
            
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content[:8000]}  # 避免太長
    except Exception as e:
        return {"error": str(e)}

# 工具對照表
TOOL_MAP = {
    "read_file": read_file_tool
}

TOOLS = [
    {
        "name": "read_file",
        "description": "讀取本地檔案內容",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "檔案完整路徑或檔名"}
            },
            "required": ["filepath"]
        }
    }
]

# ==================== 呼叫 LLM ====================
def call_llm(messages: list, tools=None):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.1,  # 保持低隨機性
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    return resp.json()

# ==================== 主流程 ====================
def main():
    print("=== MCP 檔案讀取 Agent 示範 ===")
    user_query = input("請輸入問題（例如：請幫我讀取 /tmp/test.txt 的內容）：\n")

    messages = [
        {
            "role": "system", 
            "content": (
                "你是一個具有本地檔案讀取能力的 AI 助手。\n"
                "當使用者要求你『分析』、『看』、『讀取』、『summary』或提及任何檔案名稱時，"
                "你必須使用 read_file 工具來獲取檔案內容。請直接調用工具，不要向用戶問問題。"
            )
        },
        {"role": "user", "content": user_query}
    ]

    # 第一次呼叫：詢問 LLM 該做什麼
    response = call_llm(messages, TOOLS)
    
    choice = response["choices"][0] # 確保取到第 0 個
    message = choice["message"]

    # 檢查 LLM 是否要求呼叫工具
    if "tool_calls" in message and message["tool_calls"]:
        print("\n[Agent] LLM 決定呼叫工具...")
        
        # 必須把 LLM 含有 tool_calls 的回應原封不動加入歷史
        messages.append(message)
        
        # 處理 tool_calls
        for tool_call in message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            
            # 解析參數
            args_raw = tool_call["function"]["arguments"]
            tool_args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
            
            print(f"[Agent] 正在執行工具: {tool_name}, 參數: {tool_args}")
            
            # 執行工具
            if tool_name in TOOL_MAP:
                tool_result = TOOL_MAP[tool_name](tool_args)
                print(f"[Agent] 工具執行結果: {json.dumps(tool_result, ensure_ascii=False)}")
                
                # 回傳給相容 OpenAI 格式的標準寫法
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", "call_123"), # 防呆確保有 id
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
            else:
                print(f"[錯誤] 未定義的工具: {tool_name}")

        # 第二次呼叫：讓模型看著工具結果做最後回答
        print("\n[Agent] 正在將檔案內容交還給 LLM 進行分析...")
        final_response = call_llm(messages, TOOLS)
        
        print("\n=== LLM 最終回應 ===")
        print(final_response["choices"][0]["message"]["content"])

    else:
        # 如果 LLM 沒有要用工具
        print("\n=== LLM 回應 ===")
        print(message["content"])

if __name__ == "__main__":
    main()
