# Simple-GUI-Chat
a modern simple AI chat application for OpenAI compatible API

$ pip install PyQt6 pyyaml requests

$ python ai_chat_app.py

design document:
https://chatgpt.com/share/67a0993c-9774-800c-a424-443cbae42ff5

A PyQt6 chat application that

Have a menu for exporting and importing chat history in JSON format.

Have a settings menu to configure API URL, API Key, Model, System Prompt, and Temperature, saving these to a YAML file.

Display the chat in a WhatsApp style, with different styling for user and AI messages, and special styling for file attachments.

Include an input area with buttons for attaching files, emojis, and sending messages.

Implement copy-paste functionality.

Interact with an OpenAI-compatible API, sending user input and attached file content, along with System Prompt and Temperature.

Implementation steps:

Project Setup: Create the basic PyQt6 application window with menus and layouts.

Chat Display Area: Implement the QTextBrowser for displaying chat messages with WhatsApp-style formatting.

User Input Area: Create QLineEdit for user input and buttons for "Attach File," "Emojis," and "Send." (Emoji functionality can be a placeholder initially if complex.)

API Configuration: Create the "Settings" menu with "API Configuration" dialog, including form fields and saving to YAML.

Chat History Management: Implement "Export Chat History" and "Import Chat History" menu items.

API Interaction: Implement the call_openai_api function and integrate it with the "Send" button.

File Attachment Handling: Implement "Attach File" functionality and display file previews.

Copy-Paste Functionality: Implement context menus for copy-paste.

Styling and Refinements: Apply WhatsApp-style CSS and refine UI elements.

Start by creating the basic structure and then progressively add functionality. I will use PyQt6, PyYAML, requests, and json libraries. I'll make sure to include necessary imports at the beginning of the code and test each part incrementally.
