import asyncio
import anyio
import math
import os
from mcp.server import Server
from mcp.client.session import ClientSession
from mcp.types import Tool, Resource, Prompt

# 0. 建立地端實體測試檔案
TEST_FILENAME = "mcp_fast_test.txt"
TEST_FILE_PATH = os.path.abspath(TEST_FILENAME)
with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
    f.write("【地端數據】Gemma4 透過清爽版 MCP 成功讀取此實體檔案！")

# =====================================================================
# 1. HIGH-LEVEL SERVER 端設計 (不導入繁瑣型態，活用 dict 自動轉換)
# =====================================================================
server_app = Server("fast-local-server")

# --- Resources (唯讀資源) ---
@server_app.list_resources()
async def list_resources():
    return [Resource(uri=f"file://{TEST_FILE_PATH}", name="輕量日誌", mimeType="text/plain")]

@server_app.read_resource()
async def read_resource(uri):
    if TEST_FILENAME in str(uri):
        with open(TEST_FILE_PATH, "r", encoding="utf-8") as f:
            # 💡 偷懶妙招 1：直接回傳純字串！SDK 底層會自動幫你包裝成標準資源物件
            return f.read()
    raise ValueError("找不到資源")

# --- Tools (動態工具) ---
@server_app.list_tools()
async def list_tools():
    return [
        Tool(
            name="fast_calc",
            description="地端快速計算",
            inputSchema={
                "type": "object",
                "properties": {"number": {"type": "integer"}},
                "required": ["number"]
            }
        )
    ]

@server_app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "fast_calc":
        num = arguments.get("number", 0)
        # 💡 偷懶妙招 2：直接用 dict 代替 TextContent 物件，SDK 會自動做 Pydantic 轉換！
        return [{"type": "text", "text": f"【計算完成】{num} x 42 = {num * 42}"}]

# --- Prompts (提示詞範本) ---
@server_app.list_prompts()
async def list_prompts():
    return [Prompt(name="fast_prompt", description="快速模板")]

@server_app.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "fast_prompt":
        # 💡 偷懶妙招 3：直接回傳符合結構的 dict 列表，優雅又省空間！
        return {
            "description": "分析師模板",
            "messages": [{"role": "user", "content": {"type": "text", "text": "請用專家模式思考。"}}]
        }


# =====================================================================
# 2. CLIENT 端全自動運行模擬
# =====================================================================
async def main():
    print("🚀 [系統] 啟動清爽版 MCP 全套模擬...")

    # anyio 記憶體水管
    c2s_send, c2s_receive = anyio.create_memory_object_stream(math.inf)
    s2c_send, s2c_receive = anyio.create_memory_object_stream(math.inf)

    # 背景啟動 Server
    server_task = asyncio.create_task(server_app.run(
        c2s_receive, s2c_send, server_app.create_initialization_options()
    ))

    # Client 連線與測試
    async with ClientSession(s2c_receive, c2s_send) as session:
        await session.initialize()
        print("✅ [握手成功] Client 與 Server 已在記憶體對齊通道！\n" + "-"*50)

        # 1. 測試 Prompts
        print("🔍 [演示 1] 索取 Prompt 模板...")
        target_prompt = await session.get_prompt(name="fast_prompt", arguments={})
        print(f"📥 收到模板: '{target_prompt.messages[0].content.text}'\n" + "-"*50)

        # 2. 測試 Resources
        print("🔍 [演示 2] 讀取地端檔案資源...")
        log_res = await session.read_resource(uri=f"file://{TEST_FILE_PATH}")
        print(f"📥 讀到檔案內容: {log_res.contents[0].text}\n" + "-"*50)

        # 3. 測試 Tools
        print("🔍 [演示 3] 觸發地端 Python 工具...")
        tool_result = await session.call_tool(name="fast_calc", arguments={"number": 100})
        print(f"📥 工具回傳: {tool_result.content[0].text}\n" + "-"*50)

    # 清理
    server_task.cancel()
    if os.path.exists(TEST_FILE_PATH):
        os.remove(TEST_FILE_PATH)
    print("🎉 [系統] 輕量化全套模擬圓滿結束！")

if __name__ == "__main__":
    asyncio.run(main())