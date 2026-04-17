import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from PIL import Image
import io
import base64

# 1. НАЛАШТУВАННЯ
try:
    # Беремо ключі з Secrets
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    el_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_KEY"])
except Exception as e:
    st.error("Помилка ключів у Secrets. Перевір GEMINI_KEY та ELEVENLABS_KEY.")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor Pro", page_icon="🎓")
st.title("🎓 Твій реалістичний репетитор")

SYSTEM_PROMPT = """Ти — професійний репетитор. Спілкуйся живо, українською мовою. 
Допомагай учню зрозуміти завдання через запитання. Хвали за успіхи!"""

# 2. ІНТЕРФЕЙС
img_file = st.camera_input("📸 Фото завдання")
audio_question = st.audio_input("🎤 Запитай голосом")
user_text = st.text_input("💬 Твоє питання")

# 3. ЛОГІКА
if img_file or audio_question or user_text:
    with st.spinner('Репетитор думає...'):
        try:
            content = [SYSTEM_PROMPT]
            if user_text: content.append(user_text)
            if audio_question:
                content.append({
                    "mime_type": "audio/wav",
                    "data": audio_question.getvalue()
                })
            if img_file:
                content.append(Image.open(img_file))
            
            # Отримуємо текст від Gemini
            response = model.generate_content(content)
            answer = response.text
            
            st.info(answer)
            
            # --- ОЗВУЧКА ELEVENLABS ---
            try:
                # Генеруємо аудіо (Голос Oleksandr)
                audio_gen = el_client.generate(
                    text=answer,
                    voice="Oleksandr",
                    model="eleven_multilingual_v2"
                )
                
                audio_bytes = b"".join(list(audio_gen))
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                # Виводимо плеєр
                audio_html = f"""
                    <audio autoplay="true" controls style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
            except Exception as e_audio:
                st.warning("Текст готовий, але голос тимчасово недоступний.")
            
        except Exception as e:
            st.error(f"Помилка: {str(e)}")
