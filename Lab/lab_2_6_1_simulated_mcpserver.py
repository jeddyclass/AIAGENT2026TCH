import asyncio
import anyio
import math
import os
from mcp.server import Server
from mcp.client.session import ClientSession
from mcp.types import Tool, Resource, Prompt, TextContent, GetPromptResult, PromptMessage

# 0. 建立在地端（當前路徑）的實體測試檔案
TEST_FILENAME = "mcp_local_test_log.txt"
TEST_FILE_PATH = os.path.abspath(TEST_FILENAME)

with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
    f.write("【真實地端日誌】CPU 使用率 8%, 溫度 42°C, 跨平台 Gemma4 模擬一切正常。")

# =====================================================================
# 1. SERVER 端設計
# =====================================================================
server_app = Server("mock-local-server")

# --- Resources (唯讀資源) ---
@server_app.list_resources()
async def list_resources():
    return [Resource(uri=f"file://{TEST_FILE_PATH}", name="系統狀態日誌", mimeType="text/plain")]

@server_app.read_resource()
async def read_resource(uri):
    uri_str = str(uri)
    
    if TEST_FILENAME in uri_str:
        try:
            with open(TEST_FILE_PATH, "r", encoding="utf-8") as f:
                content_data = f.read()
            # 💡 終極修正：直接回傳純文字內容，這是目前 Python mcp SDK 最穩定、最不會噴 Tuple 錯誤的寫法
            return content_data
        except Exception as e:
            return f"【錯誤】讀取地端檔案失敗: {str(e)}"
    raise ValueError(f"找不到資源，Server 收到的是: {uri_str}")

# --- Tools (動態工具) ---
@server_app.list_tools()
async def list_tools():
    return [
        Tool(
            name="calculate_heavy_task",
            description="執行地端的複雜數學計算（大腦不擅長算術時使用）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "number": {"type": "integer", "description": "輸入數字"}
                },
                "required": ["number"]
            }
        )
    ]

@server_app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "calculate_heavy_task":
        num = arguments.get("number", 0)
        result = num * 42 
        return [TextContent(type="text", text=f"【地端計算結果】{num} 乘以 42 等於 {result}")]
    raise ValueError("未知工具")

# --- Prompts (提示詞範本) ---
@server_app.list_prompts()
async def list_prompts():
    return [Prompt(name="analyst_mode", description="切換為數據分析師模式")]

@server_app.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "analyst_mode":
        return GetPromptResult(
            description="分析師提示詞模板",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text="你現在是一名精密的數據分析師，請用嚴謹的邏輯回答問題。")
                )
            ]
        )
    raise ValueError("找不到模板")


# =====================================================================
# 2. CLIENT 端設計與運行模擬流程
# =====================================================================
async def main():
    print("🚀 [系統] 正在啟動地端 MCP 全套 (anyio 管道) 模擬...")

    c2s_send, c2s_receive = anyio.create_memory_object_stream(math.inf)
    s2c_send, s2c_receive = anyio.create_memory_object_stream(math.inf)

    server_task = asyncio.create_task(server_app.run(
        c2s_receive, 
        s2c_send, 
        server_app.create_initialization_options()
    ))

    async with ClientSession(s2c_receive, c2s_send) as session:
        await session.initialize()
        print("✅ [Client] 與 Server 連線成功，完成初始化握手！\n" + "-"*50)

        # -------------------------------------------------------------
        # 演示功能 1: Prompts
        # -------------------------------------------------------------
        print("🔍 [流程 1] Client 向 Server 索取 'analyst_mode' 提示詞範本...")
        prompts = await session.list_prompts()
        print(f"👉 Server 回報可用的 Prompts: {[p.name for p in prompts.prompts]}")
        
        target_prompt = await session.get_prompt(name="analyst_mode", arguments={})
        print(f"📥 取得的 System Prompt 內容: '{target_prompt.messages[0].content.text}'\n" + "-"*50)

        # -------------------------------------------------------------
        # 演示功能 2: Resources
        # -------------------------------------------------------------
        print("🔍 [流程 2] Client 讀取 Server 的地端系統日誌資源...")
        resources = await session.list_resources()
        print(f"👉 Server 回報可用的 Resources: {[r.name for r in resources.resources]}")
        
        target_uri = f"file://{TEST_FILE_PATH}"
        log_res = await session.read_resource(uri=target_uri)
        
        # 💡 修正：ClientSession 在解包 read_resource 時，會把回傳值轉為 ReadResourceResult 物件。
        # 依據最新 SDK 版本，其文字內容可能直接在 contents[0].text 中。
        try:
            print(f"📥 真正讀取到地端檔案內容:\n   {log_res.contents[0].text}\n" + "-"*50)
        except AttributeError:
            # 防禦性寫法：若 SDK 直接把內容解成別的型態，則直接列印物件
            print(f"📥 真正讀取到地端檔案內容:\n   {log_res}\n" + "-"*50)

        # -------------------------------------------------------------
        # 演示功能 3: Tools
        # -------------------------------------------------------------
        print("🔍 [流程 3] 模擬大腦 (Gemma4) 遇到數學題，Client 代為觸發 Tools...")
        tools = await session.list_tools()
        print(f"👉 Server 回報可用的 Tools: {[t.name for t in tools.tools]}")
        
        print("🤖 [Gemma4] 思考中... 『我需要算 500 乘以 42，但我算術不好，我要叫工具幫忙！』")
        tool_result = await session.call_tool(name="calculate_heavy_task", arguments={"number": 500})
        print(f"📥 Tools 執行回傳結果: {tool_result.content[0].text}\n" + "-"*50)

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
        
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)
        
    print("🎉 [系統] MCP 全套模擬順利結束！")

if __name__ == "__main__":
    asyncio.run(main())