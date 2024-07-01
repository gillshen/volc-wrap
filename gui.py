import sys
import traceback

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPlainTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFileDialog,
    QSplitter,
)
from PyQt6.QtCore import Qt

from core import tts, ApiError
from voices import categories as voice_categories, get_voices

ALL_CATEGORIES = "All Categories"


class App(QMainWindow):
    def __init__(self):
        super().__init__()

        self._voices = dict([v.name, v.code] for v in get_voices())
        self.setWindowTitle("Volcengine Text-to-Speech")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Splitter for panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left pane: Plain text widget
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Type your text here...")
        splitter.addWidget(self.text_edit)

        # Right pane: Controls
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        splitter.addWidget(right_pane)

        # Open file button
        self.open_file_button = QPushButton("Open Text File")
        self.open_file_button.clicked.connect(self.open_file_dialog)
        right_layout.addWidget(self.open_file_button)

        # Audio file name entry
        self.save_path_entry = QLineEdit()
        self.save_path_entry.setPlaceholderText("Enter audio file name")
        right_layout.addWidget(self.save_path_entry)

        # Voice selection combobox
        self.voice_category_selector = QComboBox()
        self.voice_category_selector.addItems([ALL_CATEGORIES] + voice_categories)
        self.voice_category_selector.currentTextChanged.connect(
            self.on_voice_category_selection
        )
        right_layout.addWidget(self.voice_category_selector)
        self.voice_selector = QComboBox()
        right_layout.addWidget(self.voice_selector)

        # Add spacer to push widgets to the top
        right_layout.addStretch()

        # API call button
        self.tts_button = QPushButton("Text to Speech")
        self.tts_button.clicked.connect(self.text_to_speech)
        right_layout.addWidget(self.tts_button)

        # Make text widget zoomable
        self.text_edit.viewport().installEventFilter(self)
        self.text_edit.setMouseTracking(True)

        # Initialize the voice selector
        self.on_voice_category_selection()

    def eventFilter(self, source, event):
        if event.type() == event.Type.Wheel and source is self.text_edit.viewport():
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                if event.angleDelta().y() > 0:
                    self.text_edit.zoomIn()
                else:
                    self.text_edit.zoomOut()
                return True
        return super().eventFilter(source, event)

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            "",
            "Text Files (*.txt);;All Files (*)",
        )
        if file_name:
            with open(file_name, "r", encoding="utf-8") as file:
                self.text_edit.setPlainText(file.read())

    def save_file_dialog(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Audio File",
            "",
            "MP3 File (*.mp3)",
        )
        if file_name:
            self.save_path_entry.setText(file_name)
            return file_name

    def on_voice_category_selection(self):
        category = self.voice_category_selector.currentText()
        if category == ALL_CATEGORIES:
            category = ""
        voices = get_voices(category=category)
        self.voice_selector.clear()
        self.voice_selector.addItems([v.name for v in voices])

    def text_to_speech(self):
        save_path = self.save_path_entry.text() or self.save_file_dialog()
        if not save_path:
            return
        text = self.text_edit.toPlainText()
        voice_name = self.voice_selector.currentText()
        try:
            for _, message in tts(
                text,
                save_path,
                voice_type=self._voices[voice_name],
            ):
                print(message)
        except ApiError:
            print(traceback.format_exc())
        else:
            print("tts done")


if __name__ == "__main__":
    app = QApplication([])
    ex = App()
    ex.show()
    sys.exit(app.exec())
