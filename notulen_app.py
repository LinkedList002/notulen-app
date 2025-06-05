import streamlit as st
from openai import OpenAI
import tempfile
import os

# Inisialisasi client OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Transkrip Hasil Meeting", layout="centered")
st.title("📝 Aplikasi Notulen Meeting")
st.write("Upload file audio hasil meeting, engine AI Whisper + OpenAI")

# Format yang didukung oleh Whisper API
SUPPORTED_FORMATS = ["flac", "m4a", "mp3", "mp4", "mpeg", "mpga", "oga", "ogg", "wav", "webm"]

# Upload file audio
uploaded_file = st.file_uploader("🎙 Upload file audio (.mp3, .m4a, .wav, dll)", type=SUPPORTED_FORMATS)

if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        st.error(f"❌ Format file tidak didukung: .{file_ext}. Format yang didukung: {', '.join(SUPPORTED_FORMATS)}")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
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
        system_message = """Anda adalah asisten ahli yang mengkhususkan diri dalam membuat notulen rapat yang ringkas dan dapat ditindaklanjuti dari transkrip audio. Tugas Anda adalah mengekstrak wawasan, diskusi kunci, dan langkah-langkah selanjutnya yang dapat ditindaklanjuti dari teks yang diberikan."""

        prompt = f"""
        1. Poin-poin Diskusi Utama
        - Topik yang dibahas
        - Wawasan penting
        - Percakapan signifikan

        2. Poin-poin Penting
        - Pembelajaran inti
        - Wawasan kritis
        - Implikasi strategis

        3. Tindak Lanjut
        - Tugas atau langkah selanjutnya
        - Prioritas tindakan yang jelas
        - Tanggung jawab yang disebutkan (jika ada)

{text_transcript}

        Pedoman:
        - Gunakan Bahasa Indonesia yang baik dan benar
        - Jangan gunakan placeholder seperti '[Tanggal]' atau '[Nama]'
        - Sajikan informasi dengan ringkas dan jelas
        - Prioritaskan informasi yang dapat ditindaklanjuti
        - Gunakan format markdown
        - Jika informasi tidak lengkap atau tidak jelas, beri catatan
        """
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content":system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        summary = response.choices[0].message.content

    st.subheader("📝 Notulen Otomatis")
    st.text_area("Notulen:", value=summary, height=300)

    st.download_button("💾 Unduh Notulen", summary, file_name="notulen_rapat.txt")

    os.remove(audio_path)
