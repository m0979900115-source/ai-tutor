import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import base64

# ── Конфігурація Groq ────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_KEY"])
except Exception:
    st.error("Додайте GROQ_KEY у Secrets!")
    st.stop()

# ── Озвучка (Безкоштовна, без лімітів) ────────────────────────
async def _tts(text):
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio": data += chunk["data"]
    return data

def speak(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_tts(text))
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except: pass

# ── Стан сесії ────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🚀 Швидкий Репетитор (Groq)")

# Відображення чату
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# ── Ввід ──────────────────────────────────────────────────────
user_input = st.chat_input("Запитай що завгодно...")

if user_input:
    # Додаємо повідомлення користувача
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Запит до Groq
    with st.chat_message("assistant"):
        with st.spinner("Думаю миттєво..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Ти професійний репетитор. Відповідай українською мовою, чітко та коротко."},
                        *st.session_state.messages
                    ],
                    model="llama-3.3-70b-versatile", # Найпотужніша модель у Groq
                )
                response = chat_completion.choices[0].message.content
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Озвучка
                speak(response)
            except Exception as e:
                st.error(f"Помилка Groq: {e}")
