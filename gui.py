import sys
import traceback
import os
import os.path
import webbrowser

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPlainTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QSlider,
    QLineEdit,
    QCheckBox,
    QFileDialog,
    QSplitter,
    QSpacerItem,
)
from PyQt6.QtCore import Qt

from core import tts, ApiError
from voices import categories as voice_categories, get_voices

ALL_CATEGORIES = "All Categories"
DEFAULT_SPEED = 10
DEFAULT_VOLUME = 10
DEFAULT_PITCH = 10
DEFAULT_AUTOPLAY = 10


class MainWindow(QMainWindow):
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
        self.text_edit.setPlaceholderText("Open a file or type your text here...")
        splitter.addWidget(self.text_edit)

        # Right pane: Controls
        right_pane = QWidget()
        right_layout = QVBoxLayout(right_pane)
        splitter.addWidget(right_pane)
        splitter.setSizes([600, 300])

        # Open file button
        self.open_file_button = QPushButton("Open Text File")
        self.open_file_button.clicked.connect(self.open_file_dialog)
        right_layout.addWidget(self.open_file_button)

        right_layout.addSpacerItem(QSpacerItem(0, 10))

        # Voice selection combobox
        right_layout.addWidget(QLabel("Select a voice"))
        self.voice_category_selector = QComboBox()
        self.voice_category_selector.addItems([ALL_CATEGORIES] + voice_categories)
        self.voice_category_selector.currentTextChanged.connect(
            self.on_voice_category_selection
        )
        right_layout.addWidget(self.voice_category_selector)
        self.voice_selector = QComboBox()
        right_layout.addWidget(self.voice_selector)

        right_layout.addSpacerItem(QSpacerItem(0, 10))

        self.speed_label = QLabel()
        right_layout.addWidget(self.speed_label)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 30)
        self.speed_slider.setValue(DEFAULT_SPEED)
        self.set_speed_label(DEFAULT_SPEED)
        self.speed_slider.valueChanged.connect(self.set_speed_label)
        right_layout.addWidget(self.speed_slider)

        self.volume_label = QLabel()
        right_layout.addWidget(self.volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(1, 30)
        self.volume_slider.setValue(DEFAULT_VOLUME)
        self.set_volume_label(DEFAULT_VOLUME)
        self.volume_slider.valueChanged.connect(self.set_volume_label)
        right_layout.addWidget(self.volume_slider)

        self.pitch_label = QLabel()
        right_layout.addWidget(self.pitch_label)
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(1, 30)
        self.pitch_slider.setValue(DEFAULT_PITCH)
        self.set_pitch_label(DEFAULT_PITCH)
        self.pitch_slider.valueChanged.connect(self.set_pitch_label)
        right_layout.addWidget(self.pitch_slider)

        # Add spacer to push widgets to the top
        right_layout.addStretch()

        right_layout.addSpacerItem(QSpacerItem(0, 20))

        # Audio file name entry
        self.save_path_entry = QLineEdit()
        self.save_path_entry.setPlaceholderText("Enter audio file name here...")
        right_layout.addWidget(self.save_path_entry)

        # Autoplay check
        self.autoplay_check = QCheckBox("Autoplay when done")
        self.autoplay_check.setChecked(DEFAULT_AUTOPLAY)
        right_layout.addWidget(self.autoplay_check)

        right_layout.addSpacerItem(QSpacerItem(0, 10))

        # API call button
        self.tts_button = QPushButton("Text to Speech")
        self.tts_button.clicked.connect(self.text_to_speech)
        right_layout.addWidget(self.tts_button)

        # Make text widget zoomable
        self.text_edit.viewport().installEventFilter(self)
        self.text_edit.setMouseTracking(True)

        # Initialize the voice selector
        self.on_voice_category_selection()

        # Initialize styles
        self.set_styles()

    def set_styles(self):
        self.open_file_button.setStyleSheet(
            """
            QPushButton {
                background-color: #b1e0f0;
                padding: 5;
            }
            QPushButton:hover {
                background-color: #87d0e8;
            }
            """
        )
        self.tts_button.setStyleSheet(
            """
            QPushButton {
                background-color: #b1e0f0;
                padding: 10;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #87d0e8;
            }
            """
        )
        self.voice_category_selector.setStyleSheet("padding: 6;")
        self.voice_selector.setStyleSheet("padding: 6;")
        self.save_path_entry.setStyleSheet("padding: 6;")

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

    def set_speed_label(self, speed: int):
        if speed < 2:
            speed = 2
            self.speed_slider.setValue(speed)
        self.speed_label.setText(f"Speed: {speed / 10}")

    def set_volume_label(self, volume: int):
        self.volume_label.setText(f"Volume: {volume / 10}")

    def set_pitch_label(self, pitch: int):
        self.pitch_label.setText(f"Pitch: {pitch / 10}")

    def get_save_path(self) -> str:
        path = self.save_path_entry.text()
        if not path:
            return self.save_file_dialog()
        if not path.endswith(".mp3"):
            path += ".mp3"
        cwd = os.getcwd()
        return os.path.join(cwd, path)

    def get_voice_type(self) -> str:
        voice_name = self.voice_selector.currentText()
        return self._voices[voice_name]

    def get_speed_ratio(self) -> float:
        return self.speed_slider.value() / 10

    def get_volume_ratio(self) -> float:
        return self.volume_slider.value() / 10

    def get_pitch_ratio(self) -> float:
        return self.pitch_slider.value() / 10

    def text_to_speech(self):
        save_path = self.get_save_path()
        if not save_path:
            return
        text = self.text_edit.toPlainText()
        try:
            for _, message in tts(
                text,
                save_path,
                voice_type=self.get_voice_type(),
                speed_ratio=self.get_speed_ratio(),
                volume_ratio=self.get_volume_ratio(),
                pitch_ratio=self.get_pitch_ratio(),
            ):
                print(message)
        except ApiError:
            print(traceback.format_exc())
        else:
            if self.autoplay_check.isChecked():
                webbrowser.open(save_path)
            print("tts done")


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.resize(800, 600)
    main_window.show()
    sys.exit(app.exec())
