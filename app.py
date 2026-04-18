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
    """Рендерить аудіоплеєр з автовідтворенням."""
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
    # messages = список {"role": "user"/"assistant", "text": ..., "image": ...}
    st.session_state.messages = []

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# ── Хелпер: відправити повідомлення ──────────────────────────
def send_message(text: str = "", image=None, audio_bytes: bytes = None):
    """Формує запит до Gemini, зберігає в історію, озвучує відповідь."""
    if not text and image is None and audio_bytes is None:
        return

    # Зберегти повідомлення юзера для відображення
    st.session_state.messages.append({
        "role": "user",
        "text": text,
        "image": image,
    })

    # Зібрати контент для Gemini
    content = []
    if text:
        content.append(text)
    if audio_bytes:
        content.append({
            "mime_type": "audio/wav",
            "data": base64.b64encode(audio_bytes).decode(),
        })
    if image:
        content.append(image)

    with st.spinner("Репетитор думає…"):
        try:
            response = st.session_state.chat.send_message(content)
            answer = response.text
        except Exception as e:
            answer = f"Помилка: {e}"

    st.session_state.messages.append({
        "role": "assistant",
        "text": answer,
        "image": None,
    })

    # Озвучити — зберігаємо у стані щоб програти після rerun
    st.session_state.pending_voice = answer
    st.rerun()

# ── UI ────────────────────────────────────────────────────────
st.title("🎓 Твій репетитор")

# Історія чату
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], width=220)
        if msg.get("text"):
            st.markdown(msg["text"])

# Програти голос після rerun (один раз)
if "pending_voice" in st.session_state:
    speak(st.session_state.pop("pending_voice"))

# ── Ввід ──────────────────────────────────────────────────────
st.divider()

col_cam, col_audio = st.columns([1, 1])

with col_cam:
    img_file = st.camera_input("📸 Фото завдання")

with col_audio:
    audio_input = st.audio_input("🎤 Запитай голосом")

# Автовідправка голосу — спрацьовує щойно з'являється новий запис
if audio_input is not None:
    audio_id = id(audio_input)
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        image = Image.open(img_file) if img_file else None
        send_message(audio_bytes=audio_input.getvalue(), image=image)

# Текстове поле — відправка по Enter (st.chat_input)
text_input = st.chat_input("💬 Напиши питання…")
if text_input:
    image = Image.open(img_file) if img_file else None
    send_message(text=text_input, image=image)
