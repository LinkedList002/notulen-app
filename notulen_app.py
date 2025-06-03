import streamlit as st
from openai import OpenAI
import tempfile
import os

# Inisialisasi client OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Notulen Otomatis", layout="centered")
st.title("📝 Aplikasi Notulen Rapat Otomatis")
st.write("Upload file audio rapat, dan dapatkan transkripsi + notulen otomatis dalam Bahasa Indonesia.")

# Upload file audio
uploaded_file = st.file_uploader("🎙 Upload file audio (.mp3, .m4a, .wav, dll)", type=["mp3", "m4a", "wav", "mp4"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    st.success("✅ File berhasil diupload. Memproses...")

    # Transkripsi dengan Whisper API
    with st.spinner("Mentranskripsi audio..."):
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="id"
            )
            text_transcript = transcript.text

    st.subheader("📄 Transkrip")
    st.text_area("Hasil transkripsi:", value=text_transcript, height=300)

    # Ringkasan otomatis dengan GPT
    with st.spinner("Membuat notulen otomatis..."):
        prompt = f"""
Tolong buatkan notulen rapat dalam Bahasa Indonesia berdasarkan transkrip berikut:

{text_transcript}

Format poin-poin. Sertakan:
- Ringkasan diskusi
- Keputusan
- Tugas dan tindak lanjut
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Kamu adalah asisten yang ahli merangkum rapat."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        summary = response.choices[0].message.content

    st.subheader("📝 Notulen Otomatis")
    st.text_area("Notulen:", value=summary, height=300)

    st.download_button("💾 Unduh Notulen", summary, file_name="notulen_rapat.txt")

    os.remove(audio_path)
