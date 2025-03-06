#!/usr/bin/python
# -*- coding: utf-8 -*-
import pathlib
import uuid
import re
import io
import pathlib
from typing import Optional, List, Tuple

import langdetect
from ebooklib import epub
from tkinter import Tk, Label, Entry, Button, filedialog, messagebox, StringVar
from tkinter.ttk import Combobox
from PIL import Image


class Txt2Epub:
    @staticmethod
    def create_epub(
        input_file: pathlib.Path,
        output_file: Optional[pathlib.Path] = None,
        book_identifier: Optional[str] = None,
        book_title: Optional[str] = None,
        book_author: Optional[str] = None,
        book_language: Optional[str] = None,
        book_cover: Optional[pathlib.Path] = None,
        chapter_regex: Optional[str] = None,
    ):
        # generate fields if not specified
        book_identifier = book_identifier or str(uuid.uuid4())
        book_title = book_title or input_file.stem
        book_author = book_author or "Unknown"

        # read text from file
        with input_file.open("r", encoding="utf-8") as txt_file:
            book_text = txt_file.read()

            # detect book language if not specified
            try:
                book_language = book_language or langdetect.detect(book_text)
            except langdetect.lang_detect_exception.LangDetectException:
                book_language = "en"

        # split text into chapters using regex if provided, otherwise use default
        if chapter_regex:
            # Modification: Use finditer to capture both chapter titles
            chapters = []
            chapter_titles = []
            
            # Find all positions of chapter titles
            matches = list(re.finditer(chapter_regex, book_text))
            
            if matches:
                # Process each chapter
                for i, match in enumerate(matches):
                    start = match.start()
                    # Extract chapter title (remove trailing newline character)
                    title = match.group().rstrip()
                    chapter_titles.append(title)
                    
                    # Determine the end position of the current chapter
                    if i < len(matches) - 1:
                        end = matches[i + 1].start()
                    else:
                        end = len(book_text)
                    
                    # Chapter content starts after the title
                    content = book_text[match.end():end].strip()
                    chapters.append((title, content))
            else:
                # If no chapters are found, use the entire text as a single chapter
                chapters = [("Untitled", book_text)]
        else:
            # Use the default splitting method with three blank lines
            parts = book_text.split("\n\n\n")
            chapters = []
            
            for part in parts:
                if not part.strip():
                    continue
                
                lines = part.split("\n", 1)
                if len(lines) > 1:
                    title = lines[0].strip()
                    content = lines[1].strip()
                else:
                    title = "Untitled"
                    content = lines[0].strip()
                    
                chapters.append((title, content))

        # convert cover image to JPEG
        book_cover_jpeg = None
        if book_cover is not None and book_cover != "":
            book_cover_jpeg = convert_image_to_jpeg(book_cover)

        # create new EPUB book
        book = epub.EpubBook()

        # set book metadata
        book.set_identifier(book_identifier)
        book.set_title(book_title)
        book.add_author(book_author)
        book.set_language(book_language)
        if book_cover_jpeg:
            book.set_cover("cover.jpg", book_cover_jpeg)

        # create chapters
        spine: list[str | epub.EpubHtml] = ["nav"]
        toc = []
        for chapter_id, (chapter_title, chapter_content) in enumerate(chapters):
            # Skip empty chapters
            if not chapter_content.strip():
                continue

            # Create chapter HTML
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name="chap_{:02d}.xhtml".format(chapter_id + 1),
                lang=book_language,
            )
            # Sử dụng định dạng chuỗi thông thường thay vì f-string
            chapter.content = "<h1>{0}</h1><p>{1}</p>".format(
                chapter_title,
                chapter_content.replace('\n', '</p><p>')
            )

            # Add chapter to the book and TOC
            book.add_item(chapter)
            spine.append(chapter)
            toc.append(epub.Link(chapter.file_name, chapter.title, chapter.id))

        # Update book spine and TOC
        book.spine = spine
        book.toc = toc

        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Generate new file path if not specified
        if output_file is None:
            output_file = input_file.with_suffix(".epub")

        # Create EPUB file
        epub.write_epub(output_file, book)


class Txt2EpubGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TXT to EPUB Converter")

        # Input file
        Label(root, text="Input TXT File:").grid(row=0, column=0, padx=10, pady=10)
        self.input_file_entry = Entry(root, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=10, pady=10)
        Button(root, text="Browse", command=self.browse_input_file).grid(row=0, column=2, padx=10, pady=10)

        # Output file
        Label(root, text="Output EPUB File:").grid(row=1, column=0, padx=10, pady=10)
        self.output_file_entry = Entry(root, width=50)
        self.output_file_entry.grid(row=1, column=1, padx=10, pady=10)
        Button(root, text="Browse", command=self.browse_output_file).grid(row=1, column=2, padx=10, pady=10)

        # Book Title
        Label(root, text="Book Title:").grid(row=2, column=0, padx=10, pady=10)
        self.book_title_entry = Entry(root, width=50)
        self.book_title_entry.grid(row=2, column=1, padx=10, pady=10)

        # Book Author
        Label(root, text="Book Author:").grid(row=3, column=0, padx=10, pady=10)
        self.book_author_entry = Entry(root, width=50)
        self.book_author_entry.grid(row=3, column=1, padx=10, pady=10)

        # Book Language
        Label(root, text="Book Language:").grid(row=4, column=0, padx=10, pady=10)
        self.book_language_combobox = Combobox(root, values=["en", "fr", "de", "es", "it", "zh", "ja", "ru", "vi"], width=47)
        self.book_language_combobox.grid(row=4, column=1, padx=10, pady=10)
        self.book_language_combobox.set("en")

        # Book Cover
        Label(root, text="Book Cover:").grid(row=5, column=0, padx=10, pady=10)
        self.book_cover_entry = Entry(root, width=50)
        self.book_cover_entry.grid(row=5, column=1, padx=10, pady=10)
        Button(root, text="Browse", command=self.browse_cover_file).grid(row=5, column=2, padx=10, pady=10)

        # Chapter Regex
        Label(root, text="Chapter Regex:").grid(row=6, column=0, padx=10, pady=10)
        self.chapter_regex_entry = Entry(root, width=50)
        self.chapter_regex_entry.grid(row=6, column=1, padx=10, pady=10)
        # Thêm gợi ý cho regex - Sử dụng đúng cú pháp
        Label(root, text="Example: Thứ \\\\d+ chương").grid(row=6, column=2, padx=10, pady=10)

        # Convert Button
        Button(root, text="Convert to EPUB", command=self.convert_to_epub).grid(row=7, column=1, padx=10, pady=20)

    def browse_input_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.input_file_entry.delete(0, 'end')
            self.input_file_entry.insert(0, file_path)

    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".epub", filetypes=[("EPUB Files", "*.epub")])
        if file_path:
            self.output_file_entry.delete(0, 'end')
            self.output_file_entry.insert(0, file_path)

    def browse_cover_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp *.gif")])
        if file_path:
            self.book_cover_entry.delete(0, 'end')
            self.book_cover_entry.insert(0, file_path)

    def convert_to_epub(self):
        input_file = pathlib.Path(self.input_file_entry.get())
        output_file = pathlib.Path(self.output_file_entry.get()) if self.output_file_entry.get() else None
        book_title = self.book_title_entry.get() or None
        book_author = self.book_author_entry.get() or None
        book_language = self.book_language_combobox.get() or None
        book_cover = pathlib.Path(self.book_cover_entry.get()) if self.book_cover_entry.get() else None
        chapter_regex = self.chapter_regex_entry.get() or None

        if not input_file.exists():
            messagebox.showerror("Error", "Input file does not exist!")
            return

        try:
            Txt2Epub.create_epub(
                input_file=input_file,
                output_file=output_file,
                book_title=book_title,
                book_author=book_author,
                book_language=book_language,
                book_cover=book_cover,
                chapter_regex=chapter_regex,
            )
            messagebox.showinfo("Success", "EPUB file created successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


def convert_image_to_jpeg(image_path: pathlib.Path) -> bytes:
    """Converts any image format to JPEG and returns it as binary data."""
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="JPEG", quality=90)
        return image_buffer.getvalue()


if __name__ == "__main__":
    root = Tk()
    app = Txt2EpubGUI(root)
    root.mainloop()