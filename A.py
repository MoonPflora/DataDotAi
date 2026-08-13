# A.py (with splash/loading)
import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
import B_adapter  # ChatWindow

# --- Splash / Loading window ---
class LoadingWindow(QtWidgets.QWidget):
    def __init__(self, on_finished):
        super().__init__()
        self.on_finished = on_finished  # callback after loading finishes
        self.setWindowTitle("Data.AI Loading")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #2b2b2b;")

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.setLayout(layout)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "ai.png")
        self.logo_label = QtWidgets.QLabel()
        if os.path.exists(logo_path):
            pixmap = QtGui.QPixmap(logo_path)
            pixmap = pixmap.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setMaximum(100)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #444444;
                color: white;
                border-radius: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3399ff;
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress)

        # Timer for animation
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.value = 0
        self.timer.start(30)  # roughly 3 sec

    def update_progress(self):
        if self.value >= 100:
            self.timer.stop()
            self.close()
            if self.on_finished:
                self.on_finished()  # launch next window
        else:
            self.value += 1
            self.progress.setValue(self.value)


# --- Original first window ---
class Ui_Start(object):
    def setupUi(self, Start):
        Start.setObjectName("Data.AI")
        Start.setWindowTitle("Data.AI")
        Start.resize(300, 400)
        self.central_layout = QtWidgets.QVBoxLayout(Start)
        self.central_layout.setContentsMargins(20, 20, 20, 20)
        self.central_layout.setSpacing(15)
        Start.setLayout(self.central_layout)

        # Logo
        self.logo = QtWidgets.QLabel(Start)
        logo_path = os.path.join(os.path.dirname(__file__), "ai.png")
        if os.path.exists(logo_path):
            self.logo.setPixmap(QtGui.QPixmap(logo_path))
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(150, 150)
        self.logo.setAlignment(QtCore.Qt.AlignCenter)
        self.central_layout.addWidget(self.logo, alignment=QtCore.Qt.AlignCenter)

        # Info label
        self.label = QtWidgets.QLabel("Please select working directory", Start)
        self.label.setStyleSheet("color: #d0e0ff; font-size: 12pt;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.central_layout.addWidget(self.label)

        # Explanatory text
        self.agree_text = QtWidgets.QLabel(
            "By agreeing, you accept our Privacy & Policy documents.", Start
        )
        self.agree_text.setStyleSheet("color: #d0e0ff; font-size: 10pt;")
        self.agree_text.setWordWrap(True)
        self.agree_text.setAlignment(QtCore.Qt.AlignCenter)
        self.central_layout.addWidget(self.agree_text)

        # Radio + policy
        self.radio_layout = QtWidgets.QHBoxLayout()
        self.radioButton = QtWidgets.QRadioButton("Agree", Start)
        self.radioButton.setStyleSheet("color: #d0e0ff;")
        self.policy = QtWidgets.QLabel('<a href="#">Privacy & Policy</a>', Start)
        self.policy.setStyleSheet("color: #00aaff; font-size: 10pt;")
        self.policy.setOpenExternalLinks(False)
        self.radio_layout.addStretch()
        self.radio_layout.addWidget(self.radioButton)
        self.radio_layout.addWidget(self.policy)
        self.radio_layout.addStretch()
        self.central_layout.addLayout(self.radio_layout)

        # Browse button
        self.browse = QtWidgets.QPushButton("Browse", Start)
        self.browse.setFixedWidth(100)
        self.browse.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: #3a3a3a;
                border-radius: 8px;
                padding:6px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        self.browse.setEnabled(False)
        self.central_layout.addWidget(self.browse, alignment=QtCore.Qt.AlignCenter)

        Start.setStyleSheet("background-color: #2b2b2b;")


class DataAIWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Start()
        self.ui.setupUi(self)
        self.selected_directory = None
        self.ui.radioButton.toggled.connect(self.radio_toggled)
        self.ui.browse.clicked.connect(self.select_folder)
        self.ui.policy.linkActivated.connect(self.open_policy_file)

    def radio_toggled(self, checked):
        self.ui.browse.setEnabled(checked)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if folder:
            self.selected_directory = folder
            self.second_window = B_adapter.ChatWindow(self.selected_directory)
            self.second_window.show()
            self.close()

    def open_policy_file(self):
        policy_path = os.path.join(os.path.dirname(__file__), "policy.txt")
        if os.path.exists(policy_path):
            os.startfile(policy_path)
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "policy.md not found!")


# --- Run the app with splash ---
if __name__ == "__main__":
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)

    # Keep reference to main window
    global main_window
    main_window = None

    def start_main_window():
        global main_window
        main_window = DataAIWindow()
        main_window.show()

    splash = LoadingWindow(on_finished=start_main_window)
    splash.show()

    sys.exit(app.exec_())
