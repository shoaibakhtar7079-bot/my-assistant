import json
import os
import requests
import streamlit as st

PROFILE_FILE = "profile.txt"
MEMORY_FILE = "memory.json"
ENV_FILE = ".env"
MODEL = "gemini-3.8-flash"
def load_key():
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key and os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key

def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def ask_gemini(key, system_message, memory):
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
    contents = []
    for m in memory[-40:]:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    body = {
        "system_instruction": {"parts": [{"text": system_message}]},
        "contents": contents,
    }
    r = requests.post(url, headers={"x-goog-api-key": key, "Content-Type": "application/json"}, json=body, timeout=120)
    if r.status_code != 200:
        return "कुछ गड़बड़ हुई: " + r.text[:300]
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "जवाब नहीं मिला: " + json.dumps(data)[:300]

st.set_page_config(page_title="मेरा असिस्टेंट")
st.title("मेरा असिस्टेंट")

key = load_key()
if not key:
    st.error("चाबी नहीं मिली। .env फाइल में GEMINI_API_KEY जाँचिए।")
    st.stop()

profile = load_profile()
system_message = (
    "तुम शोएब अख्तर की पर्सनल असिस्टेंट हो। हमेशा हिंदी में, छोटे और आसान शब्दों में जवाब दो। "
    "शोएब के बारे में जानकारी: " + profile
)

if "memory" not in st.session_state:
    st.session_state.memory = load_memory()

for m in st.session_state.memory:
    with st.chat_message(m["role"]):
        st.write(m["content"])

user_input = st.chat_input("यहाँ लिखिए...")

if user_input:
    st.session_state.memory.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    with st.chat_message("assistant"):
        with st.spinner("सोच रही हूँ..."):
            answer = ask_gemini(key, system_message, st.session_state.memory)
            st.write(answer)
    st.session_state.memory.append({"role": "assistant", "content": answer})
    save_memory(st.session_state.memory)