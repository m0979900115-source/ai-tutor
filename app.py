import streamlit as st
import google.generativeai as genai
from elevenlabs.client import ElevenLabs
from PIL import Image
import io
import base64

# 1. КОНФІГУРАЦІЯ
try:
    genai.configure(api_key=st.secrets["GEMINI_KEY"])
    # Створюємо клієнт ElevenLabs з новим ключем
    el_client = ElevenLabs(api_key=st.secrets["ELEVENLABS_KEY"])
except Exception as e:
    st.error("Помилка секретів у Streamlit!")
    st.stop()

model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Tutor Pro", page_icon="🎓")
st.title("🎓 Твій живий репетитор")

SYSTEM_PROMPT = "Ти — професійний репетитор. Допомагай учню зрозуміти завдання через запитання. Спілкуйся виключно українською."

# 2. ВХІДНІ ДАНІ
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
                content.append({"mime_type": "audio/wav", "data": audio_question.getvalue()})
            if img_file:
                content.append(Image.open(img_file))
            
            response = model.generate_content(content)
            answer = response.text
            st.info(answer)
            
            # --- ОЗВУЧКА ---
            try:
                # Використовуємо Multilingual модель для кращої української
                audio_stream = el_client.text_to_speech.convert(
                    text=answer,
                    voice_id="N2lVS1wzexD6kS831tgZ", # Приємний голос (Jarvis/Ukrainian-friendly)
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                
                audio_bytes = b"".join(audio_stream)
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
                audio_html = f"""
                    <audio autoplay="true" controls style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                    </audio>
                """
                st.markdown(audio_html, unsafe_allow_html=True)
                
            except Exception as e_audio:
                st.warning(f"Деталі помилки голосу: {str(e_audio)}")
            
        except Exception as e:
            st.error(f"Помилка Gemini: {str(e)}")
