# lab_2_9_mcp_mcpo_client.py
#
# 要先啟用mcpo server:
# 請在終端機輸入以下指令來啟動 mcpo。它會把上面的 stdio 腳本包裝成 http://localhost:8000 的 OpenAPI 網頁
# mcpo --port 8000 -- python mcp_stdio_mcpo_server.py
#
# 再執行本例:
# python lab_2_9_mcp_mcpo_client.py
#
import json
import requests

OLLAMA_BASE_URL = "http://172.10.0.2:8080"
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763" 
MODEL = "gemma4_e4b_ctx_2048:latest"

# mcpo 代理伺服器的網址
MCPO_BASE_URL = "http://localhost:8000"

def call_llm(messages: list, tools=None):
    payload = {"model": MODEL, "messages": messages, "temperature": 0.1}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat/completions", json=payload, headers={"Authorization": f"Bearer {API_KEY}"})
    return resp.json()

def get_tools_from_mcpo():
    """從 mcpo 的 openapi.json 動態解析並轉換為 LLM 格式"""
    try:
        resp = requests.get(f"{MCPO_BASE_URL}/openapi.json")
        openapi_spec = resp.json()
        
        openai_tools = []
        paths = openapi_spec.get("paths", {})
        
        for path, methods in paths.items():
            if "post" in methods:
                # mcpo 的路徑（如 /read_file）去除斜線就是工具名稱
                tool_name = path.lstrip("/")
                post_detail = methods["post"]
                
                # 取得工具描述
                description = post_detail.get("description", post_detail.get("summary", ""))
                
                # 解析參數 Schema
                # mcpo 產生的參數結構通常在 components/schemas 中
                ref_schema = {}
                try:
                    content_schema = post_detail["requestBody"]["content"]["application/json"]["schema"]
                    if "$ref" in content_schema:
                        ref_name = content_schema["$ref"].split("/")[-1]
                        ref_schema = openapi_spec["components"]["schemas"][ref_name]
                    else:
                        ref_schema = content_schema
                except KeyError:
                    ref_schema = {"type": "object", "properties": {}}

                openai_tools.append({
                    "name": tool_name,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": ref_schema.get("properties", {}),
                        "required": ref_schema.get("required", [])
                    }
                })
        return openai_tools
    except Exception as e:
        print(f"[警告] 無法從 mcpo 取得工具清單: {e}")
        return []

def main():
    print("=== Open WebUI mcpo (OpenAPI) 檔案讀取 Agent 啟動 ===")
    user_query = input("請輸入問題（例如：分析 mcp.txt）：\n")

    # 1. 透過 HTTP GET 向 mcpo 自動取得（發現）所有工具
    openai_tools = get_tools_from_mcpo()
    if not openai_tools:
        print("未偵測到任何可用工具，結束。")
        return

    messages = [
        {"role": "system", "content": "你是一個具有本地檔案讀取能力的 AI 助手。請善用工具回答。"},
        {"role": "user", "content": user_query}
    ]

    # 2. 第一次呼叫 LLM
    response = call_llm(messages, openai_tools)
    
    # 【修正點 1】加上 [0] 取得 choices 列表中的第一個元素
    message = response["choices"][0]["message"]

    if "tool_calls" in message and message["tool_calls"]:
        print("\n[Agent] LLM 決定呼叫 mcpo 工具...")
        messages.append(message)

        for tool_call in message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])
            
            # 防呆處理參數名稱
            filepath = args.get("filepath") or args.get("file_path") or args.get("file_name")

            print(f"[Agent] 正在向 mcpo 發送標準 HTTP POST 請求: /{tool_name}, 參數: {filepath}")
            
            # 3. 真正呼叫 mcpo 的 HTTP API 端點
            tool_resp = requests.post(
                f"{MCPO_BASE_URL}/{tool_name}",
                json={"filepath": filepath}
            )
            
            # 讀取 mcpo 吐回來的標準網頁 JSON 結果
            result_json = tool_resp.json()
            print(f"[Agent] mcpo 回傳結果: {json.dumps(result_json, ensure_ascii=False)}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.get("id", "call_123"),
                "name": tool_name,
                "content": json.dumps(result_json, ensure_ascii=False)
            })

        # 4. 第二次呼叫 LLM 進行最終分析
        final_response = call_llm(messages, openai_tools)
        print("\n=== LLM 最終回應 ===")
        # 【修正點 2】同樣加上 [0]
        print(final_response["choices"][0]["message"]["content"])
    else:
        print("\n=== LLM 回應 ===")
        print(message["content"])

if __name__ == "__main__":
    main()
