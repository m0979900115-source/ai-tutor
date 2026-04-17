import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io

# 1. КОНФІГУРАЦІЯ (Gemini 3 + Ключ)
API_KEY = "AQ.Ab8RN6LzzJdGJ759IPA37uhSLJUSQ-ciE6AoISavDHFFLVqLCQ"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor 3.0", page_icon="🎓")
st.title("🎓 Мій персональний репетитор")

# Інструкція для ШІ
SYSTEM_PROMPT = """Ти — крутий і терплячий репетитор. 
Твоя мета: допомогти учню зрозуміти логіку завдання на фото або в аудіо. 
Не давай відповідь одразу, став навідні запитання. 
Спілкуйся виключно українською мовою. Хвали дитину за старанність!"""

# 2. ВВІД ДАНИХ
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Або напиши", placeholder="Наприклад: Як почати цю задачу?")

# 3. ЛОГІКА ТА ВІДПОВІДЬ
if img_file or audio_question or user_text:
    with st.spinner('Репетитор уважно слухає та думає...'):
        try:
            content_to_send = [SYSTEM_PROMPT]
            
            # Додаємо текст, якщо він є
            if user_text:
                content_to_send.append(f"Питання учня: {user_text}")
            
            # Додаємо аудіо (ВИПРАВЛЕНО ДЛЯ GEMINI)
            if audio_question:
                audio_bytes = audio_question.getvalue()
                content_to_send.append({
                    "mime_type": "audio/wav",
                    "data": audio_bytes
                })
            
            # Додаємо картинку, якщо вона є
            if img_file:
                img = Image.open(img_file)
                content_to_send.append(img)
            
            # Запит до моделі
            response = model.generate_content(content_to_send)
            answer = response.text
            
            # Виведення тексту
            st.markdown("---")
            st.info(answer)
            
            # ГЕНЕРАЦІЯ ГОЛОСОВОЇ ВІДПОВІДІ (ВИПРАВЛЕНО)
            tts = gTTS(text=answer, lang='uk')
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            # Autoplay дозволяє відразу чути відповідь
            st.audio(audio_buffer, format='audio/mp3', autoplay=True)
            
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
            st.warning("Спробуй ще раз, можливо, файл був завеликий.")

st.caption("Порада: після запису голосу зачекай 2 секунди, щоб файл завантажився.")
