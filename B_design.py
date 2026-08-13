# B.py
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
class ChatWindow(QtWidgets.QMainWindow):
    def __init__(self, selected_folder):
        super().__init__()
        self.selected_folder = selected_folder
        self.setWindowTitle("Chat - Data.AI")
        self.resize(600, 700)
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("background-color: #2b2b2b;")
        # Main layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(10)

        # Chat display (read-only)
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

        # Logo label (background)
        self.logo_label = QtWidgets.QLabel(self)
        pixmap = QtGui.QPixmap("logo.png")
        w = int(pixmap.width() * 0.75)   # 25% smaller
        h = int(pixmap.height() * 0.75)
        pixmap = pixmap.scaled(w, h, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.logo_label.lower()  # make sure it's behind chat_display

        # Input + send button
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

        # Buttons: Change Folder & Clear History
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.buttons_layout)

        self.change_folder_button = QtWidgets.QPushButton("Change Folder", self)
        self.change_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #3399ff;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding:6px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        self.buttons_layout.addWidget(self.change_folder_button)

        self.clear_history_button = QtWidgets.QPushButton("Clear History", self)
        self.clear_history_button.setStyleSheet("""
            QPushButton {
                background-color: #3399ff;
                color: white;
                font-weight: bold;
                border-radius: 10px;
                padding:6px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        self.buttons_layout.addWidget(self.clear_history_button)

        # Connect signals
        self.send_button.clicked.connect(self.send_message)
        self.change_folder_button.clicked.connect(self.change_folder)
        self.clear_history_button.clicked.connect(self.clear_history)
        self.input_text.installEventFilter(self)

        # Show initial folder
        self.chat_display.append(
            f'<p style="color:#d0e0ff; margin:5px 0;"><b>Selected folder:</b> {self.selected_folder}</p>'
        )

    # Event filter for Enter / Shift+Enter behavior
    def eventFilter(self, obj, event):
        if obj == self.input_text:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                    if event.modifiers() & QtCore.Qt.ShiftModifier:
                        return False  # allow newline
                    else:
                        self.send_message()
                        return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep logo centered over chat_display
        self.logo_label.setGeometry(
            self.chat_display.x(),
            self.chat_display.y(),
            self.chat_display.width(),
            self.chat_display.height()
        )

    def send_message(self):
        message = self.input_text.toPlainText().strip()
        if message:
            # User message bubble
            self.chat_display.append(
                f'<div style="background-color:#4a4a4a; padding:8px; margin:5px 0; border-radius:10px;">'
                f'<b style="color:#d0e0ff;">You:</b> {message}</div>'
            )
            self.input_text.clear()
            # Placeholder AI response bubble
            ai_response = f'Echo: {message} ' * 3  # long response test
            self.chat_display.append(
                f'<div style="background-color:#2f3a5f; padding:8px; margin:5px 0; border-radius:10px;">'
                f'<b style="color:#a0c4ff;">AI:</b> {ai_response}</div>'
            )
            self.chat_display.verticalScrollBar().setValue(self.chat_display.verticalScrollBar().maximum())

    def change_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if folder:
            self.selected_folder = folder
            self.chat_display.append(
                f'<p style="color:#d0e0ff; margin:6px 0;"><b>Folder changed to:</b> {self.selected_folder}</p>'
            )

    def clear_history(self):
        self.chat_display.clear()
        self.chat_display.append(
            f'<p style="color:#d0e0ff; margin:5px 0;"><b>Selected folder:</b> {self.selected_folder}</p>'
        )

# Standalone testing

if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon_path = os.path.join(os.path.dirname(__file__), "ai.ico")
    print("Icon exists?", os.path.exists(icon_path))
    app.setWindowIcon(QIcon(icon_path))

    w = QMainWindow()
    w.setWindowTitle("Test Icon")
    w.show()
    sys.exit(app.exec_())
