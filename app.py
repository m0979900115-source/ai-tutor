import streamlit as st
import google.generativeai as genai
import edge_tts
import asyncio
import base64
from PIL import Image

# 1. КОНФІГУРАЦІЯ (Тільки Gemini)
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
except Exception:
    st.error("Налаштуйте GEMINI_KEY у Secrets!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.title("🎓 Твій надійний репетитор")

# Функція для генерації голосу Microsoft Edge
async def generate_voice(text):
    # Голос 'uk-UA-OstapNeural' або 'uk-UA-PolinaNeural'
    communicate = edge_tts.Communicate(text, "uk-UA-PolinaNeural")
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# 2. ВВІД
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Твоє питання")

# 3. ЛОГІКА
if img_file or audio_question or user_text:
    with st.spinner('Репетитор готує відповідь...'):
        try:
            content = ["Ти професійний репетитор. Допомагай зрозуміти тему. Спілкуйся українською."]
            if user_text: content.append(user_text)
            if audio_question: content.append({"mime_type": "audio/wav", "data": audio_question.getvalue()})
            if img_file: content.append(Image.open(img_file))
            
            response = model.generate_content(content)
            answer = response.text
            st.info(answer)
            
            # ОЗВУЧКА (Edge-TTS)
            try:
                audio_bytes = asyncio.run(generate_voice(answer))
                audio_base64 = base64.b64encode(audio_bytes).decode()
                audio_html = f"""
                    <audio autoplay="true" controls style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            except Exception as e_voice:
                st.warning("Голос тимчасово не зміг завантажитись.")
                
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
