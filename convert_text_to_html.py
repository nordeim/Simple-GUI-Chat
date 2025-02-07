import sys
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QPushButton, QFileDialog, QWidget
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt
import html

class WhatsAppFormatter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Formatter")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.text_display = QTextEdit(self)
        self.text_display.setReadOnly(True)
        self.layout.addWidget(self.text_display)

        self.load_button = QPushButton("Load File", self)
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)

        self.export_button = QPushButton("Export as HTML", self)
        self.export_button.clicked.connect(self.export_html)
        self.layout.addWidget(self.export_button)

        self.css_style = """
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #e5ddd5;
                color: #000;
                padding: 20px;
            }
            .message {
                background-color: #dcf8c6;
                border-radius: 10px;
                padding: 10px;
                margin: 5px 0;
                max-width: 70%;
                word-wrap: break-word;
            }
            .bold { font-weight: bold; }
            .italic { font-style: italic; }
            .underline { text-decoration: underline; }
            .strikethrough { text-decoration: line-through; }
            .emoji { font-size: 1.2em; }
        """

    def load_file(self):
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Text Files (*.txt);;JSON Files (*.json)", options=options)
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:  # Ensure UTF-8 encoding
                if file_path.endswith(".json"):
                    data = json.load(file)
                    content = data.get("chat_log", [])  # Extract chat log
                else:
                    content = file.read()

            self.render_content(content, file_path.endswith(".json"))
        except Exception as e:
            self.text_display.setText(f"Error loading file: {str(e)}")


    def render_content(self, content, is_json):
        self.text_display.clear()
        cursor = self.text_display.textCursor()

        if is_json:
            for entry in content:
                sender, message, timestamp = entry
                formatted_message = self.format_whatsapp_text(message)
                html_content = f"<div class='message'><p><b>{html.escape(sender)}</b> ({html.escape(timestamp)})</p><p>{formatted_message}</p></div>" # Escape sender and timestamp
                cursor.insertHtml(html_content)
                cursor.insertBlock()  # Add block separator for JSON entries

        else:
            formatted_message = self.format_whatsapp_text(content)
            html_content = f"<div class='message'><p>{formatted_message}</p></div>"
            cursor.insertHtml(html_content)


    def format_whatsapp_text(self, text):
        # 1. Handle newlines *BEFORE* escaping
        text = text.replace("\\n", "<br>")

        # 2. Handle emojis (encode/decode for surrogate pairs)
        text = text.encode('utf-16', 'surrogatepass').decode('utf-16')

        # 3. Escape HTML entities (including quotes)
        text = html.escape(text)

        # 4. Apply WhatsApp-style formatting tags
        text = self.apply_whatsapp_tags(text)
        return text

    def apply_whatsapp_tags(self, text):
        # Simplified placeholder method (robust and readable)
        text = text.replace("*", "###BOLD###")
        text = text.replace("###BOLD###", "<b>", 1)
        text = text.replace("###BOLD###", "</b>", 1)
        while "###BOLD###" in text:
            text = text.replace("###BOLD###", "<b>", 1)
            text = text.replace("###BOLD###", "</b>", 1)
        text = text.replace("<b></b>", "")

        text = text.replace("_", "###ITALIC###")
        text = text.replace("###ITALIC###", "<i>", 1)
        text = text.replace("###ITALIC###", "</i>", 1)
        while "###ITALIC###" in text:
            text = text.replace("###ITALIC###", "<i>", 1)
            text = text.replace("###ITALIC###", "</i>", 1)
        text = text.replace("<i></i>", "")

        text = text.replace("~", "###STRIKE###")
        text = text.replace("###STRIKE###", "<s>", 1)
        text = text.replace("###STRIKE###", "</s>", 1)
        while "###STRIKE###" in text:
            text = text.replace("###STRIKE###", "<s>", 1)
            text = text.replace("###STRIKE###", "</s>", 1)
        text = text.replace("<s></s>", "")

        return text


    def export_html(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Save HTML File", "", "HTML Files (*.html)", options=options)
        if not file_path:
            return

        try:
            # Get the *current* HTML content from the QTextEdit
            html_content = self.text_display.toHtml()

            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>WhatsApp Formatter Output</title>
                <style>{self.css_style}</style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            with open(file_path, "w", encoding="utf-8") as file:  # Ensure UTF-8 encoding
                file.write(full_html)
            self.text_display.append("<p><i>File exported successfully!</i></p>")  # Status message - Using HTML for italics
        except Exception as e:
            self.text_display.append(f"<p>Error exporting file: {str(e)}</p>")  # Error message - Using HTML

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppFormatter()
    window.show()
    sys.exit(app.exec())
