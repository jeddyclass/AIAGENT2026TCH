
import os
import re
import json
from openai import OpenAI

# ==========================================
# 1. 初始化 Ollama + Open WebUI 用戶端
# ==========================================
# Open WebUI 的 API 介面與 OpenAI 完全相容，因此直接使用 openai SDK
OPENWEBUI_API_KEY = "sk-f60ffbf03ede457987a23650b8b11763" 
OPENWEBUI_BASE_URL = "http://172.10.0.2:8080"  # 請依據你的 Open WebUI 實際網址修改

client = OpenAI(
    api_key=OPENWEBUI_API_KEY,
    base_url=OPENWEBUI_BASE_URL
)

# 定義你想使用的 Ollama 模型代號（需確保在 Open WebUI/Ollama 中已下載）
MODEL_LLAMA_31 = "llama3.1:3b"
#MODEL_LLAMA_32 = "llama3.2:3b"
MODEL_LLAMA_32 = "llama3.2:3b"

# 全局對話歷史紀錄
chat_history = []


def model_chat(user_input: str, model_name: str, sys_prompt: str, temperature: float = 0.7, max_tokens: int = 2048):
    """
    通用對話函式，負責將訊息發送給 Open WebUI 後端
    """
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_input}
    ]
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    return response.choices[0].message.content


# ==========================================
# 2. 測試：錯誤的 Prompt Template 範例
# ==========================================
print("--- 測試 1: 使用錯誤的 Prompt Template (模型不會主動呼叫內建工具) ---")

WRONG_SYSTEM_PROMPT = """
Cutting Knowledge Date: December 2023
Today Date: 20 August 2024

You are a helpful assistant
"""

user_input_news = "When is the next Elden Ring game coming out?"
response_news = model_chat(user_input_news, MODEL_LLAMA_31, WRONG_SYSTEM_PROMPT)
print("Assistant (新聞詢問):", response_news)
print("-" * 50)

user_input_math = "What is the square root of 23131231?"
response_math = model_chat(user_input_math, MODEL_LLAMA_31, WRONG_SYSTEM_PROMPT)
print("Assistant (數學詢問):", response_math)
print("-" * 50)


# ==========================================
# 3. 測試：使用 Llama 3.1 官方 Prompt Template 觸發 Tool Calling
# ==========================================
print("\n--- 測試 2: 使用 Llama 3.1 正確的內建工具 Prompt Template ---")

CORRECT_SYSTEM_PROMPT = """
Environment: iPython
Tools: brave_search, wolfram_alpha
Cutting Knowledge Date: December 2023
Today Date: 15 September 2024
"""

# 模型此時應該要輸出含有 <|python_tag|> 的工具呼叫指令
tool_output = model_chat(user_input_math, MODEL_LLAMA_31, CORRECT_SYSTEM_PROMPT)
print("Assistant 原始輸出:\n", tool_output)
print("-" * 50)

# 使用 Regex 解析模型輸出的工具指令
print("--- 解析 Llama 3.1 的工具呼叫參數 ---")
try:
    fn_name = re.search(r'<\|python_tag\|>(\w+)\.', tool_output).group(1)
    fn_call_method = re.search(r'\.(\w+)\(', tool_output).group(1)
    fn_call_args = re.search(r'=\s*([^)]+)', tool_output).group(1)

    print(f"提取成功 -> 功能名稱: {fn_name}")
    print(f"提取成功 -> 呼叫方法: {fn_call_method}")
    print(f"提取成功 -> 參數內容: {fn_call_args}")
except AttributeError:
    print("模型未按照預期格式輸出 <|python_tag|>，請確認本地 Llama 3.1 模型的 Prompt 模板支援度。")
print("-" * 50)


# ==========================================
# 4. 測試：Llama 3.2 自訂工具 JSON 格式化 
# ==========================================
print("\n--- 測試 3: Llama 3.2 自訂工具定義與解析實戰 ---")

# 模擬資料庫
def get_user_info(user_id: int, special: str = "none") -> dict:
    user_database = {
        7890: {"name": "Emma Davis", "email": "emma@example.com", "age": 31},
        1234: {"name": "Liam Wilson", "email": "liam@example.com", "age": 28},
        2345: {"name": "Olivia Chen", "email": "olivia@example.com", "age": 35},
        3456: {"name": "Noah Taylor", "email": "noah@example.com", "age": 42}
    }
    
    if user_id in user_database:
        user_data = user_database[user_id].copy()
        if special != "none":
            user_data["special_info"] = f"Special request: {special}"
        return user_data
    else:
        return {"error": "User not found"}


function_definitions = """[
    {
        "name": "get_user_info",
        "description": "Retrieve details for a specific user by their unique identifier.",
        "parameters": {
            "type": "dict",
            "required": ["user_id"],
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The unique identifier of the user."
                },
                "special": {
                    "type": "string",
                    "description": "Any special information or parameters.",
                    "default": "none"
                }
            }
        }
    }
]"""

LLAMA32_SYSTEM_PROMPT = """You are an expert in composing functions. You are given a question and a set of possible functions. 
Based on the question, you will need to make one or more function/tool calls to achieve the purpose. 
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]
You SHOULD NOT include any other text in the response.

Here is a list of functions in JSON format that you can invoke.\n\n{functions}\n""".format(functions=function_definitions)


def process_llama32_response(response_text):
    """
    自訂的工具執行器：利用 Regex 捕捉 [func_name(args)] 格式並動態執行 Python 函式
    """
    function_call_pattern = r'\[(.*?)\((.*?)\)\]'
    function_calls = re.findall(function_call_pattern, response_text)
    
    if function_calls:
        processed_response = []
        for func_name, args_str in function_calls:
            args_dict = {}
            # 解析以逗號分隔的參數對，例如 user_id=7890, special='black'
            for arg in args_str.split(','):
                if '=' in arg:
                    key, value = arg.split('=')
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    if value.isdigit():
                        value = int(value)
                    args_dict[key] = value
            
            # 對應執行本地的 get_user_info
            if func_name == 'get_user_info':
                result = get_user_info(**args_dict)
                processed_response.append(f"Function call result: {json.dumps(result, indent=2)}")
            else:
                processed_response.append(f"Unknown function: {func_name}")
        return "\n".join(processed_response)
    else:
        return response_text


def model_chat_llama32_workflow(user_input: str):
    """
    完整的 Llama 3.2 工具調用工作流
    """
    global chat_history
    if not chat_history:
        chat_history = [{"role": "system", "content": LLAMA32_SYSTEM_PROMPT}]
    
    chat_history.append({"role": "user", "content": user_input})
    
    # 呼叫模型
    response = client.chat.completions.create(
        model=MODEL_LLAMA_32,
        messages=chat_history,
        temperature=0.7
    )
    
    assistant_response = response.choices[0].message.content
    print(f"Model 原始工具決策輸出: {assistant_response}")
    
    # 解析並執行工具
    final_output = process_llama32_response(assistant_response)
    
    chat_history.append({"role": "assistant", "content": assistant_response})
    return final_output


# 執行 Llama 3.2 測試
user_input_32 = "Can you retrieve the details for the user with the ID 7890, who has black as their special request?"
final_result = model_chat_llama32_workflow(user_input_32)

print("\n系統最終執行與解析結果:")
print(final_result)
print("#fin")

