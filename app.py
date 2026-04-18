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
    "Відповідай коротко та зрозуміло. "
    "Завжди спілкуйся українською мовою."
)

@st.cache_resource
def load_model():
    return genai.GenerativeModel(
        model_name="gemini-3-flash-preview",
        system_instruction=SYSTEM_PROMPT,
    )

model = load_model()

# ── Голос (Edge-TTS) ──────────────────────────────────────────
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

# ── Транскрибація ──────────────────────────────────────────────
def transcribe(audio_bytes: bytes) -> str:
    try:
        # Передаємо байти напряму без base64 кодування
        response = model.generate_content([
            "Розпізнай мову і поверни лише текст без пояснень.",
            {"mime_type": "audio/wav", "data": audio_bytes},
        ])
        return response.text.strip()
    except Exception as e:
        if "429" in str(e):
            return "[Ліміт запитів вичерпано. Зачекайте 1 хвилину]"
        return f"[Помилка розпізнавання: {e}]"

# ── Стан сесії ────────────────────────────────────────────────
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ── Відправка повідомлення ───────────────────────────────────
def send_message(text: str = "", image=None, audio_bytes: bytes = None):
    if not text and image is None and audio_bytes is None:
        return

    display_text = text
    if audio_bytes and not text:
        with st.spinner("Розпізнаю голос…"):
            display_text = transcribe(audio_bytes)

    # Додаємо повідомлення користувача в історію
    st.session_state.messages.append({
        "role": "user",
        "text": display_text,
        "image": image,
    })

    # Формуємо контент для Gemini
    content = []
    if text: content.append(text)
    if image: content.append(image)
    if audio_bytes:
        content.append({"mime_type": "audio/wav", "data": audio_bytes})

    with st.spinner("Репетитор думає…"):
        try:
            response = st.session_state.chat.send_message(content)
            answer = response.text
        except Exception as e:
            if "429" in str(e):
                answer = "Ой! Я отримав забагато запитів. Давай зачекаємо хвилину і продовжимо? ☕"
            else:
                answer = f"Виникла технічна помилка: {e}"

    st.session_state.messages.append({
        "role": "assistant",
        "text": answer,
    })

    st.session_state.pending_voice = answer
    st.rerun()

# ── UI ────────────────────────────────────────────────────────
st.title("🎓 Твій репетитор")

# Відображення історії
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"],
