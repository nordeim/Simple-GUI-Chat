import sys
import json
import yaml
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextBrowser, QTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QMenuBar, QMenu, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLabel, QSlider, QComboBox,
    QDialogButtonBox, QGridLayout,
    QToolButton, QLineEdit
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QAction, QTextCursor, QFont
from urllib.parse import urlparse
from openai import OpenAI
import html  # Import the html module


class EmojiPickerDialog(QDialog):
    def __init__(self, parent=None, input_box=None):
        super().__init__(parent)
        self.setWindowTitle("Emoji Picker")
        self.input_box = input_box
        self.emoji_buttons = []
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        emojis = [
            "😀", "😂", "😊", "👍", "❤️",
            "🎉", "🤔", "🚀", "🌟", "💡",
            "😞", "😡", "😴", "☕", "🍕",
            "🐶", "🐱", "🐰", "🌸", "🌈"
        ]
        row, col = 0, 0
        for emoji in emojis:
            button = QToolButton()
            button.setText(emoji)
            button.setFont(QFont("Arial", 14))
            button.clicked.connect(lambda checked, emoji=emoji: self.emoji_selected(emoji))
            layout.addWidget(button, row, col)
            self.emoji_buttons.append(button)
            col += 1
            if col > 4:
                col = 0
                row += 1

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.reject)
        layout.addWidget(close_button, row + 1, 0, 1, col + 1)

        self.setLayout(layout)

    def emoji_selected(self, emoji):
        if self.input_box:
            current_text = self.input_box.toPlainText()
            self.input_box.setText(current_text + emoji)
        self.accept()


class AIChatApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Modern AI Chat App")
        self.setGeometry(100, 100, 800, 600)

        self.chat_log = []
        self.config = self.load_config()
        if not self.config:
            self.show_config_dialog()

        self.emoji_dialog = EmojiPickerDialog(self, None)
        self.attached_file_content = None
        self.attached_file_name = None
        self.init_ui()
        self.emoji_dialog.input_box = self.input_box

        self.openai_client = None
        self.init_openai_client()  # Initialize OpenAI client here

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
                    .user-message {
                        background-color: lightgreen;
                        text-align: right;
                    }
                    .ai-message {
                        background-color: lightblue;
                        text-align: left;
                    }
                    .error-message {
                        background-color: lightcoral;
                        text-align: left;
                    }
                    .bold { font-weight: bold; }
                    .italic { font-style: italic; }
                    .underline { text-decoration: underline; }
                    .strikethrough { text-decoration: line-through; }
                    .emoji { font-size: 1.2em; }
                """

    def init_openai_client(self):
        if self.config and self.config.get('API_Key') and self.config.get('API_Url'):
            self.openai_client = OpenAI(
                api_key=self.config['API_Key'],
                base_url=self.config['API_Url']
            )
        else:
            self.openai_client = None

    def init_ui(self):
        # --- Menu Bar ---
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        settings_menu = menu_bar.addMenu("Settings")

        export_action = QAction("Export Chat History", self)
        export_action.triggered.connect(self.export_chat_history)
        file_menu.addAction(export_action)

        import_action = QAction("Import Chat History", self)
        import_action.triggered.connect(self.import_chat_history)
        file_menu.addAction(import_action)

        config_action = QAction("API Configuration", self)
        config_action.triggered.connect(self.show_config_dialog)
        settings_menu.addAction(config_action)

        # --- Chat Display Area ---
        self.chat_browser = QTextBrowser(self)
        self.chat_browser.setOpenExternalLinks(True)
        self.chat_browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_browser.customContextMenuRequested.connect(self.show_chat_context_menu)

        # --- Input Area ---
        self.input_box = QTextEdit(self)
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.setMaximumHeight(5 * self.input_box.fontMetrics().height())
        self.input_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.input_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.input_box.customContextMenuRequested.connect(self.show_input_context_menu)

        self.attach_button = QPushButton("Attach File", self)
        self.attach_button.clicked.connect(self.attach_file)
        self.emojis_button = QPushButton("Emojis", self)
        self.emojis_button.clicked.connect(self.show_emoji_picker)
        self.send_button = QPushButton("Send", self)
        self.send_button.clicked.connect(self.send_message)

        # Input layout
        input_hbox = QHBoxLayout()
        input_hbox.addWidget(self.input_box)
        input_hbox.addWidget(self.attach_button)
        input_hbox.addWidget(self.emojis_button)
        input_hbox.addWidget(self.send_button)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.chat_browser)
        main_layout.addLayout(input_hbox)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def show_emoji_picker(self):
        self.emoji_dialog.show()

    # --- Context Menus for Copy/Paste ---
    def show_chat_context_menu(self, position):
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.chat_browser.copy)
        menu.popup(self.chat_browser.viewport().mapToGlobal(position))

    def show_input_context_menu(self, position):
        menu = QMenu(self)
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.input_box.copy)
        paste_action = menu.addAction("Paste")
        paste_action.triggered.connect(self.input_box.paste)
        cut_action = menu.addAction("Cut")
        cut_action.triggered.connect(self.input_box.cut)
        select_all_action = menu.addAction("Select All")
        select_all_action.triggered.connect(self.input_box.selectAll)
        menu.popup(self.input_box.mapToGlobal(position))

    # --- File Menu Actions ---
    def export_chat_history(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Chat", "", "HTML Files (*.html)")
        if file_name:
            try:
                html_content = self.generate_html_chat_log()
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
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                QMessageBox.information(self, "Export Successful", "Chat history exported to HTML.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export chat history: {e}")

    def generate_html_chat_log(self):
        html_log = ""
        for sender, message, timestamp in self.chat_log:
            formatted_message = self.format_whatsapp_text(message)
            if sender == "You":
                html_log += f"<div class='message user-message'><p>{html.escape(timestamp)} <b>{html.escape(sender)}:</b></p><p>{formatted_message}</p></div>"
            elif sender == "AI":
                html_log += f"<div class='message ai-message'><p>{html.escape(timestamp)} <b>{html.escape(sender)}:</b></p><p>{formatted_message}</p></div>"
            else:  # Error messages
                html_log += f"<div class='message error-message'><p>{html.escape(timestamp)} <b>{html.escape(sender)}:</b></p><p>{formatted_message}</p></div>"
        return html_log

    def import_chat_history(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import Chat", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    data = json.load(f)
                    self.chat_log = data.get('chat_log', [])
                    self.chat_browser.clear()
                    for entry in self.chat_log:
                        sender, message, timestamp = entry
                        self.display_message(sender, message, timestamp)  # Use display_message
                QMessageBox.information(self, "Import Successful", "Chat history imported from JSON.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Could not import chat history: {e}")

    # --- Settings Menu Actions and Configuration ---
    def load_config(self):
        try:
            with open('api_configuration.yaml', 'r') as file:
                config = yaml.safe_load(file)
                if 'Available_Models' not in config:
                    config['Available_Models'] = ["gpt-4o-mini", "o3-mini", "deepseek/deepseek-chat",
                                                  "deepseek/deepseek-r1", "deepseek-reasoner", "deepseek-chat"]
                return config
        except FileNotFoundError:
            return None
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "Configuration Error", f"Error reading configuration file: {e}")
            return None

    def save_config(self, api_url, api_key, model, system_prompt, temperature):
        # --- Configuration Validation ---
        if not api_url.strip():
            QMessageBox.warning(self, "Configuration Error", "API URL cannot be empty.")
            return False
        parsed_url = urlparse(api_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            QMessageBox.warning(self, "Configuration Error", "Invalid API URL format.")
            return False
        if not api_key.strip():
            QMessageBox.warning(self, "Configuration Error", "API Key cannot be empty.")
            return False
        temperature_val = float(temperature)
        if not 0.0 <= temperature_val <= 2.0:
            QMessageBox.warning(self, "Configuration Error", "Temperature must be between 0.0 and 2.0.")
            return False
        valid_models = ["gpt-4o-mini", "o3-mini", "deepseek/deepseek-chat", "deepseek/deepseek-r1", "deepseek-reasoner",
                        "deepseek-chat"]
        if model.strip() and model.strip() not in valid_models:
            QMessageBox.warning(self, "Configuration Error",
                                f"Model '{model}' is not in the list of suggested models. Please ensure it's a valid model for your API endpoint.")

        config = {
            'API_Url': api_url,
            'API_Key': api_key,
            'Model': model,
            'System_Prompt': system_prompt,
            'Temperature': temperature_val
        }
        try:
            with open('api_configuration.yaml', 'w') as file:
                yaml.dump(config, file)
            self.config = config
            self.init_openai_client()
            QMessageBox.information(self, "Configuration Saved", "API configuration saved successfully.")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Could not save configuration: {e}")
            return False

    def show_config_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("API Configuration")
        form_layout = QFormLayout()

        api_url_input = QLineEdit(self.config.get('API_Url', '') if self.config else '')
        api_key_input = QLineEdit(self.config.get('API_Key', '') if self.config else '')

        self.model_combo = QComboBox(self)
        models = ["gpt-4o-mini", "o3-mini", "deepseek/deepseek-chat", "deepseek/deepseek-r1", "deepseek-reasoner",
                  "deepseek-chat"]
        self.model_combo.addItems(models)
        current_model = self.config.get('Model', 'gpt-4o-mini') if self.config else 'gpt-4o-mini'
        self.model_combo.setCurrentText(current_model)
        self.model_combo.setEditable(True)

        system_prompt_input = QLineEdit(self.config.get('System_Prompt', '') if self.config else '')
        temperature_slider = QSlider(Qt.Orientation.Horizontal)
        temperature_slider.setRange(0, 200)
        temperature_slider.setValue(
            int((self.config.get('Temperature', 0.5) if self.config else 0.5) * 100))
        temperature_label = QLabel(f"Temperature ({temperature_slider.value() / 100.0:.2f})")
        temperature_slider.valueChanged.connect(
            lambda value: temperature_label.setText(f"Temperature ({(value / 100.0):.2f})"))

        form_layout.addRow("API URL:", api_url_input)
        form_layout.addRow("API Key:", api_key_input)
        form_layout.addRow("Model:", self.model_combo)
        form_layout.addRow("System Prompt:", system_prompt_input)
        form_layout.addRow("Temperature:", temperature_slider)
        form_layout.addRow("", temperature_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.save_config(api_url_input.text(), api_key_input.text(),
                                                          self.model_combo.currentText(), system_prompt_input.text(),
                                                          temperature_slider.value() / 100.0))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        form_layout.addRow(buttons)
        dialog.setLayout(form_layout)

        dialog.exec()

    # --- File Attachment ---
    def attach_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Attach File", "", "All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    content = file.read()
                    preview_length = 500
                    preview = content[:preview_length]
                    if len(content) > preview_length:
                        preview += "...\n[Preview limited to first 500 characters]"
                    self.attached_file_content = content
                    self.attached_file_name = file_name

                self.display_file_attachment(file_name, preview)

            except Exception as e:
                QMessageBox.warning(self, "File Error", f"Could not read file: {e}")

    def display_file_attachment(self, file_name, preview):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        formatted_message = (
            f"<div style='text-align: right; background-color: lightyellow; padding: 5px; border-radius: 10px;'>"
            f"<small>[{timestamp}]</small> <b>You attached: {os.path.basename(file_name)}</b><br>"
            f"<pre style='white-space: pre-wrap; font-family: monospace;'>{preview}</pre></div>"
        )
        self.chat_browser.append(formatted_message)

    # --- Sending and Displaying Messages ---
    def send_message(self):
        user_input = self.input_box.toPlainText()
        full_message_content = user_input

        if self.attached_file_content:
            full_message_content += f"\n\n[Attached File: {os.path.basename(self.attached_file_name)}]\n{self.attached_file_content}"

        if not user_input and not self.attached_file_content:
            return

        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.display_message("You", user_input, timestamp, is_user=True,
                             file_attached=self.attached_file_name is not None)

        self.chat_log.append(["You", full_message_content, timestamp])

        self.input_box.clear()
        self.attached_file_content = None
        self.attached_file_name = None

        # Call API and handle response
        self.call_api(full_message_content)

    def display_message(self, sender, message, timestamp, is_user=False, file_attached=False, is_error=False):
        formatted_message = self.format_whatsapp_text(message)
        sender_display = "You" if is_user else "AI"
        if is_user:
            html_content = f"<div class='message user-message'><p>{html.escape(timestamp)} <b>{html.escape(sender_display)}:</b></p><p>{formatted_message}</p></div>"
        elif is_error:
            html_content = f"<div class='message error-message'><p>{html.escape(timestamp)} <b>{html.escape(sender_display)}:</b></p><p>{formatted_message}</p></div>"
        else:
            html_content = f"<div class='message ai-message'><p>{html.escape(timestamp)} <b>{html.escape(sender_display)}:</b></p><p>{formatted_message}</p></div>"

        cursor = self.chat_browser.textCursor()
        cursor.insertHtml(html_content)
        cursor.insertBlock()
        self.chat_browser.moveCursor(QTextCursor.MoveOperation.End) # Scroll to the end of chat

    def format_whatsapp_text(self, text):
        # 1. Escape HTML entities (including quotes)
        text = html.escape(text)

        # 2. Handle newlines *AFTER* escaping
        text = text.replace("\n", "<br>")

        # 3. Handle emojis (encode/decode for surrogate pairs)
        text = text.encode('utf-16', 'surrogatepass').decode('utf-16')

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

    # --- API Call Function using OpenAI library ---
    def call_api(self, prompt):
        if not self.config:
            QMessageBox.warning(self, "API Error",
                                "API configuration is missing. Please configure API settings.")
            return
        if not self.openai_client:
            QMessageBox.warning(self, "API Error", "OpenAI client not initialized. Check API configuration.")
            return

        model = self.config.get('Model')
        system_prompt = self.config.get('System_Prompt')
        temperature = float(self.config.get('Temperature'))

        try:
            completion = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            ai_response_content = completion.choices[0].message.content
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            self.display_message("AI", ai_response_content, timestamp)
            self.chat_log.append(["AI", ai_response_content, timestamp])

        except Exception as e:
            error_message = f"API request failed: {e}"
            self.display_message("AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
                                 is_error=True)
            self.chat_log.append(
                ["AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = AIChatApp()
    chat_app.show()
    sys.exit(app.exec())
