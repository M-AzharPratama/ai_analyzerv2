import streamlit as st
from analyzer import extract_text_from_pdf, analyze_resume

st.title("🧠 Smart Resume Screening System (SRSS)")
st.write("membantu menyeleksi CV berbahasa Inggris berdasarkan kebutuhan perusahaan.")
st.write("Upload CV dan dapatkan analisis otomatis.")

uploaded_file = st.file_uploader("Upload file CV (PDF)", type=["pdf"])

if uploaded_file:
    text = extract_text_from_pdf(uploaded_file)
    result = analyze_resume(text)

    st.subheader("📊 Hasil Analisis:")
    st.write(f"**Skor Resume:** {result['score']} / 100")
    st.write(f"**Jumlah Kata:** {result['word_count']}")
    st.write(f"**Bagian Ditemukan:** {', '.join(result['found_sections'])}")
    st.write(f"**Skill Yang Dikuasai:** {', '.join(result['matched'])}")

    st.subheader("💡 Saran Perbaikan:")
    for f in result['feedback']:
        st.write("- ", f)
