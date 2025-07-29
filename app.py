
import streamlit as st
import requests
import tempfile
import re
from PIL import Image
from pdf2image import convert_from_bytes

OCR_API_KEY = "helloworld"  # Free demo key from OCR.Space

def extract_text_from_image(image_bytes):
    response = requests.post(
        "https://api.ocr.space/parse/image",
        files={"filename": image_bytes},
        data={"apikey": OCR_API_KEY, "language": "eng"},
    )
    result = response.json()
    if result.get("IsErroredOnProcessing"):
        return ""
    return result["ParsedResults"][0]["ParsedText"]

def parse_receipt_text(text):
    lines = text.splitlines()
    establishment = ""
    amount = ""
    date = ""

    # Try to find establishment name (first non-empty line)
    for line in lines:
        if line.strip():
            establishment = line.strip()
            break

    # Find amount
    amount_match = re.search(r"(Total|Amount|Grand Total)[^\d]*([\d,.]+)", text, re.IGNORECASE)
    if amount_match:
        amount = amount_match.group(2)

    # Find date
    date_match = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})", text)
    if date_match:
        date = date_match.group(0)

    return establishment, amount, date

st.title("🧾 Expense Receipt Extractor (OCR API Version)")

uploaded_files = st.file_uploader("Upload receipt images or PDFs", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

if uploaded_files:
    results = []
    for file in uploaded_files:
        st.write(f"Processing: {file.name}")
        if file.type == "application/pdf":
            images = convert_from_bytes(file.read())
            for img in images:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    img.save(tmp.name)
                    with open(tmp.name, "rb") as f:
                        text = extract_text_from_image(f)
                    os.unlink(tmp.name)
                    est, amt, dt = parse_receipt_text(text)
                    results.append((file.name, est, amt, dt))
        else:
            image = Image.open(file)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                image.save(tmp.name)
                with open(tmp.name, "rb") as f:
                    text = extract_text_from_image(f)
                os.unlink(tmp.name)
                est, amt, dt = parse_receipt_text(text)
                results.append((file.name, est, amt, dt))

    st.subheader("📋 Extracted Receipt Details")
    for fname, est, amt, dt in results:
        st.markdown(f"**File:** {fname}")
        st.markdown(f"- Establishment: `{est}`")
        st.markdown(f"- Amount: `{amt}`")
        st.markdown(f"- Date: `{dt}`")
        st.markdown("---")
