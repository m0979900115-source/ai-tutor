import streamlit as st
from groq import Groq
import edge_tts
import asyncio
import base64
from PIL import Image
import io

# --- Инициализация клиента Groq ---
try:
    client = Groq(api_key=st.secrets["GROQ_KEY"])
except Exception:
    st.error("Ошибка: Добавьте GROQ_KEY в Secrets!")
    st.stop()

# --- Функция перевода голоса в текст (Whisper) ---
def transcribe_audio(audio_bytes):
    try:
        audio_file = ("speech.wav", audio_bytes)
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo", 
            response_format="text",
            language="ru"
        )
        return transcription
    except Exception as e:
        return f"Ошибка распознавания: {e}"

# --- Функция анализа фото (Vision) ---
def analyze_image(image_bytes):
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Распознай текст и задание на этом фото. Отвечай на русском языке."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка зрения: {e}"

# --- Улучшенная Озвучка (Живой женский голос) ---
async def generate_audio_base64(text):
    # Очистка текста от символов разметки, которые робот пытается прочитать
    clean_text = text.replace('*', '').replace('#', '').replace('-', ' ').strip()
    
    # Настройки: rate="+20%" убирает медлительность, pitch="+2Hz" делает голос живее
    communicate = edge_tts.Communicate(
        clean_text, 
        "ru-RU-SvetlanaNeural", 
        rate="+25%", 
        pitch="+2Hz"
    )
    
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    
    if audio_data:
        return base64.b64encode(audio_data).decode()
    return None

def speak(text):
    try:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        b64_audio = new_loop.run_until_complete(generate_audio_base64(text))
        new_loop.close()
        
        if b64_audio:
            # Использование HTML компонента для более стабильного автозапуска в браузере
            audio_html = f"""
                <audio autoplay="true">
                    <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                </audio>
            """
            st.components.v1.html(audio_html, height=0)
    except:
        pass

# --- Основной Интерфейс ---
st.set_page_config(page_title="AI Tutor", page_icon="🎓")
st.title("🎓 Ваш репетитор (Версия 3.0)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории чата
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.divider()

# Панель инструментов
with st.container():
    col1, col2 = st.columns(2)
    with col1: 
        img_file = st.camera_input("📸 Сфотографировать задание")
    with col2: 
        audio_file = st.audio_input("🎤 Задать вопрос голосом")
    
    u_text = st.chat_input("Или напишите вопрос здесь...")

# --- Логика обработки ---
if img_file or audio_file or u_text:
    final_query = ""
    display_text = ""

    if img_file:
        with st.spinner("Анализирую фото..."):
            img_desc = analyze_image(img_file.getvalue())
            final_query += f"\n[ЗАДАНИЕ НА ФОТО]: {img_desc}\n"
            display_text += "📷 (Фото задания отправлено) "

    if audio_file:
        with st.spinner("Слушаю..."):
            voice_text = transcribe_audio(audio_file.getvalue())
            final_query += f"\n[ГОЛОСОВОЙ ВОПРОС]: {voice_text}"
            display_text += f"🎤 Голос: {voice_text}"
            st.info(f"🎤 Распознано: {voice_text}")

    if u_text:
        final_query += f"\n[ВОПРОС ТЕКСТОМ]: {u_text}"
        display_text += u_text

    if final_query:
        st.session_state.messages.append({"role": "user", "content": display_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Учитель думает..."):
                try:
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Ты добрый и быстрый учитель. Объясняй кратко и понятно на русском языке. Не используй много спецсимволов."},
                            *st.session_state.messages,
                            {"role": "user", "content": final_query}
                        ]
                    )
                    ans = resp.choices[0].message.content
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    
                    # Запуск озвучки
                    speak(ans)
                except Exception as e:
                    st.error(f"Ошибка Groq: {e}")
