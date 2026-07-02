#
# 要先啟用mcp sse server:
# 請在單獨一個的終端機輸入以下指令來啟動 
# python mcp_sse_server.py
#
# 再在另一個終端機執行本例:
# python lab_2_8_mcp_sse_client.py
#
import json
import requests
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

OLLAMA_BASE_URL = "http://172.10.0.2:8080"
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763"  
MODEL = "gemma4_e4b_ctx_2048:latest"
MCP_SSE_URL = "http://localhost:8000/sse"

def call_llm(messages: list, tools=None):
    url = f"{OLLAMA_BASE_URL}/api/chat/completions" 

    # 調整 payload，加入 options 確保 Ollama 願意吐出更多字，且限制上下文
    payload = {
        "model": MODEL, 
        "messages": messages, 
        "temperature": 0.1,
        "options": {
            "num_ctx": 2048,      # 限制上下文視窗
            "num_predict": 2048    # 允許單次最多回覆 2048 個 Token，防止斷頭
        }
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
        
    resp = requests.post(url, json=payload, headers={"Authorization": f"Bearer {API_KEY}"})
    return resp.json()

async def main():
    print("=== MCP SSE 檔案讀取 Agent 啟動 ===")
    user_query = input("請輸入問題（例如：分析 mcp.txt）：\n")

    async with sse_client(url=MCP_SSE_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            mcp_tools = await session.list_tools()

            openai_tools = []
            for t in mcp_tools.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })

            messages = [
                {"role": "system", "content": "你是一個具有本地檔案讀取能力的 AI 助手。請用繁體中文簡短回答。"},
                {"role": "user", "content": user_query}
            ]

            response = call_llm(messages, openai_tools)
            
            if "choices" not in response:
                print("LLM 呼叫失敗，回應內容：", response)
                return
                
            message = response["choices"][0]["message"]

            if "tool_calls" in message and message["tool_calls"]:
                print("\n[Agent] LLM 決定呼叫遠端 MCP 工具...")
                messages.append(message)

                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"]["arguments"])
                    filepath = args.get("filepath") or args.get("file_path") or args.get("file_name") or list(args.values())[0]

                    print(f"[Agent] 正在透過 SSE 請求工具: {tool_name}, 參數: {filepath}")
                    
                    mcp_result = await session.call_tool(tool_name, arguments={"filepath": filepath})
                    result_text = mcp_result.content[0].text if mcp_result.content else ""

                    # 【核心防禦】：如果檔案太大，強行截斷前 800 個字，避免 2048 視窗爆掉
                    if len(result_text) > 800:
                        result_text = result_text[:800] + "\n... (因長度限制，後續內容已省略) ..."

                    injection_prompt = f"\n\n【系統提示：已讀取檔案 {filepath}】:\n\"\"\"\n{result_text}\n\"\"\"\n請用繁體中文簡短總結或回答：{user_query}"
                    
                    messages.append({
                        "role": "user",
                        "content": injection_prompt
                    })

                # 第二輪呼叫
                final_response = call_llm(messages, tools=None)
                
                print("\n=== LLM 最終回應 ===")
                if "choices" in final_response:
                    print(final_response["choices"][0]["message"]["content"])
                else:
                    print("第二輪呼叫錯誤：", final_response)
            else:
                print("\n=== LLM 回應 ===")
                print(message["content"])

if __name__ == "__main__":
    asyncio.run(main())