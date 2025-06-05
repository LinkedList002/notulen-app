import streamlit as st
from openai import OpenAI
import tempfile
import os

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="Transkrip Hasil Meeting", layout="centered")
st.markdown(
    """
    <div style='text-align: center;'>
        <img src='https://raw.githubusercontent.com/username/repo-name/main/logo.png' width='150'/>
        <h1>Aplikasi Notulen Meeting</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("Upload file audio hasil meeting, engine AI Whisper + OpenAI")

SUPPORTED_FORMATS = ["flac", "m4a", "mp3", "mp4", "mpeg", "mpga", "oga", "ogg", "wav", "webm"]

if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "summary" not in st.session_state:
    st.session_state.summary = None

uploaded_file = st.file_uploader("🎙 Upload file audio (.mp3, .m4a, .wav, dll)", type=SUPPORTED_FORMATS)

if uploaded_file and st.session_state.transcript is None:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        st.error(f"❌ Format file tidak didukung: .{file_ext}")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    st.success("✅ File berhasil diupload. Memproses...")

    # Proses transkripsi dengan pengecekan error
    with st.spinner("Mentranskripsi audio..."):
        try:
            with open(audio_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="id"
                )
                st.session_state.transcript = result.text if hasattr(result, "text") else "Gagal membaca hasil transkrip."
        except Exception as e:
            st.error(f"Terjadi kesalahan saat transkripsi: {e}")
            st.stop()
        finally:
            os.remove(audio_path)

# Tampilkan hasil transkripsi
if st.session_state.transcript:
    st.subheader("📄 Transkrip")
    st.text_area("Hasil transkripsi:", value=st.session_state.transcript, height=300)

    if st.session_state.summary is None:
        with st.spinner("Membuat notulen otomatis..."):
            try:
                system_message = "Kamu adalah asisten yang ahli merangkum rapat."

                prompt = f"""
Tolong buatkan notulen rapat dalam Bahasa Indonesia berdasarkan transkrip berikut:

{st.session_state.transcript}

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
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.4
                )
                st.session_state.summary = response.choices[0].message.content
            except Exception as e:
                st.error(f"Gagal membuat notulen otomatis: {e}")
                st.stop()

    st.subheader("📝 Notulen Otomatis")
    st.text_area("Notulen:", value=st.session_state.summary, height=300)
    st.download_button("💾 Unduh Notulen", st.session_state.summary, file_name="notulen_rapat.txt")

    if st.button("🔄 Proses file baru"):
        st.session_state.clear()
        st.success("Silakan upload file audio baru untuk mulai proses lagi.")
        st.stop()
