import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io
import time

# 1. БЕЗПЕЧНЕ НАЛАШТУВАННЯ
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Ключ GEMINI_KEY не знайдено! Перевірте вкладку Secrets у налаштуваннях Streamlit.")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor 3.0", page_icon="🎓")
st.title("🎓 Мій персональний репетитор")

SYSTEM_PROMPT = """Ти — крутий репетитор. Допоможи учню зрозуміти завдання. 
Не давай відповідь одразу, став навідні запитання. 
Спілкуйся виключно українською. Будь емоційним та підбадьорюй!"""

# 2. ВВІД ДАНИХ
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Або напиши", placeholder="Наприклад: Що робити в цій задачі?")

# 3. ЛОГІКА ТА ВІДПОВІДЬ
if img_file or audio_question or user_text:
    with st.spinner('Репетитор готує відповідь...'):
        try:
            content_to_send = [SYSTEM_PROMPT]
            
            if user_text:
                content_to_send.append(f"Питання: {user_text}")
            
            if audio_question:
                audio_bytes = audio_question.getvalue()
                content_to_send.append({"mime_type": "audio/wav", "data": audio_bytes})
            
            if img_file:
                img = Image.open(img_file)
                content_to_send.append(img)
            
            response = model.generate_content(content_to_send)
            answer = response.text
            
            st.markdown("---")
            st.info(answer)
            
            # --- ПОКРАЩЕНИЙ БЛОК ОЗВУЧКИ ---
            try:
                # Створюємо аудіо
                tts = gTTS(text=answer, lang='uk')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio_bytes = audio_buffer.getvalue() # Отримуємо байти напряму
                
                # Відтворюємо
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)
            except Exception as e_tts:
                st.warning("Текст готовий, але виникла помилка з голосом. Спробуй ще раз через мить.")
            # ------------------------------
            
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
