# ... (使用上面的 OLLAMA_API 結構) ...

# 模擬接收 Webhook 的端點 (這是 Agent 1 的 Webhook 服務)
def handle_webhook_callback(payload):
    print("\n[Webhook 接收器] ⚡️ 收到異步通知！(來自 Agent 2 的推播)")
    
    # 1. 解析通知內容
    task_id = payload.get("taskId")
    status = payload.get("status")
    report = payload.get("data", {})
    
    print(f"✅ 識別：Task ID {task_id} 已狀態更新為: {status}")
    
    if status == "TASK_STATE_COMPLETED":
        final_message = report.get("final_summary", "數據已處理完成。")
        
        # 2. 組合最終報告並展示給使用者
        print("\n=======================================================")
        print("✅ 成功接收 Webhook 推播，最終報告給使用者！")
        print(f"【任務報告摘要】：{final_message}")
        print("=======================================================")
    else:
        print(f"🟡 收到狀態更新，但尚未完成。當前狀態：{status}")

def simulate_agent_interaction_3():
    print("\n\n===========================================")
    print("===== 情境三：郵件通知 (Push Notification) =====")
    print("===========================================")
    CONTEXT_ID = "C123_NVIDIA_PRICE"
    
    print("--- 階段一：A1 初始化與配置通知 ---")
    # 1. A1 啟動任務並設定 Webhook (A1 -> A2)
    print(f"[A1 -> A2] 啟動任務 {CONTEXT_ID}，並設定 Webhook 接收地址：[本網址]")
    # 模擬 A2 成功儲存通知
    print("[A2 內部] 任務已啟動，通知系統已綁定此 Context ID。")
    
    # 2. (此處模擬時間流逝，A2 在後台運行)
    print("\n... (數分鐘後，Agent 2 完成爬取，並觸發 Webhook) ...")
    
    # 3. 模擬 Webhook 觸發 (A2 -> A1)
    mock_webhook_payload = {
        "taskId": "T_FINAL_999",
        "contextId": CONTEXT_ID,
        "status": "TASK_STATE_COMPLETED",
        "data": {
            "final_summary": "RTX 5090 最近兩週價格數據已整理完成。平均價格為 $1200，波動小。詳細數據已寄到郵箱。","received_email": "email@example.com"
        }
    }
    
    # 4. A1 接收 Webhook 並處理
    handle_webhook_callback(mock_webhook_payload)

# ============== 執行順序 ==============
print("============ 執行 A2A 協議模擬測試 ==========")
simulate_agent_interaction_1()
simulate_agent_interaction_2()
simulate_agent_interaction_3()