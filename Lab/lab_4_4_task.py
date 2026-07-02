import gradio as gr
import time

# ==========================================
# 1. 模擬的 Agent 核心
# ==========================================
class BusAssistantAgent:
    def __init__(self):
        self.routes = {
            "藍23": {"status": "正常", "next_bus": [3, 15, 28]},
            "307": {"status": "密集", "next_bus": [1, 5, 9]},
            "綠1": {"status": "班次較少", "next_bus": [12, 45]}
        }
        self.last_input = ""

    def receive_input(self, message: str):
        self.last_input = message

    def process_stream(self, message: str):
        yield "🤖 [Agent 心跳] 正在分析您的句子結構與關鍵字..."
        time.sleep(0.8)
        
        matched_route = None
        for route in self.routes.keys():
            if route in message:
                matched_route = route
                break
        
        yield f"🔍 [Agent 心跳] 偵測到目標路線：{matched_route if matched_route else '未偵測到特定路線，準備搜尋全部'}"
        time.sleep(0.8)
        
        yield "📡 [Agent 心跳] 正在向交通部 TDX 平台發送 API 請求..."
        time.sleep(1.2)
        
        yield "📊 [Agent 心跳] 資料封包接收成功，正在格式化輸出..."
        time.sleep(0.5)
        
        if matched_route:
            info = self.routes[matched_route]
            minutes = info["next_bus"][0]
            response = f"✨ **查詢成功！**\n\n您查詢的 **{matched_route}** 公車，目前營運狀況為【{info['status']}】。\n下一班車預計 **{minutes} 分鐘** 後抵達您的站點。接下來的班次為：{', '.join(map(str, info['next_bus'][1:]))} 分鐘。"
        else:
            response = "❌ **查詢失敗：**\n\n抱歉，我目前只能辨識 **藍23**、**307**、**綠1** 這三條路線。請試著輸入「藍23還要多久？」來測試我喔！"
            
        yield response

# ==========================================
# 2. 修改後的 Gradio 介面程式碼 (相容您的 Gradio 版本)
# ==========================================
agent = BusAssistantAgent()

def respond(message, chat_history):
    # 使用新版的字典格式（Messages format）
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": ""})
    yield "", chat_history
    
    agent.receive_input(message)
    
    for step_output in agent.process_stream(message):
        # 更新最後一筆 assistant 的內容
        chat_history[-1] = {"role": "assistant", "content": step_output}
        yield "", chat_history

with gr.Blocks() as demo:
    gr.Markdown("# 🚌 模擬公車動態 AI 助理")
    gr.Markdown("提示：可以試著輸入 `藍23還要多久到？` 看看 Agent 的思考過程！")
    
    # 【修正點】移除了 type="messages" 參數，避免 TypeError
    chatbot = gr.Chatbot(label="公車助理")
    msg = gr.Textbox(label="輸入您的問題", placeholder="請輸入公車路線...")
    clear = gr.ClearButton([msg, chatbot], value="清除對話")

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())