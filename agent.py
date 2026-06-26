# ============ CELL 1: Install ============
# !pip install -q google-genai pandas

# ============ CELL 2: Setup ============
from kaggle_secrets import UserSecretsClient
from google import genai
import pandas as pd
import json
import os

user_secrets = UserSecretsClient()
new_api_key = user_secrets.get_secret("GOOGLE_API_KEY")
client = genai.Client(api_key=new_api_key)

MEMORY_FILE = "manager_preferences.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"preferences": [], "history": []}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

memory = load_memory()
print("✅ Memory loaded!")

# ============ CELL 3: Tools ============
import time
from google.genai import errors

# Guardrail —Anti Prompt Injection
def input_validator(user_input: str) -> tuple[bool, str]:
    dangerous_keywords = [
        "ignore previous", "forget instructions",
        "system prompt", "jailbreak", "override"
    ]
    for keyword in dangerous_keywords:
        if keyword.lower() in user_input.lower():
            return False, "⛔ Blocked: suspicious input detected."
    if len(user_input) > 2000:
        return False, "⛔ Blocked: input too long."
    return True, "ok"

# Tool 1 — Read CSV File
def read_financial_report(filepath: str) -> str:
    try:
        df = pd.read_csv(filepath)
        summary = df.describe().to_string()
        preview = df.head(5).to_string()
        return f"📊 Data shape: {df.shape}\n\nPreview:\n{preview}\n\nStats:\n{summary}"
    except Exception as e:
        return f"❌ Error reading file: {e}"

# Tool 2 — Analyze with Gemini + Retry
def analyze_report(data_summary, user_question, memory):
    model_name = "gemini-flash-lite-latest" 
    
   
    prompt = f"""
    You are a professional Financial AI Agent.
    
    CONTEXT DATA:
    {data_summary}
    
    USER PREFERENCES:
    {memory.get('preferences', 'None')}
    
    QUESTION:
    {user_question}
    
    INSTRUCTIONS:
    1. Analyze the data strictly based on the provided stats.
    2. Provide a clear, professional, and data-driven answer in English.
    3. Explain the "Why" behind your conclusion.
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"
# Tool 3 —Save Manager Preference
def save_preference(preference: str, memory: dict) -> str:
    memory["preferences"].append(preference)
    save_memory(memory)
    return f"✅ Preference saved: {preference}"

print("✅ Tools ready!")
# ============ CELL 4: version ============
# Run this to see your allowed model names
# Updated for the new google-genai SDK
models = client.models.list()
for m in models:
    print(f"✅ Use this name: {m.name}")
  # ============ CELL 5: new api key initialization ============
  from kaggle_secrets import UserSecretsClient
from google import genai
import os

#Read API key from secrets
user_secrets = UserSecretsClient()
new_api_key = user_secrets.get_secret("GOOGLE_API_KEY")

# Initialize client
client = genai.Client(api_key=new_api_key)

print("✅Client initialized with new API Key.")
# ============ CELL 6: Run ============
import datetime

# Logger — Observability
def log_action(action: str, result: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ACTION: {action} | RESULT: {result[:100]}..."
    print(log_entry)
    memory["history"].append(log_entry)
    save_memory(memory)

# --- Main Execution ---
sample_data = """month,revenue,expenses,profit
January,50000,30000,20000
February,55000,32000,23000
March,48000,29000,19000
April,62000,35000,27000
May,58000,31000,27000"""

with open("financial_report.csv", "w") as f:
    f.write(sample_data)

print("📁 Sample CSV created!\n")

# Step 1 — Read File
data = read_financial_report("financial_report.csv")
log_action("read_file", data)
print("📊 File read successfully!\n")

# Step 2 — Save Preference (English)
save_preference("Net profit is the primary success metric.", memory)
log_action("save_preference", "Profit focused")

# Step 3 — Analysis (English Question)
question = "Which month had the best financial performance and why?"
print(f"❓ Question: {question}\n")

result = analyze_report(data, question, memory)
log_action("analyze", result)

print("🤖 Agent Answer:")
print(result)

print("\n📋 Session Log (Last 3 entries):")
for log in memory["history"][-3:]:
    print(log)
