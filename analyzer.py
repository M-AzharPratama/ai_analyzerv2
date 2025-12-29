import PyPDF2
import re
import requests
import spacy
import json

# ---- FUNGSI 1: Ekstrak teks dari PDF ----
def extract_text_from_pdf(file):
    """Membaca file PDF dan menggabungkan teks dari setiap halaman."""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text


_nlp = None
def _ensure_spacy():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("xx_ent_wiki_sm")
    return _nlp

def extract_person_names(text):
    nlp = _ensure_spacy()
    doc = nlp(text)
    names = set()
    for ent in doc.ents:
        if ent.label_.lower() == "person":
            names.add(ent.text.strip().casefold())
    return names

def check_language_quality_en(text, whitelist=None):
    if not text or not isinstance(text, str):
        return ["⚠️ No text provided for analysis."]

    whitelist = [w.lower() for w in (whitelist or [])]

    # 🚫 Baris yang akan dilewati (biasanya berisi nama atau perkenalan diri)
    skip_keywords = [
        "my name", "i am", "profile", "summary of qualifications",
        "curriculum vitae", "resume", "personal data", "biodata"
    ]

    # 🚫 Jenis saran yang akan diabaikan (terlalu teknis)
    ignore_categories = [
        "TYPOS", "PUNCTUATION", "EN_QUOTES", "HYPHENATION", "MORFOLOGIK_RULE_EN"
    ]

    url = "https://api.languagetool.org/v2/check"
    data = {
        "text": text,
        "language": "en-US"
    }

    try:
        response = requests.post(url, data=data, timeout=20)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return [f"⚠️ Failed to connect to LanguageTool API: {e}"]

    result = response.json()
    issues = []

    for match in result.get("matches", []):
        rule_id = match.get("rule", {}).get("id", "")
        issue_type = match.get("rule", {}).get("issueType", "")
        message = match.get("message", "")
        replacements = match.get("replacements", [])
        offset = match.get("offset", 0)
        length = match.get("length", 0)
        word = text[offset: offset + length].strip()
        word_lower = word.lower()

        # 🚫 Skip baris yang berisi nama/perkenalan
        line_no = text[:offset].count('\n') + 1
        line_text = text.splitlines()[line_no - 1].lower() if line_no - 1 < len(text.splitlines()) else ""
        if any(keyword in line_text for keyword in skip_keywords):
            continue

        # 🚫 Skip kata dalam whitelist
        if any(w in word_lower for w in whitelist):
            continue

        # 🚫 Skip semua uppercase (kemungkinan nama institusi/perusahaan)
        if word.isupper() and len(word) > 2:
            continue

        # 🚫 Abaikan saran yang terlalu kecil / teknis
        if rule_id in ignore_categories or issue_type.lower() in ["typographical", "whitespace"]:
            continue

        suggestion = replacements[0]["value"] if replacements else "-"
        issues.append(f'📝 "{word}" (line {line_no}) → {message} | 💡 Suggestion: {suggestion}')

    if not issues:
        issues = ["✅ No significant grammar or spelling issues detected."]

    return issues

# ---- FUNGSI 3: Cek kata atau frasa yang bisa diperbaiki ----
def check_wording(text):
    """Memberi saran penggantian kata dengan versi yang lebih profesional."""
    replacements = {
        "hardworking": "dedicated",
        "team player": "collaborative professional",
        "responsible for": "managed / led",
        "helped": "contributed to / assisted in",
        "did": "executed / implemented",
        "make": "create / develop",
        "good": "strong / effective",
        "bad": "inefficient / less optimal",
        "a lot": "numerous / multiple",
    }

    text_lower = text.lower()
    suggestions = []

    for bad, good in replacements.items():
        if bad in text_lower:
            suggestions.append(f"💡 Ganti '{bad}' dengan kata yang lebih profesional seperti '{good}'.")

    if not suggestions:
        suggestions.append("✅ Tidak ditemukan kata yang perlu diganti.")
    return suggestions


# ---- FUNGSI 4: Analisis dasar resume ----
def analyze_resume(text):
    text_lower = text.lower()
    score = 0
    feedback = []

    # --- Cek panjang resume ---
    word_count = len(text.split())
    if 200 < word_count < 500:
        score += 20
    else:
        feedback.append("⚠️ Resume terlalu pendek atau terlalu panjang (ideal:200–500 kata).")

    # --- Cek bagian penting ---
    sections = [
        ["education", "pendidikan"],
        ["experience", "pengalaman"],
        ["skills", "keterampilan"],
        ["projects", "projek"]
    ]

    found_sections = []
    for group in sections:
        if any(word in text_lower for word in group):
            found_sections.append(group[0])  # ambil kata utama

    score += len(found_sections) * 10
    if len(found_sections) < len(sections):
        missing_section = [group[0] for group in sections if group[0] not in found_sections]
        feedback.append("⚠️ Beberapa bagian penting tidak ditemukan: " + ", ".join(missing_section))


    # --- Cek kata kunci penting ---
    keywords = ["python", "machine learning", "leadership", "communication", "sql", "data", "analysis"]
    matched = [k for k in keywords if k in text_lower]
    score += len(matched) * 5
    if len(matched) < 3:
        missing_keywords = [k for k in keywords if k not in matched]
        feedback.append(
            "⚠️ Soft skill yang dibutuhkan: "
            + ", ".join(missing_keywords[:5])  # tampilkan maksimal 5 saran
        )

    # --- Panggil analisis tambahan (grammar & wording) ---
    lang_feedback = check_language_quality_en(text, whitelist=["Muhammad Azhar Pratama", "Azhar"])
    wording_feedback = check_wording(text)

    feedback.extend(lang_feedback)
    feedback.extend(wording_feedback)

    # --- Batasi skor maksimum ---
    score = min(score, 100)

    return {
        "score": score,
        "word_count": word_count,
        "found_sections": found_sections,
        "matched": matched,
        "feedback": feedback
    } 
