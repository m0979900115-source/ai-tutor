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
                    {"type": "text", "text": "Распознай текст и задание на этом фото. Опиши его кратко для учителя-ментора. Отвечай на русском."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка зрения: {e}"

# --- Озвучка (Быстрый и живой женский голос) ---
async def generate_audio_base64(text):
    # Убираем символы разметки, чтобы голос не запинался
    clean_text = text.replace('*', '').replace('#', '').replace('-', ' ').replace('>', ' ').strip()
    
    communicate = edge_tts.Communicate(
        clean_text, 
        "ru-RU-SvetlanaNeural", 
        rate="+20%", 
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
            audio_html = f"""
                <audio autoplay="true">
                    <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                </audio>
            """
            st.components.v1.html(audio_html, height=0)
    except:
        pass

# --- Интерфейс ---
st.set_page_config(page_title="AI Mentor", page_icon="🎓")
st.title("🎓 Ваш наставник (Режим Ментора)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Отображение истории
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

st.divider()

# Панель ввода
with st.container():
    col1, col2 = st.columns(2)
    with col1: 
        img_file = st.camera_input("📸 Сфотографировать задание")
    with col2: 
        audio_file = st.audio_input("🎤 Спросить голосом")
    
    u_text = st.chat_input("Напиши свой вопрос или ответ учителю...")

# --- Обработка логики ---
if img_file or audio_file or u_text:
    final_query = ""
    display_text = ""

    if img_file:
        with st.spinner("Смотрю на задание..."):
            img_desc = analyze_image(img_file.getvalue())
            final_query += f"\n[УЧЕНИК ПОКАЗАЛ ФОТО]: {img_desc}\n"
            display_text += "📷 (Показал фото задания) "

    if audio_file:
        with st.spinner("Слушаю..."):
            voice_text = transcribe_audio(audio_file.getvalue())
            final_query += f"\n[УЧЕНИК СПРОСИЛ ГОЛОСОМ]: {voice_text}"
            display_text += f"🎤 {voice_text}"
            st.info(f"🎤 Распознано: {voice_text}")

    if u_text:
        final_query += f"\n[УЧЕНИК НАПИСАЛ]: {u_text}"
        display_text += u_text

    if final_query:
        st.session_state.messages.append({"role": "user", "content": display_text})
        
        with st.chat_message("assistant"):
            with st.spinner("Учитель думает над подсказкой..."):
                try:
                    resp = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {
                                "role": "system", 
                                "content": """Ты — профессиональный учитель-ментор. Твоя задача — помогать ученику прийти к ответу самому.
                                ПРАВИЛА:
                                1. НИКОГДА не давай готовое решение или ответ сразу.
                                2. Если ученик дает задачу, спроси, как он думает, с чего нужно начать.
                                3. Давай только ОДНУ небольшую подсказку за раз.
                                4. Используй наводящие вопросы (например: 'А что если мы попробуем сначала...?', 'Помнишь, как решаются такие примеры?').
                                5. Хвали за старания и правильные мысли.
                                6. Отвечай кратко, по-доброму и только на русском языке. Не используй сложную разметку типа таблиц или жирного текста, чтобы голос звучал чисто."""
                            },
                            *st.session_state.messages[:-1], # Передаем историю без последнего служебного сообщения
                            {"role": "user", "content": final_query}
                        ]
                    )
                    ans = resp.choices[0].message.content
                    st.write(ans)
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    
                    speak(ans)
                except Exception as e:
                    st.error(f"Ошибка: {e}")
