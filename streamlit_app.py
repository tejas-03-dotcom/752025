import streamlit as st
from PIL import Image, ImageDraw
import pytesseract
from textblob import TextBlob
import io
import base64

# Optional: Tesseract path (set this locally if needed)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

st.set_page_config(page_title="OCR Spell Check", layout="wide")
st.title("🖼️ OCR Spell Check Web App")

st.write("Upload an image with text. This app will extract the text using OCR and highlight any misspelled words.")

# File uploader
uploaded_file = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg", "bmp", "tiff"])

def is_misspelled(word):
    if word.isdigit() or len(word) < 2:
        return False
    blob = TextBlob(word)
    return blob.correct().lower() != word.lower()

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Uploaded Image", use_column_width=True)

    if st.button("🔍 Process Image"):
        with st.spinner("Processing..."):
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            words = ocr_data['text']
            confs = ocr_data['conf']
            lefts = ocr_data['left']
            tops = ocr_data['top']
            widths = ocr_data['width']
            heights = ocr_data['height']

            draw = ImageDraw.Draw(image)
            result_text = ""
            misspelled_count = 0

            for i, word in enumerate(words):
                conf = int(confs[i]) if confs[i].isdigit() else 0
                if word.strip() and conf > 60:
                    if is_misspelled(word):
                        misspelled_count += 1
                        x, y = lefts[i], tops[i]
                        w, h = widths[i], heights[i]
                        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                        result_text += f":red[{word}] "
                    else:
                        result_text += word + " "

        st.subheader("🔤 Extracted Text")
        st.markdown(result_text)

        st.subheader("📌 Annotated Image with Highlighted Errors")
        st.image(image, caption="Misspelled words highlighted in red", use_column_width=True)

        # Allow download of image
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        b64 = base64.b64encode(img_bytes).decode()

        st.markdown(
            f'<a href="data:image/png;base64,{b64}" download="annotated_image.png">📥 Download Annotated Image</a>',
            unsafe_allow_html=True
        )

        st.success(f"Done! Found {misspelled_count} misspelled word(s).")

