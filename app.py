import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from PIL import Image
import io
import base64

# 1. БЕЗПЕЧНЕ НАЛАШТУВАННЯ
try:
    API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("Налаштуйте GEMINI_KEY у Secrets!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor 3.0", page_icon="🎓")
st.title("🎓 Мій персональний репетитор")

SYSTEM_PROMPT = "Ти — крутий репетитор. Допоможи учню зрозуміти завдання. Не давай відповідь одразу, став навідні запитання. Спілкуйся українською."

# 2. ВВІД
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Твоє питання")

# 3. ЛОГІКА
if img_file or audio_question or user_text:
    with st.spinner('Думаю...'):
        try:
            content = [SYSTEM_PROMPT]
            if user_text: content.append(user_text)
            if audio_question: content.append({"mime_type": "audio/wav", "data": audio_question.getvalue()})
            if img_file: content.append(Image.open(img_file))
            
            response = model.generate_content(content)
            answer = response.text
            
            st.info(answer)
            
            # --- НОВИЙ МЕТОД: BASE64 (Найбільш сумісний з мобільними) ---
            try:
                tts = gTTS(text=answer, lang='uk')
                fp = io.BytesIO()
                tts.write_to_fp(fp)
                fp.seek(0)
                
                # Кодуємо звук у текст (Base64)
                audio_base64 = base64.b64encode(fp.read()).decode()
                
                # Створюємо HTML-плеєр, який браузер точно зрозуміє
                audio_html = f"""
                    <audio autoplay="true" controls>
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                
            except Exception as e_audio:
                st.warning("Голос не зміг завантажитися, але текст вище!")
            # ---------------------------------------------------------
            
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
