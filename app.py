
import os
import tempfile
import requests
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes

# OCR.Space API endpoint and key (demo key used here)
OCR_API_URL = "https://api.ocr.space/parse/image"
OCR_API_KEY = "helloworld"

def extract_text_from_image(image_bytes):
    response = requests.post(
        OCR_API_URL,
        files={"filename": image_bytes},
        data={"apikey": OCR_API_KEY, "language": "eng"},
    )
    result = response.json()
    if result.get("IsErroredOnProcessing"):
        return ""
    return result["ParsedResults"][0]["ParsedText"]

def extract_fields(text):
    import re
    lines = text.splitlines()
    name = next((line for line in lines if line.strip()), "Unknown")
    amount_match = re.search(r"\$?\s?(\d+\.\d{2})", text)
    date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    return {
        "Establishment": name.strip(),
        "Amount": amount_match.group(1) if amount_match else "Not found",
        "Date": date_match.group(1) if date_match else "Not found"
    }

def process_uploaded_file(uploaded_file):
    results = []
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
        for image in images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                image.save(tmp_img.name)
                tmp_img.seek(0)
                text = extract_text_from_image(tmp_img)
                results.append(extract_fields(text))
            os.unlink(tmp_img.name)
    else:
        try:
            image = Image.open(uploaded_file)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_img:
                image.save(tmp_img.name)
                tmp_img.seek(0)
                text = extract_text_from_image(tmp_img)
                results.append(extract_fields(text))
        finally:
            if 'tmp_img' in locals() and os.path.exists(tmp_img.name):
                os.unlink(tmp_img.name)
    return results

# Streamlit UI
st.title("Expense Receipt Extractor (OCR API Version)")
uploaded_files = st.file_uploader("Upload receipt images or PDFs", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        all_results.extend(process_uploaded_file(file))

    if all_results:
        st.write("### Extracted Receipt Data")
        st.table(all_results)
    else:
        st.warning("No data extracted from the uploaded files.")
