import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import base64
from PIL import Image

# 1. Налаштування моделі (спробуємо найбільш універсальне ім'я)
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    # Використовуємо 'gemini-1.5-flash-latest' для кращої сумісності
    model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest")
except Exception:
    st.error("Налаштуйте GEMINI_KEY у Secrets!")
    st.stop()

# 2. Безкоштовна озвучка без ключів (Edge-TTS)
async def _tts(text):
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def speak(text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_tts(text))
        loop.close()
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)
    except:
        pass

# 3. Стан програми
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = model.start_chat(history=[])

st.title("🎓 Твій вчитель (Stable)")

# Відображення чату
for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        if m.get("image"): st.image(m["image"], width=200)
        st.write(m["text"])

st.divider()

# ФОРМА для запобігання циклам
with st.container():
    col_img, col_voice = st.columns(2)
    with col_img:
        img_file = st.camera_input("📸 Фото завдання")
    with col_voice:
        audio_file = st.audio_input("🎤 Голос")
    
    u_text = st.text_input("💬 Текст питання:")
    btn = st.button("Надіслати 🚀")

if btn:
    content = []
    if img_file:
        content.append(Image.open(img_file))
    if u_text:
        content.append(u_text)
    if audio_file:
        content.append({"mime_type": "audio/wav", "data": audio_file.getvalue()})

    if content:
        # Зберігаємо в історію
        st.session_state.chat_history.append({
            "role": "user", 
            "text": u_text or "[Голос/Фото]", 
            "image": Image.open(img_file) if img_file else None
        })
        
        try:
            with st.spinner("Вчитель думає..."):
                resp = st.session_state.gemini_chat.send_message(content)
                st.session_state.chat_history.append({"role": "assistant", "text": resp.text})
                st.rerun()
        except Exception as e:
            st.error(f"Помилка: {e}")

# Озвучення останньої відповіді
if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
    speak(st.session_state.chat_history[-1]["text"])
