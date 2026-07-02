import json
import requests

# --- 配置參數 ---
OLLAMA_API = {
    "api_key": "sk-f60ffbf03ede457987a23650b8b11763",
    "ip": "http://172.10.0.2:8080",
    "model": "gemma4_e4b_ctx_2048:latest",
    "endpoint": "/api/chat/completions"
}

def call_llm_tool(prompt, tools_definition):
    """
    模擬調用地端 LLM 決定要呼叫哪個 A2A 函數。
    在實際場景中，我們需要一個機制來模擬 Tool Calling 的輸出。
    """
    print("\n--- 🛠️ 模擬 LLM 決定使用 Tool Calling ---")
    print(f"Prompt 傳給 LLM: {prompt[:50]}...")
    
    # 實際的 LLM 呼叫會在這裡發生，它會輸出 JSON 格式的工具呼叫指令
    # 為了模擬，我們假設 LLM 已經決定要調用 A2A 的 message/send
    
    return {
        "tool_name": "A2A_Protocol",
        "method": "message/send",
        "parameters": {
            "contextId": "hello_test_001",
            "message": "Hello, I am Agent 1. Can you confirm your identity?",
            "expectedResponseType": "Confirmation Message"
        }
    }

def simulate_agent_interaction_1():
    print("===========================================")
    print("===== 情境一：Say Hello (Message Exchange) =====")
    print("===========================================")

    # 1. 模擬 Agent 1 接收到指令 (User -> A1)
    user_prompt = "請幫我測試一下 Agent 2 是否能正常回應，用一個簡單的問候語開始。"
    
    # 2. 模擬 A1 決定使用 Tool/Function (A1 內部邏輯)
    tool_call = call_llm_tool(user_prompt, None)
    
    if tool_call["method"] == "message/send":
        params = tool_call["parameters"]
        print("\n[A1 執行] 準備調用 A2A: message/send...")
        
        # 3. 模擬 A1 呼叫 Agent 2 (A1 -> A2)
        print(f"[A1 -> A2] 發送 A2A 請求：{json.dumps(params)}")
        
        # 4. 模擬 A2 收到請求並回覆 (A2 -> A1)
        print("\n[A2 內部處理] 接收到請求，根據 AgentCard 回應一個問候語...")
        a2_response = {
            "status": "SUCCESS",
            "contextId": params["contextId"],
            "response_type": "Message",
            "data": {
                "message": "Greetings! I am Agent 2, I confirm my identity. I specialize in logistics.",
                "source": "AgentCard Read"
            }
        }
        
        # 5. 模擬 A1 收到並展示給使用者 (A2 -> A1 -> User)
        print("\n[A1 收到] 成功接收到 Agent 2 的回應。")
        print("="*50)
        print(f"✅ 最終展示給使用者: {a2_response['data']['message']}")
        print("="*50)

# simulate_agent_interaction_1()