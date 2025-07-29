
import streamlit as st
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import re
import tempfile
import os

st.title("🧾 Expense Receipt Extractor")

uploaded_files = st.file_uploader("Upload receipt images or PDFs", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def extract_text_from_pdf(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file.read())
        tmp_file_path = tmp_file.name
    images = convert_from_path(tmp_file_path)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    os.remove(tmp_file_path)
    return text

def extract_fields(text):
    # Extract date
    date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})', text)
    date = date_match.group(0) if date_match else "Not found"

    # Extract amount
    amount_match = re.search(r'(Total|Amount|AMT)[^\d]*(\d+[.,]\d{2})', text, re.IGNORECASE)
    amount = amount_match.group(2) if amount_match else "Not found"

    # Extract establishment name (first line with letters and spaces)
    lines = text.splitlines()
    name = "Not found"
    for line in lines:
        if re.search(r'[A-Za-z]{2,}', line):
            name = line.strip()
            break

    return name, amount, date

if uploaded_files:
    results = []
    for file in uploaded_files:
        if file.type == "application/pdf":
            text = extract_text_from_pdf(file)
        else:
            image = Image.open(file)
            text = extract_text_from_image(image)

        name, amount, date = extract_fields(text)
        results.append({"File": file.name, "Establishment": name, "Amount": amount, "Date": date})

    st.subheader("📋 Extracted Information")
    st.table(results)
