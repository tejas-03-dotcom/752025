from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.utils import platform
from kivy.lang import Builder

from PIL import Image as PILImage, ImageDraw
import pytesseract
from textblob import TextBlob
import os

# Kivy GUI Layout (KV Language)
Builder.load_string('''
<OCRSpellCheckAppMobile>:
    orientation: 'vertical'
    spacing: 10
    padding: 10

    BoxLayout:
        size_hint_y: None
        height: 50
        spacing: 10
        Button:
            text: 'Load Image'
            on_press: root.load_image()
        Button:
            text: 'Process'
            on_press: root.process_image()

    Image:
        id: img_preview
        size_hint: (1, 0.6)

    ScrollView:
        Label:
            id: extracted_text
            size_hint_y: None
            height: self.texture_size[1]
            text_size: (self.width, None)
            padding: (10, 10)
''')


class OCRSpellCheckAppMobile(BoxLayout):
    def __init__(self, android=None, **kwargs):
        super().__init__(**kwargs)
        self.original_image = None
        self.image_path = ""

        # Set Tesseract path for Android
        if platform == 'android':
            from android.storage import app_storage_path
            self.tessdata_dir = os.path.join(app_storage_path(), 'tesseract')
            os.makedirs(self.tessdata_dir, exist_ok=True)
            pytesseract.pytesseract.tesseract_cmd = '/data/data/com.termux/files/usr/bin/tesseract'
        else:
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def load_image(self):
        from kivy import platform
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

            from androidstorage4kivy import Chooser
            chooser = Chooser(self.chooser_callback)
            chooser.choose_content("image/*")
        else:
            from tkinter.filedialog import askopenfilename
            file_path = askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                self.image_path = file_path
                self.display_image(file_path)

    def chooser_callback(self, uri):
        from androidstorage4kivy import SharedStorage
        ss = SharedStorage()
        copy_path = os.path.join(ss.get_cache_dir(), 'selected_image.jpg')
        ss.copy_to_cache(uri, copy_path)
        self.image_path = copy_path
        self.display_image(copy_path)

    def display_image(self, path):
        self.original_image = PILImage.open(path)
        self.ids.img_preview.source = path
        self.ids.img_preview.reload()

    def is_misspelled(self, word):
        if word.isdigit() or len(word) < 2:
            return False
        tb = TextBlob(word)
        corrected = tb.correct()
        return str(corrected).lower() != word.lower()

    def process_image(self):
        if not self.image_path:
            self.ids.extracted_text.text = "Please load an image first!"
            return

        try:
            img = PILImage.open(self.image_path)
            draw = ImageDraw.Draw(img)

            # OCR processing
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            # Extract words and positions
            words = ocr_data['text']
            confidences = ocr_data['conf']
            lefts = ocr_data['left']
            tops = ocr_data['top']
            widths = ocr_data['width']
            heights = ocr_data['height']

            # Process words
            result_text = ""
            misspelled_count = 0

            for i, word in enumerate(words):
                if word.strip() and confidences[i] > 60:
                    if self.is_misspelled(word):
                        # Highlight misspelled words
                        x, y, w, h = lefts[i], tops[i], widths[i], heights[i]
                        draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                        result_text += f"[color=ff0000]{word}[/color] "
                        misspelled_count += 1
                    else:
                        result_text += word + " "

            # Save and display processed image
            processed_path = os.path.join(os.path.dirname(self.image_path), "processed.jpg")
            img.save(processed_path)
            self.display_image(processed_path)

            # Show results
            self.ids.extracted_text.text = result_text
            self.ids.extracted_text.text += f"\n\nFound {misspelled_count} misspelled words"

        except Exception as e:
            self.ids.extracted_text.text = f"Error: {str(e)}"


class MobileOCRApp(App):
    def build(self):
        return OCRSpellCheckAppMobile()


if __name__ == '__main__':
    MobileOCRApp().run()