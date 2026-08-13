import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QFileDialog, QLabel, QScrollArea, QFrame
)


class ChatWindow(QMainWindow):
    def __init__(self, working_dir):
        super().__init__()
        self.setWindowTitle("Data.AI Chatbot")
        self.setGeometry(200, 200, 500, 600)

        self.working_dir = working_dir

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Chat area (scrollable)
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)

        # Input area
        input_layout = QHBoxLayout()
        self.input_box = QTextEdit()
        self.input_box.setFixedHeight(40)  # single line style
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)

    def send_message(self):
        msg = self.input_box.toPlainText().strip()
        if not msg:
            return
        self.chat_area.append(f"You: {msg}")
        self.input_box.clear()

        # For now just echo response
        self.chat_area.append(f"AI: Echo -> {msg}")


class StartupDialog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Working Directory")
        self.setGeometry(300, 300, 400, 120)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.label = QLabel("Please choose a working directory:")
        layout.addWidget(self.label)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.choose_dir)
        layout.addWidget(browse_btn)

    def choose_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.chat_window = ChatWindow(folder)
            self.chat_window.show()
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    startup = StartupDialog()
    startup.show()
    sys.exit(app.exec_())
