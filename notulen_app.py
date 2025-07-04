import streamlit as st
import openai
import tempfile
import os
import subprocess

# Inisialisasi Groq API
openai.api_key = st.secrets["GROQ_API_KEY"]
openai.api_base = "https://api.groq.com/openai/v1"

st.set_page_config(page_title="Transkrip Hasil Meeting", layout="centered")
st.markdown(
    """
    <div style='text-align: center;'>
        <img src='https://github.com/LinkedList002/notulen-app/blob/main/Logo%20APNM%20New.png?raw=true' width='150'/>
        <h1>Aplikasi Notulen Meeting</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.write("Upload file audio hasil meeting, AI akan transkrip dan membuat notulen otomatis (via Groq)")

SUPPORTED_FORMATS = ["flac", "m4a", "mp3", "mp4", "mpeg", "mpga", "oga", "ogg", "wav", "webm"]

if "transcript" not in st.session_state:
    st.session_state.transcript = None
if "summary" not in st.session_state:
    st.session_state.summary = None

uploaded_file = st.file_uploader("🎙 Upload file audio (.mp3, .m4a, .wav, dll)", type=SUPPORTED_FORMATS)

def split_audio_ffmpeg(input_path, chunk_length_sec=300):
    output_files = []
    duration_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_path
    ]
    duration = float(subprocess.check_output(duration_cmd).decode().strip())
    total_parts = int(duration // chunk_length_sec) + 1

    for i in range(total_parts):
        start_time = i * chunk_length_sec
        output_path = f"{input_path}_part{i}.mp3"
        split_cmd = [
            "ffmpeg", "-y", "-i", input_path, "-ss", str(start_time), "-t", str(chunk_length_sec),
            "-acodec", "copy", output_path
        ]
        subprocess.run(split_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        output_files.append(output_path)

    return output_files

if uploaded_file and st.session_state.transcript is None:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    if file_ext not in SUPPORTED_FORMATS:
        st.error(f"❌ Format file tidak didukung: .{file_ext}")
        st.stop()

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    st.success("✅ File berhasil diupload. Memproses...")

    with st.spinner("🔄 Memecah audio dan mentranskripsi..."):
        try:
            chunk_paths = split_audio_ffmpeg(audio_path)
            transcripts = []

            for idx, chunk in enumerate(chunk_paths):
                st.info(f"📤 Memproses bagian {idx + 1} dari {len(chunk_paths)}...")
                with open(chunk, "rb") as f:
                    result = openai.Audio.transcribe(
                        model="whisper-large-v3",  # multilingual model di Groq
                        file=f,
                        response_format="text",
                        language="id"  # Bahasa Indonesia
                    )
                    transcripts.append(result)

                os.remove(chunk)

            st.session_state.transcript = "\n".join(transcripts)

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat transkripsi: {e}")
            st.stop()
        finally:
            os.remove(audio_path)

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

                response = openai.ChatCompletion.create(
                    model="llama3-70b-8192",  # LLM dari Groq
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
