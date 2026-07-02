# lab_2_7_mcp_stdio_client.py
#
# 執行方式：直接執行 python lab_2_7_mcp_stdio_client.py，它會自動在背景叫起 mcp_stdio_server.py 進行通訊。
#
import json
import requests
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

OLLAMA_BASE_URL = "http://172.10.0.2:8080/"
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763" 
MODEL = "gemma4_e4b_ctx_2048:latest"

def call_llm(messages: list, tools=None):
    payload = {"model": MODEL, "messages": messages, "temperature": 0.1}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat/completions", json=payload, headers={"Authorization": f"Bearer {API_KEY}"})
    return resp.json()

async def main():
    print("=== MCP stdio 檔案讀取 Agent 啟動 ===")
    user_query = input("請輸入問題（例如：分析 mcp.txt）：\n")

    # 1. 設定要啟動的地端 Server 指令
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_stdio_server.py"]
    )

    # 2. 透過 stdio 啟動並連接 Server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # 初始化並獲取 Server 上的所有工具
            await session.initialize()
            mcp_tools = await session.list_tools()

            # 3. 將 MCP 工具格式轉換為 LLM 看得懂的 OpenAI 格式
            openai_tools = []
            for t in mcp_tools.tools:
                openai_tools.append({
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema
                })

            messages = [
                {"role": "system", "content": "你是一個具有本地檔案讀取能力的 AI 助手。請善用工具回答。回答時請以繁體中文為主。"},
                {"role": "user", "content": user_query}
            ]

            # 4. 第一次呼叫 LLM
            response = call_llm(messages, openai_tools)
            message = response["choices"][0]["message"]

            if "tool_calls" in message and message["tool_calls"]:
                print("\n[Agent] LLM 決定呼叫 MCP 工具...")
                
                # 收集所有工具執行後的文字內容
                all_tool_results = []

                for tool_call in message["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"[Debug] LLM 回傳的原始參數: {args}")

                    filepath = args.get("filepath") or args.get("file_path") or args.get("file_name")
                    if not filepath:
                        filepath = "mcp.txt"

                    print(f"[Agent] 正在透過 MCP 請求工具: {tool_name}, 參數: {filepath}")
                    
                    mcp_result = await session.call_tool(tool_name, arguments={"filepath": filepath})
                    result_text = mcp_result.content[0].text if mcp_result.content else ""
                    
                    print(f"[Agent] MCP 工具回傳長度: {len(result_text)}")
                    
                    # 將讀取到的內容存入暫存陣列
                    all_tool_results.append(f"--- 檔案 [{filepath}] 內容開始 ---\n{result_text}\n--- 檔案 [{filepath}] 內容結束 ---")

                # ================= 關鍵修正：完全跳出 for 迴圈 =================
                print("[Agent] 正在重組對話歷史（進行文字切片防止爆 Window），準備進行最終分析...")
                
                # 【防爆機制】如果單一檔案內容太長，只取前 1000 個字，並提醒模型這是摘要
                truncated_results = []
                for res in all_tool_results:
                    if len(res) > 1000:
                        truncated_results.append(res[:1000] + "\n\n...(因地端模型長度限制，上方僅截取檔案前 1000 字，請針對這部分分析)...")
                    else:
                        truncated_results.append(res)

                tool_results_text = '\n\n'.join(truncated_results)

                # 重建一個乾淨的對話紀錄給第二次呼叫
                final_messages = [
                    {"role": "system", "content": "你是一個具有本地檔案讀取能力的 AI 助手。請根據提供的檔案內容回答問題。請以繁體中文詳細回覆。"},
                    {"role": "user", "content": f"以下是系統為你讀取到的本地檔案資料：\n\n{tool_results_text}\n\n請根據上方檔案內容，回答我最初的問題：『{user_query}』"}
                ]
                
                # 6. 第二次呼叫 LLM 進行最終分析
                final_response = call_llm(final_messages, openai_tools)
                print("\n=== LLM 最終回應 ===")
                print(final_response["choices"][0]["message"]["content"])
            else:
                print("\n=== LLM 回應 ===")
                print(message["content"])

if __name__ == "__main__":
    asyncio.run(main())
