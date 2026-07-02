import time
import random
import json
# ===============================================================
# 🔥 核心配置與模擬函數 (用於統一環境)
# ===============================================================
# OLLAMA_BASE_URL = "http://localhost:8080/"
# API_KEY = "sk-1540f219fcb246b9bb55c7951491c01b" 
# MODEL = "gemma4_e4b_ctx_128k_nothink:latest"

OLLAMA_API = {
    "api_key": "sk-f60ffbf03ede457987a23650b8b11763",
    "ip": "http://172.10.0.2:8080",
    "model": "gemma4_e4b_ctx_2048:latest",
    "endpoint": "/api/chat/completions"
}
def call_llm_tool(prompt, context):
    """
    模擬 LLM 決定調用 A2A 協議的 Tool Calling 過程。
    根據不同的情境，返回不同的 A2A 調用指令。
    """
    print("\n" + "="*20)
    print("--- 🧠 [LLM 決策點] 模擬 LLM 根據 Prompt 決定調用 A2A 協議 ---")

    if "測試一下 Agent 2" in prompt:
        # 情境一：簡單問候
        return {
            "tool_name": "A2A_Protocol",
            "method": "message/send",
            "parameters": {
                "contextId": "hello_test_001",
                "message": "您好，我是 Agent 1。能否請您確認一下您的身份？",
                "expectedResponseType": "Confirmation Message"
            }
        }

    elif "爬取 RTX 5090" in prompt:
        # 情境二：發起長時間任務
        return {
            "tool_name": "A2A_Protocol",
            "method": "message/send",
            "parameters": {
                "contextId": "T101_RTX_PRICE",
                "message": "請幫我爬取 RTX 5090 最近兩週的市場價格。",
                "expectedResponseType": "Task ID"
            }
        }
    elif "通知 email@example.com" in prompt:
        # 情境三：啟動任務並設置 Webhook
        return {
            "tool_name": "A2A_Protocol",
            "method": "message/send",
            "parameters": {
                "contextId": "C123_NVIDIA_PRICE",
                "message": "請幫我爬取 RTX 5090 最近兩週的市場價格，並寄信給 email@example.com。",
                "expectedResponseType": "Task ID + Notification Setup"
            }
        }
    return None
# ===============================================================
# 🗺️ 流程情境一：Message 交換 (Hello)
# ===============================================================
def simulate_agent_interaction_1():
    print("\n" + "="*80)
    print("======== 🌐 流程演示 1：基礎 Message 交換 (問候/確認) ========")
    print("="*80)
    # 1. 模擬 User -> A1
    user_prompt = "請幫我測試一下 Agent 2 是否能正常回應，用一個簡單的問候語開始。"
    print(f"\n[使用者輸入]：{user_prompt}")

    # 2. 模擬 A1 決定調用 Tool
    tool_call = call_llm_tool(user_prompt, None)

    if tool_call and tool_call['method'] == "message/send":
        params = tool_call['parameters']
        print(f"\n[Agent 1 執行] 準備調用 A2A: message/send...")
        print(f"[A1 -> A2] 發送 A2A 請求：{json.dumps(params, ensure_ascii=False)}")

        # 3. 模擬 A2 收到請求並回覆
        print("\n[Agent 2 內部處理] 接收到請求，根據 AgentCard 回覆一個問候語...")
        a2_response = {
            "status": "SUCCESS",
            "contextId": params["contextId"],
            "response_type": "Message",
            "data": {
                "message": "您好！我是 Agent 2，身份確認成功。我的專長是跨國物流協作。",
                "source": "AgentCard 查閱"
            }
        }

        # 4. 模擬 A1 收到並展示給使用者
        print("\n[Agent 1 接收] 成功接收到 Agent 2 的回應。")
        print("="*80)
        print(f"✅ 最終展示給使用者: {a2_response['data']['message']}")
        print("="*80)
# ===============================================================
# 🌐 流程情境二：Task & Polling (任務與輪詢)
# ===============================================================
def simulate_agent_interaction_2():
    print("\n\n" + "="*80)
    print("======== 🌐 流程演示 2：任務管理與輪詢 (Task & Polling) ========")
    print("="*80)
    TASK_ID = "T101_RTX_PRICE"

    # 1. 模擬 User -> A1
    user_prompt = "請幫我爬取 RTX 5090 最近兩週的市場價格。"
    print(f"\n[使用者輸入]：{user_prompt}")

    # 2. 模擬 A1 啟動任務 (A1 -> A2)
    tool_call = call_llm_tool(user_prompt, None)

    if tool_call and tool_call['method'] == "message/send":
        params = tool_call['parameters']
        print(f"\n[Agent 1 執行] 準備調用 A2A: message/send (Task ID: {TASK_ID})")
        print(f"[A1 -> A2] 發送 A2A 請求：{json.dumps(params, ensure_ascii=False)}")

        # 3. 模擬 A2 返回 Task ID (狀態: SUBMITTED)
        print("\n[Agent 2 內部處理] 任務已創建，初始狀態設置為 WORKING...")

        # 4. 模擬輪詢循環 (A1 核心邏輯)
        print("\n--- 🚀 開始定時輪詢進程 (Polling Loop) ---")
        for attempt in range(1, 5):
            print(f"\n[A1 邏輯] 輪詢中... 呼叫 tasks/get?id={TASK_ID} (第 {attempt} 次)")

            # 模擬 A2 的回應 (狀態模擬)
            if attempt < 4:
                # 模擬正在處理中 (Working State)
                progress = random.randint(10, 40)
                a2_response = {
                    "task_id": TASK_ID,
                    "status": "TASK_STATE_WORKING",
                    "message": f"數據爬取進行中，已完成 {progress}%。",
                    "estimated_completion_time": "2 分鐘"
                }
                print(f"[A2 回應] 🟢 狀態: {a2_response['status']} - {a2_response['message']}")
                time.sleep(0.5)
            else:
                # 模擬完成狀態 (Completed State)
                a2_response = {
                    "task_id": TASK_ID,
                    "status": "TASK_STATE_COMPLETED",
                    "artifacts": [
                        {"name": "PriceData", "content": "這是一個包含 14 天數據的結構化 JSON..."}
                    ],
                    "final_message": "所有數據已成功收集！請查閱 Artifacts。"
                }
                print(f"[A2 回應] 🔵 狀態: {a2_response['status']}")
                break
        # 5. A1 處理完成結果
        print("\n" + "="*80)
        print("✅ 流程結束：Agent 1 成功接收所有 Artifacts，並向使用者匯報。")
        print("="*80)
# ===============================================================
# 📞 流程情境三：ContextID + Push Notification (通知機制)
# ===============================================================
def handle_webhook_callback(payload):
    """模擬 Agent 1 的 Webhook 接收端點"""
    print("\n🚨🚨🚨 [Webhook 接收器] ⚡️ 收到異步通知！(來自 Agent 2 的推送) 🚨🚨🚨")

    # 1. 解析通知內容
    task_id = payload.get("taskId")
    status = payload.get("status")
    report = payload.get("data", {})

    print(f"✅ 識別：Task ID {task_id} 已狀態更新為: {status}")

    if status == "TASK_STATE_COMPLETED":
        final_message = report.get("final_summary", "數據已處理完成。")

        # 2. 組合成最終報告並展示給使用者
        print("\n" + "="*80)
        print("✅ 流程結束：Agent 1 成功接收 Webhook 推播，最終報告給使用者！")
        print("=======================================================================================")
        print(f"【任務報告摘要】：{final_message}")
        print("========================================================================================")
    else:
        print(f"🟡 收到狀態更新，但尚未完成。當前狀態：{status}")


def simulate_agent_interaction_3():
    print("\n\n" + "="*80)
    print("======== 📞 流程演示 3：上下文與異步通知 (ContextID & Push) ========")
    print("="*80)
    CONTEXT_ID = "C123_NVIDIA_PRICE"

    # 1. 模擬 User -> A1
    user_prompt = "請幫我爬取 RTX 5090 最近兩週的市場價格，並寄信給 email@example.com。"
    print(f"\n[使用者輸入]：{user_prompt}")

    # 2. 模擬 A1 啟動任務並設置通知 (A1 -> A2)
    tool_call = call_llm_tool(user_prompt, None)

    if tool_call and tool_call['method'] == "message/send":
        params = tool_call['parameters']
        print(f"\n[Agent 1 執行] 步驟一：發送初始 A2A 請求，攜帶上下文ID：{json.dumps(params, ensure_ascii=False)}")

        # 3. 模擬 A1 執行後續的通知配置 (Task State Setup)
        print("\n[A1 -> A2] 步驟二：調用 tasks/pushNotificationConfig/set...")
        print("[A2 內部] 任務已設置：當任務狀態改變時，系統已綁定 Context ID，並將自動 Webhook 推送至 A1 監聽地址。")

        # 4. 模擬 Background Task 執行 (等待時間)
        print("\n... (模擬後台爬蟲任務正在後台運行，等待通知觸發) ...")
        time.sleep(1)

        # 5. 模擬 Webhook 觸發 (A2 自動推送 -> A1)
        mock_webhook_payload = {
            "taskId": "T_FINAL_999",
            "contextId": CONTEXT_ID,
            "status": "TASK_STATE_COMPLETED",
            "data": {
                "final_summary": "RTX 5090 最近兩週價格數據已整理完成。平均價格為 $1200，波動小。詳細數據已寄送到您指定的電子郵件。",
                "received_email": "email@example.com"
            }
        }

        # 6. A1 接收並處理 Webhook (核心！)
        handle_webhook_callback(mock_webhook_payload)
# ============================================================================
# 🌟 主執行入口 (The Main Runner)
# ============================================================================
def run_all_scenarios():
    print("\n\n=================================================================")
    print("========== ✨ A2A 協議全流程模擬演示啟動 ✨ ==========")
    print("=================================================================")

    # 執行情境一：簡單問候
    simulate_agent_interaction_1()

    time.sleep(2)

    # 執行情境二：任務與輪詢
    simulate_agent_interaction_2()
    time.sleep(2)

    # 執行情境三：上下文與異步通知
    simulate_agent_interaction_3()

    print("\n\n=================================================================")
    print("✅ 所有 A2A 流程模擬演示全部完成！")
    print("=================================================================")
# 運行主程序
if __name__ == "__main__":
    run_all_scenarios()
