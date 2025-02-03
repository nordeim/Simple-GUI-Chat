import sys
import json
import yaml
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextBrowser, QTextEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QMenuBar, QMenu, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLabel, QSlider, QComboBox, # Added QComboBox
    QDialogButtonBox, QGridLayout,
    QToolButton, QLineEdit # for emoji buttons, and QLineEdit for config validation
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QAction, QTextCursor, QFont
from urllib.parse import urlparse # For basic URL validation
from openai import OpenAI # Import OpenAI library

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
        self.attached_file_content = None # Instance variable for attached file content
        self.attached_file_name = None # Instance variable for attached file name
        self.init_ui()
        self.emoji_dialog.input_box = self.input_box

        self.openai_client = None # Initialize OpenAI client here, configure later

    def init_openai_client(self):
        if self.config and self.config.get('API_Key') and self.config.get('API_Url'):
            self.openai_client = OpenAI(
                api_key=self.config['API_Key'],
                base_url=self.config['API_Url']
            )
        else:
            self.openai_client = None # Ensure client is None if config is missing or incomplete


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
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Chat", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'w') as f:
                    json.dump({'chat_log': self.chat_log}, f, indent=4)
                QMessageBox.information(self, "Export Successful", "Chat history exported to JSON.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export chat history: {e}")

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
                        self.display_message(sender, message, timestamp)
                QMessageBox.information(self, "Import Successful", "Chat history imported from JSON.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Could not import chat history: {e}")

    # --- Settings Menu Actions and Configuration ---
    def load_config(self):
        try:
            with open('api_configuration.yaml', 'r') as file:
                return yaml.safe_load(file)
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
        if not all([parsed_url.scheme, parsed_url.netloc]): # Basic URL validation
            QMessageBox.warning(self, "Configuration Error", "Invalid API URL format.")
            return False
        if not api_key.strip():
            QMessageBox.warning(self, "Configuration Error", "API Key cannot be empty.")
            return False
        # --- End of Validation ---

        config = {
            'API_Url': api_url,
            'API_Key': api_key,
            'Model': model,
            'System_Prompt': system_prompt,
            'Temperature': temperature
        }
        try:
            with open('api_configuration.yaml', 'w') as file:
                yaml.dump(config, file)
            self.config = config
            self.init_openai_client() # Re-initialize OpenAI client with new config
            QMessageBox.information(self, "Configuration Saved", "API configuration saved successfully.")
            return True # Indicate successful save
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Could not save configuration: {e}")
            return False # Indicate save failure


    def show_config_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("API Configuration")
        form_layout = QFormLayout()

        api_url_input = QLineEdit(self.config.get('API_Url', '') if self.config else '')
        api_key_input = QLineEdit(self.config.get('API_Key', '')if self.config else '')

        self.model_combo = QComboBox(self) # Use QComboBox for model selection
        models = ["gpt-3.5-turbo", "gpt-4", "gpt-3.5-turbo-16k", "gpt-4-32k"] # Common models, extend as needed
        self.model_combo.addItems(models)
        current_model = self.config.get('Model', 'gpt-3.5-turbo') if self.config else 'gpt-3.5-turbo'
        self.model_combo.setCurrentText(current_model)
        self.model_combo.setEditable(True) # Allow manual input as well

        system_prompt_input = QLineEdit(self.config.get('System_Prompt', '')if self.config else '')
        temperature_slider = QSlider(Qt.Orientation.Horizontal)
        temperature_slider.setRange(0, 100)
        temperature_slider.setValue(int((self.config.get('Temperature', 0.5) if self.config else 0.5) * 100))
        temperature_label = QLabel(f"Temperature ({temperature_slider.value() / 100.0:.1f})") # Initial label format
        temperature_slider.valueChanged.connect(lambda value: temperature_label.setText(f"Temperature ({(value / 100.0):.1f})")) # Updated label format

        form_layout.addRow("API URL:", api_url_input)
        form_layout.addRow("API Key:", api_key_input)
        form_layout.addRow("Model:", self.model_combo) # Use QComboBox
        form_layout.addRow("System Prompt:", system_prompt_input)
        form_layout.addRow("Temperature:", temperature_slider)
        form_layout.addRow("", temperature_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.save_config(api_url_input.text(), api_key_input.text(), self.model_combo.currentText(), system_prompt_input.text(), temperature_slider.value() / 100.0)) # Get model from QComboBox
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
                    content = file.readlines()[:5]
                    preview = ''.join(content)
                    self.attached_file_content = file.read() # Store full content in instance variable
                    self.attached_file_name = file_name   # Store file name in instance variable

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
        self.display_message("You", user_input, timestamp, is_user=True, file_attached=self.attached_file_name is not None)

        self.chat_log.append(["You", full_message_content, timestamp])

        self.input_box.clear()
        self.attached_file_content = None # Clear attached file content and name
        self.attached_file_name = None


        # Call API and handle response
        self.call_api(full_message_content)

    def display_message(self, sender, message, timestamp, is_user=False, file_attached=False, is_error=False): # Added is_error parameter
        alignment = "right" if is_user else "left"
        background_color = "lightgreen" if is_user else "lightblue"
        sender_display = "You" if is_user else "AI"
        if is_error: # Error message styling
            background_color = "lightcoral" # Distinct color for errors

        formatted_message = (
            f"<div style='text-align: {alignment}; background-color: {background_color}; padding: 5px; border-radius: 10px;'>"
            f"<small>[{timestamp}]</small> <b>{sender_display}:</b><br>"
            f"<div style='white-space: pre-wrap; word-wrap: break-word; text-align: left;'>{message}</div></div>"
        )
        self.chat_browser.append(formatted_message)

    # --- API Call Function using OpenAI library ---
    def call_api(self, prompt):
        if not self.config:
            QMessageBox.warning(self, "API Error", "API configuration is missing. Please configure API settings.")
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

        except Exception as e: # Catch broad exceptions for API errors using openai library
            error_message = f"API request failed: {e}"
            QMessageBox.critical(self, "API Error", error_message)
            self.display_message("AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"), is_error=True) # Use is_error=True for error styling
            self.chat_log.append(["AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = AIChatApp()
    chat_app.show()
    sys.exit(app.exec())
