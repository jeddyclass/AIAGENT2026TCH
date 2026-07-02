import requests
import json
import time

# ==========================================
# 1. 設定 Open WebUI / Ollama 的 API 資訊
# ==========================================
OPEN_WEBUI_URL = "http://172.10.0.2:8080/api/chat/completions"
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763"
MODEL_NAME = "gemma4_e4b_nothink:latest"

OPEN_WEBUI_URL = "http://192.168.1.153:8080/api/chat/completions"
API_KEY = "sk-cebd4fabff5f4b5d8434795173832ba9"
MODEL_NAME = "gemma4_e4b_nothink:latest"



def call_llm(prompt: str, system_prompt: str = "你是一個有用的 AI 助手。") -> str:
    """呼叫 Open WebUI / Ollama API 的統一函式"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2  # 降低隨機性，讓 ReAct 輸出更穩定
    }
    try:
        response = requests.post(OPEN_WEBUI_URL, headers=headers, json=payload, timeout=240)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"Error: API 回傳錯誤碼 {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: 無法連線到 Open WebUI: {str(e)}"


# ==========================================
# 2. MCP (Model Context Protocol) 模擬端
# ==========================================
class MockMCPServer:
    """模擬一個獨立的 MCP 伺服器，提供 Tools 與 Resources"""
    def __init__(self):
        self.company_db = {
            "專案x": "專案X（Project X）官方代號為『Nebula』，預計於 2026 年第三季啟動 AI 核心模組線。",
            "mcp協定": "MCP 是 Model Context Protocol 的縮寫，是一套開放標準，允許開發者建立安全的雙向連線，讓 LLM 與外部資料與工具互動。"
        }

    def list_tools(self):
        return [{
            "name": "query_company_knowledge",
            "description": "檢索公司內部機密或最新專案知識庫",
            "input_schema": {"type": "object", "properties": {"keyword": {"type": "string"}}}
        }]

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        if tool_name == "query_company_knowledge":
            keyword = arguments.get("keyword", "").lower()
            print(f"🔌 [MCP Server] 執行工具 '{tool_name}'，參數: {keyword}")
            for k, v in self.company_db.items():
                if k in keyword:
                    return f"【MCP Resource 尋獲】: {v}"
            return "【MCP Resource】未找到相關機密文檔。"
        return "錯誤：無此工具"


# ==========================================
# 3. Memory 模組 (共享或獨立)
# ==========================================
class AgentMemory:
    def __init__(self):
        self.history = []
    def add(self, role: str, msg: str):
        self.history.append({"role": role, "content": msg})
    def get_context(self) -> str:
        return "\n".join([f"{h['role']}: {h['content']}" for h in self.history[-6:]])


# ==========================================
# 4. Multi-Agent & A2A & ReAct 核心實作
# ==========================================
class RagAgent:
    """RAG Agent：專門透過 MCP 協定操作資料庫的 Agent"""
    def __init__(self, mcp_server: MockMCPServer):
        self.mcp = mcp_server
        self.system_prompt = """你是一個 RAG 專門代理。
你擁有調用 MCP 工具的能力。請使用 ReAct 格式思考。
若需要查資料，請精確輸出： Action: query_company_knowledge[關鍵字]
得到 Observation 後，請整合並輸出： Final Answer: 最終答案"""

    def receive_message(self, request_text: str) -> str:
        print(f"🤖 [RagAgent] 收到 A2A 請求: '{request_text}'")
        
        # 第一輪 ReAct：思考並決定調用 MCP Tool
        prompt = f"請幫我處理這個請求，必要時使用工具：{request_text}"
        llm_output = call_llm(prompt, self.system_prompt)
        print(f"🧠 [RagAgent 思考]:\n{llm_output}")
        
        if "Action:" in llm_output:
            # 解析 MCP Action
            try:
                tool_part = llm_output.split("Action:")[1].strip()
                tool_name = tool_part.split("[")[0]
                tool_arg = tool_part.split("[")[1].replace("]", "")
                
                # 呼叫 MCP 服務
                observation = self.mcp.call_tool(tool_name, {"keyword": tool_arg})
                print(f"📥 [RagAgent 收到 MCP 回傳]: {observation}")
                
                # 第二輪 ReAct：給出最終答案
                next_prompt = f"{prompt}\n{llm_output}\nObservation: {observation}\n請給出最終 Final Answer。"
                final_output = call_llm(next_prompt, self.system_prompt)
                if "Final Answer:" in final_output:
                    return final_output.split("Final Answer:")[1].strip()
                return final_output
            except Exception as e:
                return f"RagAgent 執行 MCP 失敗: {str(e)}"
        
        if "Final Answer:" in llm_output:
            return llm_output.split("Final Answer:")[1].strip()
        return llm_output


class CoordinatorAgent:
    """主協調 Agent (Router)：負責面對用戶，並透過 A2A 調度其他 Agent"""
    def __init__(self, rag_agent: RagAgent):
        self.rag_agent = rag_agent
        self.memory = AgentMemory()
        self.system_prompt = """你是一個團隊協調代理 (Coordinator)。
你負責分析用戶的問題，並決定是直接回答，還是需要透過 A2A (Agent-to-Agent) 委託給專門的 RagAgent。

你的思考規則 (ReAct)：
1. 如果問題涉及公司內部機密、專案X、最新技術細節、MCP等，你需要找 RagAgent 幫忙。
   格式： Action: Call_Agent[RagAgent, 具體提問內容]
2. 得到對方的 Observation 後，整合並回答用戶。
   格式： Final Answer: 給用戶的最終回答"""

    def handle_user_input(self, user_input: str):
        print(f"\n👥 ====== 收到用戶請求: {user_input} ======")
        context = self.memory.get_context()
        
        prompt = f"【對話歷史】:\n{context}\n\n【當前用戶提問】: {user_input}\n請進行 ReAct 推理。"
        llm_output = call_llm(prompt, self.system_prompt)
        print(f"👑 [Coordinator 思考]:\n{llm_output}")
        
        if "Action: Call_Agent" in llm_output:
            # 解析 A2A 呼叫
            try:
                action_content = llm_output.split("Action: Call_Agent")[1].strip()
                # 提取 RagAgent 與問題
                sub_req = action_content.replace("[RagAgent,", "").replace("]", "").strip()
                
                # ==== A2A 通訊發生處 ====
                rag_response = self.rag_agent.receive_message(sub_req)
                print(f"🤝 [A2A 通訊完成] RagAgent 回報結果。")
                
                # 協調者彙整結果回覆用戶
                next_prompt = f"{prompt}\n{llm_output}\nObservation from RagAgent: {rag_response}\n請輸出最終的 Final Answer 給用戶。"
                final_response = call_llm(next_prompt, self.system_prompt)
                
                if "Final Answer:" in final_response:
                    reply = final_response.split("Final Answer:")[1].strip()
                else:
                    reply = final_response
            except Exception as e:
                reply = f"A2A 調度失敗: {str(e)}"
        elif "Final Answer:" in llm_output:
            reply = llm_output.split("Final Answer:")[1].strip()
        else:
            reply = llm_output
            
        # 紀錄至主要記憶
        self.memory.add("User", user_input)
        self.memory.add("Coordinator", reply)
        print(f"\n✨ [最終對外回應]: {reply}")


# ==========================================
# 5. 啟動模擬測試
# ==========================================
if __name__ == "__main__":
    # 初始化 MCP 伺服器
    mcp_server = MockMCPServer()
    
    # 初始化內部領域 Agent (專精 RAG + MCP)
    rag_agent = RagAgent(mcp_server)
    
    # 初始化面對用戶的主 Agent (專精 A2A 路由)
    coordinator = CoordinatorAgent(rag_agent)
    
    # 測試任務一：需要觸發 A2A 與 MCP 鏈條的複雜任務
    coordinator.handle_user_input("幫我查一下專案X的代號是什麼？順便解釋一下什麼是MCP協定")
    
    print("\n" + "="*60 + "\n")
    
    # 測試任務二：依賴主要記憶，由主 Agent 直接處理的閒聊
    coordinator.handle_user_input("太棒了，謝謝你的詳細解答！")