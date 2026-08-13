# B_adapter.py
import sys
import json
import re
import html
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
import config
from terminal import TerminalSession

class WorkerThread(QtCore.QThread):
    finished = QtCore.pyqtSignal(dict)

    def __init__(self, terminal: TerminalSession, message: str, folder: str):
        super().__init__()
        self.terminal = terminal
        self.message = message
        self.folder = folder  # selected folder snapshot

    def run(self):
        # Preserve history
        preserved_history = self.terminal.conversation.get("history", [])

        # Prepare conversation for this message
        self.terminal.conversation["message"] = self.message
        self.terminal.conversation["target"] = ["ai"]
        self.terminal.conversation["data"] = ""
        self.terminal.conversation["history"] = preserved_history

        # Refresh folder snapshot
        self.terminal.update_input_with_folder_tree()

        from communicator import handle_message  # avoid circular imports
        handle_message(json.dumps(self.terminal.conversation))

        response = self.terminal.get_response()
        if response:
            response_history = response.get("history", preserved_history)
            self.terminal.conversation.update(response)
            self.terminal.conversation["history"] = response_history
            self.finished.emit(self.terminal.conversation)
        else:
            self.finished.emit({"message": "[No response within timeout]", "history": preserved_history})


class ChatWindow(QtWidgets.QWidget):
    def __init__(self, selected_folder):
        super().__init__()
        self.selected_folder = selected_folder
        self.setWindowTitle("Chat - Data.AI")
        self.resize(600, 700)
        self.setStyleSheet("background-color: #2b2b2b;")

        # Terminal session with fresh conversation but empty input
        self.terminal = TerminalSession()
        self.terminal.conversation = {
            "message": "",
            "history": [],
            "data": "",
            "target": [],
            "input": {}
        }
        self.threads = []

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # Chat display
        self.chat_display = QtWidgets.QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: rgba(58, 58, 58, 25);
            color: white;
            font-size: 13pt;
            font-family: 'Segoe UI';
            padding:10px;
            border-radius: 12px;
        """)
        self.chat_display.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.chat_display.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.layout.addWidget(self.chat_display)

        # Logo
        self.logo_label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("logo.png")
        w, h = int(pixmap.width() * 0.75), int(pixmap.height() * 0.75)
        self.logo_label.setPixmap(pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.logo_label.lower()

        # Input + send
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.bottom_layout)
        self.input_text = QtWidgets.QTextEdit(self)
        self.input_text.setFixedHeight(80)
        self.input_text.setStyleSheet("""
            background-color: #3a3a3a;
            color: white;
            font-size: 12pt;
            font-family: 'Segoe UI';
            padding:8px;
            border-radius: 10px;
            border: 1px solid #444444;
            selection-background-color: #555555;
        """)
        self.bottom_layout.addWidget(self.input_text)
        self.send_button = QtWidgets.QPushButton("Send", self)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #3399ff;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding:8px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        self.bottom_layout.addWidget(self.send_button)

        # Folder / Clear buttons
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)
        self.change_folder_button = QtWidgets.QPushButton("Change Folder", self)
        self.change_folder_button.setStyleSheet(self.send_button.styleSheet())
        self.buttons_layout.addWidget(self.change_folder_button)
        self.clear_history_button = QtWidgets.QPushButton("Clear History", self)
        self.clear_history_button.setStyleSheet(self.send_button.styleSheet())
        self.buttons_layout.addWidget(self.clear_history_button)

        # Signals
        self.send_button.clicked.connect(self.on_send)
        self.change_folder_button.clicked.connect(self.on_change_folder)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.input_text.installEventFilter(self)

        self.chat_display.append(f'<p style="color:#d0e0ff; margin:5px 0;"><b>Selected folder:</b> {self.selected_folder}</p>')

    def format_message(self, message: str) -> str:
        message = html.escape(message)
        message = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', message)
        message = re.sub(r'\*(.+?)\*', r'<i>\1</i>', message)
        message = message.replace('\n', '<br>')
        return message

    def eventFilter(self, obj, event):
        if obj == self.input_text and event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                if event.modifiers() & QtCore.Qt.ShiftModifier:
                    return False
                else:
                    self.on_send()
                    return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.logo_label.setGeometry(self.chat_display.x(), self.chat_display.y(),
                                    self.chat_display.width(), self.chat_display.height())

    def on_send(self):
        message = self.input_text.toPlainText().strip()
        if not message:
            return

        self.chat_display.append(
            f'<div style="background-color:#4a4a4a; padding:8px; margin:5px 0; border-radius:10px;">'
            f'<b style="color:#d0e0ff;">You:</b> {self.format_message(message)}</div>'
        )
        self.input_text.clear()
        self.chat_display.append(
            '<div style="background-color:#444444; padding:8px; margin:5px 0; border-radius:10px;"><i>Processing...</i></div>'
        )

        # Pass selected folder to thread for fresh snapshot but preserve history
        thread = WorkerThread(self.terminal, message, self.selected_folder)
        thread.finished.connect(self.on_response)
        thread.finished.connect(lambda: self.threads.remove(thread))
        self.threads.append(thread)
        thread.start()

    def on_response(self, response_json):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.select(QtGui.QTextCursor.BlockUnderCursor)
        if "Processing..." in cursor.selectedText():
            cursor.removeSelectedText()
            cursor.deleteChar()

        message = response_json.get("message", "[No response]")
        formatted_msg = self.format_message(message)
        self.chat_display.append(
            f'<div style="background-color:#2f3a5f; padding:8px; margin:5px 0; border-radius:10px;">'
            f'<b style="color:#a0c4ff;">AI:</b> {formatted_msg}</div>'
        )
        self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def on_change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if folder:
            self.selected_folder = folder
            config.WORKING_DIR = folder
            preserved_history = self.terminal.conversation.get("history", [])
            self.terminal.conversation = {
                "message": "",
                "history": preserved_history,
                "data": "",
                "target": [],
                "folder": {}
            }
            self.chat_display.append(
                f'<p style="color:#d0e0ff; margin:6px 0;"><b>Folder changed to:</b> {self.selected_folder}</p>'
            )

    def clear_history(self):
        self.chat_display.clear()
        self.chat_display.append(
            f'<p style="color:#d0e0ff; margin:5px 0;"><b>Selected folder:</b> {self.selected_folder}</p>'
        )
        self.terminal.conversation = {"message": "", "history": [], "data": "", "target": [], "folder": {}}

    def closeEvent(self, event):
        self.terminal.conversation = {"message": "", "history": [], "data": "", "target": [], "folder":""}
