import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import base64
from PIL import Image

# 1. Налаштування (використовуємо стабільну модель 1.5 Flash)
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
except Exception:
    st.error("Перевірте GEMINI_KEY у Secrets!")
    st.stop()

# 2. Озвучка
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

# 3. Стан чату
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = model.start_chat(history=[])

st.title("🎓 Репетитор (Версія 2.0)")

# Відображення чату
for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        if m.get("image"): st.image(m["image"], width=200)
        st.write(m["text"])

st.divider()

# ФОРМА — це важливо для зупинки циклів
with st.container():
    c1, c2 = st.columns(2)
    with c1: img_file = st.camera_input("📸 Фото")
    with c2: audio_file = st.audio_input("🎤 Голос")
    
    u_text = st.text_input("💬 Твій текст:")
    btn = st.button("Надіслати вчителю 🚀")

if btn:
    content = []
    if img_file: content.append(Image.open(img_file))
    if u_text: content.append(u_text)
    if audio_file: content.append({"mime_type": "audio/wav", "data": audio_file.getvalue()})

    if content:
        st.session_state.chat_history.append({"role": "user", "text": u_text or "[Запит]", "image": Image.open(img_file) if img_file else None})
        
        try:
            with st.spinner("Думаю..."):
                resp = st.session_state.gemini_chat.send_message(content)
                st.session_state.chat_history.append({"role": "assistant", "text": resp.text})
                st.rerun()
        except Exception as e:
            if "429" in str(e):
                st.error("Google все ще блокує твій IP. Зачекай 1 годину або спробуй інший інтернет (наприклад, мобільний).")
            else:
                st.error(f"Помилка: {e}")

# Озвучка останньої відповіді
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
    speak(st.session_state.chat_history[-1]["text"])
