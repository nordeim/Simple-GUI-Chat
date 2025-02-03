import sys
import json
import yaml
import os
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextBrowser, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QMenuBar, QMenu, QFileDialog, QMessageBox,
    QDialog, QFormLayout, QLabel, QSlider,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QAction

class AIChatApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Modern AI Chat App")
        self.setGeometry(100, 100, 800, 600)

        self.chat_log = [] # Initialize chat log to store messages
        self.config = self.load_config() # Load API configuration from YAML
        if not self.config:
            self.show_config_dialog() # If config is missing, show config dialog

        self.init_ui() # Initialize user interface elements

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
        self.chat_browser.setOpenExternalLinks(True) # Make links clickable
        self.chat_browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) # Enable custom context menu
        self.chat_browser.customContextMenuRequested.connect(self.show_chat_context_menu) # Connect to context menu function

        # --- Input Area ---
        self.input_box = QLineEdit(self)
        self.input_box.setPlaceholderText("Type your message...")
        self.input_box.returnPressed.connect(self.send_message) # Send message on Enter key
        self.input_box.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) # Input context menu
        self.input_box.customContextMenuRequested.connect(self.show_input_context_menu) # Connect to input context menu function

        self.attach_button = QPushButton("Attach File", self)
        self.attach_button.clicked.connect(self.attach_file)
        self.emojis_button = QPushButton("Emojis", self) # Emoji functionality can be added here
        self.emojis_button.setEnabled(False) # Disabled for now, can be implemented later
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
                    self.chat_log = data.get('chat_log', []) # Load chat log from JSON
                    self.chat_browser.clear() # Clear current chat display
                    for entry in self.chat_log: # Re-display each message from chat log
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
            self.config = config # Update current config
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
        temperature_slider.setRange(0, 100) # Range 0-100 for 0.0 to 1.0
        temperature_slider.setValue(int((self.config.get('Temperature', 0.5) if self.config else 0.5) * 100)) # Default 0.5
        temperature_label = QLabel(str(temperature_slider.value() / 100.0)) # Label to display current temp value
        temperature_slider.valueChanged.connect(lambda value: temperature_label.setText(str(value / 100.0))) # Update label on slider change

        form_layout.addRow("API URL:", api_url_input)
        form_layout.addRow("API Key:", api_key_input)
        form_layout.addRow("Model:", model_input)
        form_layout.addRow("System Prompt:", system_prompt_input)
        form_layout.addRow("Temperature:", temperature_slider)
        form_layout.addRow("", temperature_label) # Empty label row for temperature value display

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(lambda: self.save_config(api_url_input.text(), api_key_input.text(), model_input.text(), system_prompt_input.text(), temperature_slider.value() / 100.0))
        buttons.accepted.connect(dialog.accept) # Close dialog on save
        buttons.rejected.connect(dialog.reject)

        form_layout.addRow(buttons)
        dialog.setLayout(form_layout)

        dialog.exec() # Execute the dialog

    # --- File Attachment ---
    def attach_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Attach File", "", "All Files (*)")
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    content = file.readlines()[:5] # Read first 5 lines for preview
                    preview = ''.join(content)
                self.display_file_attachment(file_name, preview)
                self.input_box.setProperty("attached_file_content", open(file_name, 'r').read()) # Store full file content
                self.input_box.setProperty("attached_file_name", file_name) # Store file name
            except Exception as e:
                QMessageBox.warning(self, "File Error", f"Could not read file: {e}")

    def display_file_attachment(self, file_name, preview):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        formatted_message = (
            f"<div style='text-align: right; background-color: lightyellow; padding: 5px; border-radius: 10px;'>"
            f"<small>[{timestamp}]</small> <b>You attached: {os.path.basename(file_name)}</b><br>" # Just show filename
            f"<pre style='white-space: pre-wrap; font-family: monospace;'>{preview}</pre></div>" # Use <pre> for preview
        )
        self.chat_browser.append(formatted_message)

    # --- Sending and Displaying Messages ---
    def send_message(self):
        user_input = self.input_box.text()
        attached_file_content = self.input_box.property("attached_file_content")
        attached_file_name = self.input_box.property("attached_file_name")

        if not user_input and not attached_file_content: # Prevent sending empty messages without attachment
            return

        full_message_content = user_input
        if attached_file_content:
            full_message_content += f"\n\n[Attached File: {os.path.basename(attached_file_name)}]\n{attached_file_content}"

        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.display_message("You", user_input, timestamp, is_user=True, file_attached=attached_file_name is not None) # Display user message

        # Add user message to chat log
        self.chat_log.append(["You", full_message_content, timestamp])

        self.input_box.clear() # Clear input box after sending
        self.input_box.setProperty("attached_file_content", None) # Clear attached file content
        self.input_box.setProperty("attached_file_name", None) # Clear attached file name


        # Call API and handle response
        self.call_api(full_message_content)

    def display_message(self, sender, message, timestamp, is_user=False, file_attached=False):
        alignment = "right" if is_user else "left"
        background_color = "lightgreen" if is_user else "lightblue"
        sender_display = "You" if is_user else "AI" # Consistent sender display

        formatted_message = (
            f"<div style='text-align: {alignment}; background-color: {background_color}; padding: 5px; border-radius: 10px;'>"
            f"<small>[{timestamp}]</small> <b>{sender_display}:</b><br>"
            f"<div style='white-space: pre-wrap; word-wrap: break-word;'>{message}</div></div>" # pre-wrap and word-wrap for text formatting
        )
        self.chat_browser.append(formatted_message)

    # --- API Call Function ---
    def call_api(self, prompt):
        if not self.config:
            QMessageBox.warning(self, "API Error", "API configuration is missing. Please configure API settings.")
            return

        api_url = self.config.get('API_Url')
        api_key = self.config.get('API_Key')
        model = self.config.get('Model')
        system_prompt = self.config.get('System_Prompt')
        temperature = self.config.get('Temperature')

        headers = {
            'Authorization': f'Bearer {api_key}', # Assuming Bearer token auth
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
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            ai_response_content = response.json()['choices'][0]['message']['content'] # Adjust based on actual API response format
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            self.display_message("AI", ai_response_content, timestamp)
            self.chat_log.append(["AI", ai_response_content, timestamp]) # Add AI response to chat log
        except requests.exceptions.RequestException as e:
            error_message = f"API request failed: {e}"
            QMessageBox.critical(self, "API Error", error_message)
            self.display_message("AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")) # Display error in chat too
            self.chat_log.append(["AI", f"Error: {error_message}", QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")]) # Log error response


if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_app = AIChatApp()
    chat_app.show()
    sys.exit(app.exec())
