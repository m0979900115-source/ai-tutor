import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import base64
from PIL import Image

# ── Конфігурація ──────────────────────────────────────────────
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
except Exception:
    st.error("Налаштуйте GEMINI_KEY у Secrets!")
    st.stop()

SYSTEM_PROMPT = (
    "Ти — дружній та терплячий репетитор. "
    "Допомагай учню зрозуміти тему крок за кроком. "
    "Відповідай коротко та зрозуміло. Завжди спілкуйся українською."
)

@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        model_name="gemini-3-flash-preview",
        system_instruction=SYSTEM_PROMPT,
    )

model = load_model()

# ── Голос (Edge-TTS) без зайвої асинхронності ────────────────
async def _tts_task(text: str):
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def speak(text: str):
    try:
        # Створюємо новий цикл подій спеціально для озвучки
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_bytes = loop.run_until_complete(_tts_task(text))
        loop.close()
        
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'<audio autoplay controls style="width:100%"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.info("Голос готується...")

# ── Стан сесії ────────────────────────────────────────────────
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── UI ────────────────────────────────────────────────────────
st.title("🎓 Твій репетитор")

# Відображення історії чату
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image") is not None:
            st.image(msg["image"], width=250)
        st.markdown(msg["text"])

st.divider()

# Керування вводом
col1, col2 = st.columns(2)
with col1:
    img_file = st.camera_input("📸 Фото завдання")
with col2:
    audio_file = st.audio_input("🎤 Запитай голосом")

user_text = st.chat_input("💬 Напиши питання...")

# Логіка обробки (виконується при кожному оновленні сторінки)
input_data = None
if audio_file:
    input_data = {"type": "audio", "data": audio_file}
elif user_text:
    input_data = {"type": "text", "data": user_text}

if input_data:
    # Перевірка, щоб не відправляти те саме повідомлення двічі
    current_input_id = f"{input_data['type']}_{id(input_data['data'])}"
    if st.session_state.get("last_processed_id") != current_input_id:
        st.session_state.last_processed_id = current_input_id
        
        content = []
        display_text = user_text if user_text else "[Голосове повідомлення]"
        
        if img_file:
            img = Image.open(img_file)
            content.append(img)
        if user_text:
            content.append(user_text)
        if audio_file:
            content.append({"mime_type": "audio/wav", "data": audio_file.getvalue()})

        st.session_state.messages.append({"role": "user", "text": display_text, "image": Image.open(img_file) if img_file else None})
        
        with st.spinner("Репетитор думає..."):
            try:
                response = st.session_state.chat.send_message(content)
                answer = response.text
                st.session_state.messages.append({"role": "assistant", "text": answer})
                st.rerun() # Тут він спрацює коректно, бо ми поза callback
            except Exception as e:
                if "429" in str(e):
                    st.warning("Забагато запитів! Почекай 30 секунд. ☕")
                else:
                    st.error(f"Помилка: {e}")

# Озвучуємо останню відповідь асистента
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    speak(st.session_state.messages[-1]["text"])
