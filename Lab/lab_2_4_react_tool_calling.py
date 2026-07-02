import requests
import json
import re

# ================== 配置 ==================
API_BASE = "http://172.10.0.2:8080"   # 你的 OpenWebUI 端口
API_KEY = "sk-f60ffbf03ede457987a23650b8b11763" 
MODEL = "gemma4_e4b_ctx_2048:latest"


HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ================== 工具定義 ==================
def weather_tool(city: str) -> str:
    """模擬天氣工具（實際上你可以接真實 API）"""
    # 這裡示範固定回傳，實際可替換成真實天氣 API
    return "30°C, cloudy, with afternoon thunderstorms."

# ================== 呼叫 LLM ==================
def call_llm(prompt: str, temperature=0.7) -> str:
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1024
    }
    
    response = requests.post(
        f"{API_BASE}/api/chat/completions", 
        json=payload, 
        headers=HEADERS
    )
    
    if response.status_code != 200:
        raise Exception(f"API Error: {response.text}")
    
    return response.json()["choices"][0]["message"]["content"]

# ================== ReAct 主循環 ==================
def react_agent_old(query: str, max_steps=10):
    print(f"👤 User: {query}\n")
    
    history = f"Question: {query}\n"
    
    for step in range(1, max_steps + 1):
        print(f"--- Step {step} ---")
        
        # 1. Thought + Action
        prompt = f"""{history}

You are a helpful assistant using ReAct (Reasoning + Acting) method.
Think step by step and respond in the following format:

Thought: [your reasoning]
Action: [tool name] [input]   # e.g. Weather Taipei

Answer only with Thought and Action (if needed)."""

        response = call_llm(prompt)
        print(f"🤖 LLM:\n{response}\n")
        
        history += f"\n{response}"
        
        # 2. 解析 Action
        action_match = re.search(r"Action:\s*(.+)", response, re.IGNORECASE)
        
        if not action_match:
            # 可能直接給最終答案
            final_match = re.search(r"Final Answer:?\s*(.+)", response, re.IGNORECASE | re.DOTALL)
            if final_match:
                print(f"✅ Final Answer: {final_match.group(1).strip()}")
                return
            continue
        
        action_text = action_match.group(1).strip()
        
        # 3. 執行工具（目前只支援 weather）
        if "weather" in action_text.lower() or "台北" in action_text or "Taipei" in action_text:
            city = "Taipei"
            observation = weather_tool(city)
            obs_text = f"Observation: {observation}"
            print(f"🔧 Tool: {obs_text}\n")
            history += f"\n{obs_text}"
        else:
            print("⚠️ Unknown tool, continuing...\n")
    
    print("⚠️ Reached max steps")

def react_agent(query: str, max_steps=15):
    print(f"👤 User: {query}\n")
    
    history = f"Question: {query}\n"
    step = 0
    
    while True:
        step += 1
        if step > max_steps:
            print("⚠️ Reached maximum steps limit")
            break
            
        print(f"--- Step {step} ---")
        
        # 1. 讓 LLM 思考下一步
        prompt = f"""{history}

You are using ReAct (Reasoning + Acting).
Respond in exactly this format:

Thought: [your reasoning here]
Action: [ToolName] [input]   # or "None" if no tool needed

If you have enough information, output:
Final Answer: [your final answer]"""

        response = call_llm(prompt, temperature=0.3)
        print(f"🤖 LLM:\n{response}\n")
        
        history += f"\n{response}"
        
        # 2. 檢查是否結束
        if "Final Answer:" in response or "final answer:" in response.lower():
            final_answer = re.search(r"Final Answer:?\s*(.+)", response, re.IGNORECASE | re.DOTALL)
            if final_answer:
                print(f"✅ Final Answer: {final_answer.group(1).strip()}")
                return
        
        # 3. 解析並執行 Action
        action_match = re.search(r"Action:\s*(.+)", response, re.IGNORECASE)
        if not action_match or "none" in action_match.group(1).lower():
            print("🤔 No action needed, continuing...\n")
            continue
            
        action_text = action_match.group(1).strip()
        
        # 執行工具
        if "weather" in action_text.lower() or "taipei" in action_text.lower():
            observation = weather_tool("Taipei")
            obs_text = f"Observation: {observation}"
            print(f"🔧 Tool Result: {obs_text}\n")
            history += f"\n{obs_text}"
        else:
            print(f"⚠️ Unknown tool: {action_text}\n")
    
    print("🏁 ReAct finished.")
    
# ================== 執行 ==================
if __name__ == "__main__":
    query = "Is it a good day for running in Taipei today?"
    react_agent(query)