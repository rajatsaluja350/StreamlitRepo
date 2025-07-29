
import os
import tempfile
import requests
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes

# OCR.Space API key (free tier)
OCR_API_KEY = "helloworld"
OCR_API_URL = "https://api.ocr.space/parse/image"

# Function to extract text from image using OCR.Space API
def extract_text_from_image(image):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        image.save(tmp.name)
        with open(tmp.name, 'rb') as f:
            response = requests.post(
                OCR_API_URL,
                files={"file": f},
                data={"apikey": OCR_API_KEY, "language": "eng"},
            )
        os.unlink(tmp.name)

    try:
        result = response.json()
        if isinstance(result, dict) and not result.get("IsErroredOnProcessing", True):
            parsed_results = result.get("ParsedResults")
            if parsed_results and isinstance(parsed_results, list):
                return parsed_results[0].get("ParsedText", "")
    except Exception as e:
        st.error(f"Error parsing OCR response: {e}")
    return ""

# Function to extract fields from text
def extract_fields(text):
    import re
    lines = text.splitlines()
    name = lines[0] if lines else "Unknown"
    amount = ""
    date = ""

    for line in lines:
        if not amount:
            match = re.search(r'(\$|Rs\.?)\s?(\d+[.,]?\d*)', line, re.IGNORECASE)
            if match:
                amount = match.group(0)
        if not date:
            match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', line)
            if match:
                date = match.group(0)

    return {"Establishment": name, "Amount": amount, "Date": date}

# Function to process uploaded file
def process_uploaded_file(uploaded_file):
    results = []
    if uploaded_file.type == "application/pdf":
        images = convert_from_bytes(uploaded_file.read())
        for img in images:
            text = extract_text_from_image(img)
            if text:
                results.append(extract_fields(text))
    else:
        image = Image.open(uploaded_file)
        text = extract_text_from_image(image)
        if text:
            results.append(extract_fields(text))
    return results

# Streamlit UI
st.title("📄 Expense Receipt Extractor (OCR API)")

uploaded_files = st.file_uploader("Upload receipt images or PDFs", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        all_results.extend(process_uploaded_file(file))

    if all_results:
        st.success("Extraction complete!")
        st.table(all_results)
    else:
        st.warning("No data extracted from the uploaded files.")
