import time
import random

# ... (使用上面的 OLLAMA_API 結構) ...

def simulate_agent_interaction_2():
    print("\n\n===========================================")
    print("===== 情境二：爬取價格與輪詢 (Task & Polling) =====")
    print("===========================================")
    TASK_ID = "T101_RTX_PRICE"
    
    # 1. 模擬 A1 啟動任務 (A1 -> A2)
    print(f"[A1 -> A2] 啟動任務: message/send (Task ID: {TASK_ID})")
    print("[A2 內部] 任務已接受，狀態設定為 WORKING...")
    
    # 2. 模擬輪詢循環 (A1 核心邏輯)
    print("\n--- 🚀 開始定時輪詢進度 (Polling) ---")
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
                "estimated_completion_time": "2 minutes"
            }
            print(f"[A2 回應] 🟢 狀態: {a2_response['status']} - {a2_response['message']}")
            time.sleep(1) # 等待模擬延遲
        else:
            # 模擬完成狀態 (Completed State)
            a2_response = {
                "task_id": TASK_ID,
                "status": "TASK_STATE_COMPLETED",
                "artifacts": [
                    {"name": "PriceData", "content": "這是爬取到的 14 天數據 JSON 結構..."}
                ],
                "final_message": "所有數據已成功收集！請查閱 Artifacts。"
            }
            print(f"[A2 回應] 🔵 狀態: {a2_response['status']}")
            break

    # 3. A1 處理完成結果
    print("\n=======================================================")
    print("✅ 流程結束：Agent 1 成功接收所有 Artifacts，並將報告給使用者。")
    print("=======================================================")


# simulate_agent_interaction_2()