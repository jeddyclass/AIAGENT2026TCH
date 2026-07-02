# mcp_sse_server.py
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("File-Reader-SSE")

@mcp.tool()
def read_file(filepath: str) -> str:
    """讀取本地檔案內容。"""
    try:
        if not os.path.exists(filepath):
            return f"錯誤：檔案不存在 {filepath}"
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()[:8000]
    except Exception as e:
        return f"錯誤：{str(e)}"

if __name__ == "__main__":
    print("正在啟動 MCP SSE 伺服器，監聽 http://localhost:8000 ...")
    # 啟動為 sse 模式，底層會自動建立一個 Starlette/FastAPI 的 Web 服務
    mcp.run(transport="sse")
