import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import pytesseract
import numpy as np
from spellchecker import SpellChecker

# Set tesseract path (update this to your Tesseract installation path)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class OCRSpellCheckApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image OCR with Spell Check")
        self.root.geometry("1000x700")

        # Variables
        self.image_path = ""
        self.original_image = None
        self.tk_image = None
        self.ocr_data = None

        # Create widgets
        self.create_widgets()

        # Initialize spell checker
        self.spell = SpellChecker()

    def create_widgets(self):
        # Top frame for buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10)

        # Load image button
        load_btn = tk.Button(top_frame, text="Load Image", command=self.load_image)
        load_btn.pack(side=tk.LEFT, padx=5)

        # Process button
        process_btn = tk.Button(top_frame, text="Process Image", command=self.process_image)
        process_btn.pack(side=tk.LEFT, padx=5)

        # Save button
        save_btn = tk.Button(top_frame, text="Save Result", command=self.save_result)
        save_btn.pack(side=tk.LEFT, padx=5)

        # Image display
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)

        # Text display
        self.text_display = tk.Text(self.root, height=10, wrap=tk.WORD)
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")]
        )
        if file_path:
            self.image_path = file_path
            self.original_image = Image.open(file_path)
            self.display_image(self.original_image)
            self.text_display.delete(1.0, tk.END)

    def display_image(self, image):
        # Resize image for display while maintaining aspect ratio
        max_width = 800
        max_height = 400
        img_width, img_height = image.size

        if img_width > max_width or img_height > max_height:
            ratio = min(max_width / img_width, max_height / img_height)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(image)
        self.image_label.config(image=self.tk_image)

    def process_image(self):
        if not self.image_path:
            messagebox.showerror("Error", "Please load an image first")
            return

        try:
            # Perform OCR
            img = Image.open(self.image_path)
            self.ocr_data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT
            )

            # Get all words and their bounding boxes
            words = self.ocr_data['text']
            confidences = self.ocr_data['conf']
            lefts = self.ocr_data['left']
            tops = self.ocr_data['top']
            widths = self.ocr_data['width']
            heights = self.ocr_data['height']

            # Filter out empty words and words with low confidence
            valid_indices = [i for i, word in enumerate(words)
                             if word.strip() and confidences[i] > 60]

            # Check spelling and highlight misspelled words
            draw = ImageDraw.Draw(self.original_image)
            misspelled_words = []

            for i in valid_indices:
                word = words[i]
                # Skip words that are all digits or very short
                if word.isdigit() or len(word) < 2:
                    continue

                # Check spelling
                if word.lower() not in self.spell:
                    # This word is misspelled
                    misspelled_words.append(word)

                    # Get bounding box coordinates
                    left = lefts[i]
                    top = tops[i]
                    right = left + widths[i]
                    bottom = top + heights[i]

                    # Draw rectangle around misspelled word
                    draw.rectangle([left, top, right, bottom],
                                   outline="red", width=2)

            # Display the processed image
            self.display_image(self.original_image)

            # Show the extracted text with misspelled words highlighted
            self.text_display.delete(1.0, tk.END)
            for i, word in enumerate(words):
                if word.strip():  # Only process non-empty words
                    if word in misspelled_words:
                        # Highlight misspelled words in red
                        self.text_display.insert(tk.END, word + " ", "misspelled")
                    else:
                        self.text_display.insert(tk.END, word + " ")

            # Configure the misspelled tag
            self.text_display.tag_config("misspelled", foreground="red")

            # Show summary
            messagebox.showinfo("Processing Complete",
                                f"Found {len(misspelled_words)} misspelled words")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def save_result(self):
        if not self.original_image:
            messagebox.showerror("Error", "No processed image to save")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if file_path:
            self.original_image.save(file_path)
            messagebox.showinfo("Success", "Image saved successfully")


if __name__ == "__main__":
    root = tk.Tk()
    app = OCRSpellCheckApp(root)
    root.mainloop()