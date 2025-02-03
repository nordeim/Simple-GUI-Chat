import sys
import json
import yaml
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextBrowser, QTextEdit, # Changed from QLineEdit to QTextEdit
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QMenuBar, QMenu, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLabel, QSlider,
    QDialogButtonBox, QGridLayout,
    QToolButton # for emoji buttons
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QAction, QTextCursor, QFont

class EmojiPickerDialog(QDialog):
    def __init__(self, parent=None, input_box=None):
        super().__init__(parent)
        self.setWindowTitle("Emoji Picker")
        self.input_box = input_box # Store reference to input box
        self.emoji_buttons = []
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout(self)
        emojis = [
            "😀", "😂", "😊", "👍", "❤️",
            "🎉", "🤔", "🚀", "🌟", "💡",
            "😞", "😡", "😴", "☕", "🍕",
            "🐶", "🐱", "🐰", "🌸", "🌈"
        ] # Common emojis - can be extended
        row, col = 0, 0
        for emoji in emojis:
            button = QToolButton()
            button.setText(emoji)
            button.setFont(QFont("Arial", 14)) # Make emojis larger
            button.clicked.connect(lambda checked, emoji=emoji: self.emoji_selected(emoji)) # Pass emoji to function
            layout.addWidget(button, row, col)
            self.emoji_buttons.append(button)
            col += 1
            if col > 4: # 5 emojis per row
                col = 0
                row += 1

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.reject) # Close dialog without accepting (just dismiss)
        layout.addWidget(close_button, row + 1, 0, 1, col + 1) # Span all columns

        self.setLayout(layout)

    def emoji_selected(self, emoji):
        if self.input_box:
            current_text = self.input_box.toPlainText() # Get current text from QTextEdit
            self.input_box.setText(current_text + emoji) # Append emoji
        self.accept() # Close dialog


class AIChatApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Modern AI Chat App")
        self.setGeometry(100, 100, 800, 600)

        self.chat_log = []
        self.config = self.load_config()
        if not self.config:
            self.show_config_dialog()

        self.emoji_dialog = EmojiPickerDialog(self, None) # Initialize emoji dialog, input_box will be set later
        self.init_ui()
        self.emoji_dialog.input_box = self.input_box # Now set input_box for emoji dialog after input_box is created


    def init_ui(self):
        # --- Menu Bar ---
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        settings_menu = menu_bar.addMenu("Settings")

        # Export Chat History
        export_action = QAction("Export Chat History", self)
        export_action.triggered.connect(self.export_chat_history)
        file_menu.addAction(export_action)

        # Import Chat History
        import_action = QAction("Import Chat History", self)
        import_action.triggered.connect(self.import_chat_history)
        file_menu.addAction(import_action)

        # API Configuration
        config_action = QAction("API Configuration", self)
        config_action.triggered.connect(self.show_config_dialog)
        settings_menu.addAction(config_action)

        # --- Chat Display Area ---
        self.chat_browser = QTextBrowser(self)
        self.chat_browser.setOpenExternalLinks(True)
        self.chat_browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_browser.customContextMenuRequested.connect(self.show_chat_context_menu)

        # --- Input Area ---
        self.input_box = QTextEdit(self) # Changed to QTextEdit
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.setMaximumHeight(5 * self.input_box.fontMetrics().height()) # Max 5 lines height
        self.input_box.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth) # Enable text wrapping
        self.input_box.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) # Vertical scroll bar when needed
        self.input_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.input_box.customContextMenuRequested.connect(self.show_input_context_menu)


        self.attach_button = QPushButton("Attach File", self)
        self.attach_button.clicked.connect(self.attach_file)
        self.emojis_button = QPushButton("Emojis", self)
        self.emojis_button.clicked.connect(self.show_emoji_picker) # Connect emoji button to show picker
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
        self.emoji_dialog.show() # Show emoji picker dialog


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
            QMessageBox.information(self, "Configuration Saved", "API configuration saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Could not save configuration: {e}")

    def show_config_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("API Configuration")
        form_layout = QFormLayout()

        api_url_input = QLineEdit(self.config.get('API_Url', '') if self.config else '')
        api_key_input = QLineEdit(self.config.get('API_Key', '')if self.config else '')
        model_input = QLineEdit(self.config.get('Model', '')if self.config else '') # Consider dropdown for models
        system_prompt_input = QLineEdit(self.config.get('System_Prompt', '')if self.config else '')
        temperature_slider = QSlider(Qt.Orientation.Horizontal)
        temperature_slider.setRange(0, 100)
        temperature_slider.setValue(int((self.config.get('Temperature', 0.5) if self.config else 0.5) * 100))
        temperature_label = QLabel(str(temperature_slider.value() / 100.0))
        temperature_slider.valueChanged.connect(lambda value: temperature_label.setText(str(value / 100.0)))

        form_layout.addRow("API URL:", api_url_input)
        form_layout.addRow("API Key:", api_key_input)
        form_layout.addRow("Model:", model_input)
        form_layout.addRow("System Prompt:", system_prompt_input)
        form_layout.addRow("Temperature:", temperature_slider)
        form_layout.addRow("", temperature_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.save_config(api_url_input.text(), api_key_input.text(), model_input.text(), system_prompt_input.text(), temperature_slider.value() / 100.0))
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
                self.display_file_attachment(file_name, preview)
                self.input_box.setProperty("attached_file_content", open(file_name, 'r').read())
                self.input_box.setProperty("attached_file_name", file_name)
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
        user_input = self.input_box.toPlainText() # Get text from QTextEdit using toPlainText()
        attached_file_content = self.input_box.property("attached_file_content")
        attached_file_name = self.input_box.property("attached_file_name")

        if not user_input and not attached_file_content:
            return

        full_message_content = user_input
        if attached_file_content:
            full_message_content += f"\n\n[Attached File: {os.path.basename(attached_file_name)}]\n{attached_file_content}"

        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.display_message("You", user_input, timestamp, is_user=True, file_attached=attached_file_name is not None)

        self.chat_log.append(["You", full_message_content, timestamp])

        self.input_box.clear() # clear QTextEdit
        self.input_box.setProperty("attached_file_content", None)
        self.input_box.setProperty("attached_file_name", None)


        # Call API and handle response
        self.call_api(full_message_content)

    def display_message(self, sender, message, timestamp, is_user=False, file_attached=False):
        alignment = "right" if is_user else "left"
        background_color = "lightgreen" if is_user else "lightblue"
        sender_display = "You" if is_user else "AI"

        formatted_message = (
            f"<div style='text-align: {alignment}; background-color: {background_color}; padding: 5px; border-radius: 10px;'>"
            f"<small>[{timestamp}]</small> <b>{sender_display}:</b><br>"
            f"<div style='white-space: pre-wrap; word-wrap: break-word; text-align: left;'>{message}</div></div>" # Added text-align: left here
        )
        self.chat_browser.append(formatted_message)

    # --- API Call Function ---
    def call_api(self, prompt):
        if not self.config:
            QMessageBox.warning(self, "API Error", "API configuration is missing. Please configure API settings.")
            return

        api_url = self.config.get('API_Url') # Using configured API_Url
        api_key = self.config.get('API_Key')
        model = self.config.get('Model')
        system_prompt = self.config.get('System_Prompt')
        temperature = self.config.get('Temperature')

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        try:
            response = requests.post(api_url, headers=headers, json=data) # Using api_url from config
            response.raise_for_status()
            ai_response_content = response.json()['choices'][0]['message']['content']
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            self.display_message("AI", ai_response_content, timestamp)
            self.chat_log.append(["AI", ai_response_content, timestamp])
        except requests.exceptions.RequestException as e:
            error_message = f"API request failed: {e}"
            QMessageBox.critical(self, "API Error", error_message)
            self.display_message("AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"))
            self.chat_log.append(["AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = AIChatApp()
    chat_app.show()
    sys.exit(app.exec())
