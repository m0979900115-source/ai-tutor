import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import base64
import nest_asyncio
from PIL import Image

nest_asyncio.apply()

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

# ── Голос ─────────────────────────────────────────────────────
async def _tts(text: str) -> bytes:
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def speak(text: str) -> None:
    try:
        audio_bytes = asyncio.get_event_loop().run_until_complete(_tts(text))
        b64 = base64.b64encode(audio_bytes).decode()
        st.markdown(
            f'<audio autoplay controls style="width:100%">'
            f'<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"Голос недоступний: {e}")

# ── Стан сесії ────────────────────────────────────────────────
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Функція відправки ─────────────────────────────────────────
def send_message():
    # Забираємо дані з тимчасових ключів віджетів
    text = st.session_state.get("user_text", "")
    img_file = st.session_state.get("user_cam", None)
    audio_file = st.session_state.get("user_audio", None)

    if not text and not img_file and not audio_file:
        return

    # Підготовка контенту
    content = []
    display_msg = {"role": "user", "text": text, "image": None}

    if img_file:
        image = Image.open(img_file)
        content.append(image)
        display_msg["image"] = image
    
    if text:
        content.append(text)
    
    if audio_file:
        audio_bytes = audio_file.getvalue()
        content.append({"mime_type": "audio/wav", "data": audio_bytes})
        if not text:
            display_msg["text"] = "[Голосове повідомлення]"

    st.session_state.messages.append(display_msg)

    # Запит до Gemini
    with st.spinner("Репетитор думає..."):
        try:
            response = st.session_state.chat.send_message(content)
            answer = response.text
        except Exception as e:
            if "429" in str(e):
                answer = "Забагато запитів! Давай зробимо паузу на 1 хвилину. ☕"
            else:
                answer = f"Помилка: {e}"

    st.session_state.messages.append({"role": "assistant", "text": answer})
    st.session_state.pending_voice = answer

    # ОЧИЩЕННЯ ВВОДУ: видаляємо дані з віджетів, щоб не було циклу
    for key in ["user_text", "user_cam", "user_audio"]:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

# ── UI ────────────────────────────────────────────────────────
st.title("🎓 Твій репетитор")

# Чат
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image") is not None:
            st.image(msg["image"], width=250)
        st.markdown(msg["text"])

# Озвучка
if "pending_voice" in st.session_state:
    speak(st.session_state.pop("pending_voice"))

st.divider()

# Елементи вводу з ключами (Key) для керування станом
col1, col2 = st.columns(2)
with col1:
    st.camera_input("📸 Фото", key="user_cam", on_change=send_message)
with col2:
    st.audio_input("🎤 Голос", key="user_audio", on_change=send_message)

st.chat_input("💬 Напиши питання...", key="user_text", on_submit=send_message)
