import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import base64
from PIL import Image

# 1. Спрощена конфігурація
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    # Використовуємо коротку назву моделі, яку система знає за замовчуванням
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Помилка конфігурації: {e}")
    st.stop()

# 2. Озвучка (Edge-TTS) - стабільна та безкоштовна
async def _tts(text):
    try:
        communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except:
        return None

def speak(text):
    audio_bytes = asyncio.run(_tts(text))
    if audio_bytes:
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(f'<audio autoplay src="data:audio/mp3;base64,{b64}"></audio>', unsafe_allow_html=True)

# 3. Історія чату
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

st.title("🎓 Твій репетитор")

# Відображення повідомлень
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], width=250)
        st.write(msg["text"])

st.divider()

# Ввід даних
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        img_input = st.camera_input("📸 Фото завдання")
    with col2:
        audio_input = st.audio_input("🎤 Голос")
    
    text_input = st.text_input("💬 Текст:")
    send_btn = st.button("Надіслати 🚀")

if send_btn:
    prompt_parts = []
    current_image = None
    
    if img_input:
        current_image = Image.open(img_input)
        prompt_parts.append(current_image)
    if text_input:
        prompt_parts.append(text_input)
    if audio_input:
        prompt_parts.append({"mime_type": "audio/wav", "data": audio_input.getvalue()})

    if prompt_parts:
        # Додаємо в інтерфейс
        st.session_state.messages.append({
            "role": "user",
            "text": text_input or "[Медіа-запит]",
            "image": current_image
        })
        
        try:
            with st.spinner("Вчитель відповідає..."):
                # Прямий запит без складних сесій для надійності
                response = model.generate_content(prompt_parts)
                answer = response.text
                st.session_state.messages.append({"role": "assistant", "text": answer})
                st.rerun()
        except Exception as e:
            if "429" in str(e):
                st.error("Забагато запитів. Зачекайте 1 хвилину.")
            else:
                st.error(f"Помилка: {e}")

# Озвучка останньої відповіді
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak(st.session_state.messages[-1]["text"])
