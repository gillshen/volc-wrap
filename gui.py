import sys
import traceback
import os
import os.path
import re
import webbrowser
from typing import Tuple

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
    QMessageBox,
    QSpacerItem,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCursor

from core import AudioParams, tts
from voices import categories as voice_categories, get_voices
from languages import get_languages

ALL_CATEGORIES = "All Categories"
DEFAULT_SPEED = 10
DEFAULT_VOLUME = 10
DEFAULT_PITCH = 10
DEFAULT_AUTOPLAY = True


class IllegalFilenameError(Exception):
    pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._voices = dict([v.name, v.code] for v in get_voices())
        self._languages = {}
        self.setWindowTitle("Volcengine Text-to-Speech")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Splitter for panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Two panes
        left_pane = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(left_pane)
        right_pane = QWidget()
        splitter.addWidget(right_pane)
        splitter.setSizes([600, 300])

        # Left pane: Text edit
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Open a file or type your text here...")
        left_pane.addWidget(self.text_edit)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        left_pane.addWidget(self.console)
        left_pane.setSizes([500, 100])

        # Right pane: Controls
        right_layout = QVBoxLayout(right_pane)

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
        self.voice_selector.currentTextChanged.connect(self.on_voice_selection)
        right_layout.addWidget(self.voice_selector)

        # Language selection combobox
        self.language_selector = QComboBox()
        right_layout.addWidget(self.language_selector)

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

        # Saving dir
        right_layout.addWidget(QLabel("Directory to save the output in"))
        dir_selector = QWidget()
        right_layout.addWidget(dir_selector)
        dir_selector_layout = QHBoxLayout(dir_selector)
        dir_selector_layout.setContentsMargins(0, 0, 0, 0)
        self.save_dir_selector = QComboBox()
        self.save_dir_selector.addItem(os.getcwd())
        dir_selector_layout.addWidget(self.save_dir_selector, stretch=1)
        self.change_dir_button = QPushButton("Change")
        self.change_dir_button.clicked.connect(self.change_save_dir)
        dir_selector_layout.addWidget(self.change_dir_button, stretch=0)

        # Audio filename
        right_layout.addWidget(QLabel("Filename"))
        self.save_filename_entry = QLineEdit()
        self.save_filename_entry.setPlaceholderText("Enter audio file name here...")
        right_layout.addWidget(self.save_filename_entry)

        # Autoplay check
        self.autoplay_check = QCheckBox("Autoplay when done")
        self.autoplay_check.setChecked(DEFAULT_AUTOPLAY)
        right_layout.addWidget(self.autoplay_check)

        right_layout.addSpacerItem(QSpacerItem(0, 10))

        # API call button
        self.tts_button = QPushButton("Create Speech")
        self.tts_button.clicked.connect(self.text_to_speech)
        right_layout.addWidget(self.tts_button)

        # Make text widget zoomable
        self.text_edit.viewport().installEventFilter(self)
        self.text_edit.setMouseTracking(True)

        # Initialize linked selectors
        self.on_voice_category_selection()
        self.on_voice_selection()

        # Initialize styles
        self.set_styles()

    def set_styles(self):
        self.open_file_button.setStyleSheet(
            """
            QPushButton {
                background-color: #b1e0f0;
                padding: 6;
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
        self.language_selector.setStyleSheet(
            """
            QComboBox {
                padding: 6;
            }
            QComboBox:disabled {
                background-color: transparent;
            }
            """
        )
        self.save_dir_selector.setStyleSheet("padding: 6;")
        self.change_dir_button.setStyleSheet(
            """
            QPushButton {
                padding: 6 16;
            }
            QPushButton:hover {
                background-color: #87d0e8;
            }
            """
        )
        self.save_filename_entry.setStyleSheet("padding: 6;")

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

    def on_voice_category_selection(self):
        category = self.voice_category_selector.currentText()
        if category == ALL_CATEGORIES:
            category = ""
        voices = get_voices(category=category)
        self.voice_selector.clear()
        self.voice_selector.addItems([v.name for v in voices])

    def on_voice_selection(self):
        voice_name = self.voice_selector.currentText()
        self._languages = dict(get_languages(voice_name=voice_name))
        self.language_selector.clear()
        if self._languages:
            self.language_selector.setEnabled(True)
            self.language_selector.addItems(list(self._languages.keys()))
        else:
            self.language_selector.setDisabled(True)

    def set_speed_label(self, speed: int):
        if speed < 2:
            speed = 2
            self.speed_slider.setValue(speed)
        self.speed_label.setText(f"Speed: {speed / 10}")

    def set_volume_label(self, volume: int):
        self.volume_label.setText(f"Volume: {volume / 10}")

    def set_pitch_label(self, pitch: int):
        self.pitch_label.setText(f"Pitch: {pitch / 10}")

    def change_save_dir(self):
        file_name = QFileDialog.getExistingDirectory(
            self,
            "Choose a directory",
        )
        if file_name:
            self.save_dir_selector.addItem(file_name)
            self.save_dir_selector.setCurrentText(file_name)

    def get_save_path(self) -> str:
        save_filename = self.save_filename_entry.text().strip()
        if not save_filename:
            return ""
        if re.search(r'[<>:"/\\|?*]', save_filename):
            raise IllegalFilenameError
        if not save_filename.endswith(".mp3"):
            save_filename += ".mp3"
        save_dir = self.save_dir_selector.currentText()
        save_path = os.path.join(save_dir, save_filename)
        return save_path

    def get_voice_type(self) -> str:
        voice_name = self.voice_selector.currentText()
        return self._voices[voice_name]

    def get_language(self) -> str:
        lang_name = self.language_selector.currentText()
        return self._languages.get(lang_name, "")

    def get_speed_ratio(self) -> float:
        return self.speed_slider.value() / 10

    def get_volume_ratio(self) -> float:
        return self.volume_slider.value() / 10

    def get_pitch_ratio(self) -> float:
        return self.pitch_slider.value() / 10

    def text_to_speech(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(
                self,
                "Text required",
                "You did not provide any text for conversion.",
            )
            return

        try:
            save_path = self.get_save_path()
        except IllegalFilenameError:
            QMessageBox.warning(
                self,
                "Illegal filename",
                'Filename cannot contain any of following characters: <>:"/\\|?*',
            )
            return
        if not save_path:
            QMessageBox.warning(self, "Filename required", "Please specify a filename.")
            return

        if os.path.exists(save_path):
            overwrite = QMessageBox.question(
                self,
                "File already exists",
                f"{save_path} already exists.\nDo you want to overwrite it?",
            )
            if overwrite == QMessageBox.StandardButton.No:
                return

        audio_params = AudioParams(
            voice_type=self.get_voice_type(),
            language=self.get_language(),
            speed_ratio=self.get_speed_ratio(),
            volume_ratio=self.get_volume_ratio(),
            pitch_ratio=self.get_pitch_ratio(),
        )

        self.worker = ApiCaller(text, audio_params, save_path)
        self.worker.in_progress.connect(self.log)
        self.worker.started.connect(self.on_tts_start)
        self.worker.finished.connect(self.on_tts_finish)
        self.worker.error.connect(self.on_tts_error)
        self.worker.start()

    def on_tts_start(self):
        self.tts_button.setDisabled(True)
        self.console.clear()
        self.log("Starting...\n")

    def on_tts_finish(self, exit_with_error: int):
        self.tts_button.setEnabled(True)
        if exit_with_error:
            self.log("Task terminated due to error.")
            return
        save_path = self.worker.save_path
        self.log(f"Finished.\nAudio saved at {save_path}.")
        if self.autoplay_check.isChecked():
            webbrowser.open(save_path)

    def on_tts_error(self, data: Tuple[Exception, str]):
        self.tts_button.setEnabled(True)
        exc, message = data
        self.log(f"Error:\n{message}\n")
        QMessageBox.critical(self, exc.__class__.__name__, message)

    def log(self, message):
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        self.console.ensureCursorVisible()
        self.console.setReadOnly(False)
        self.console.insertPlainText(message)
        self.console.setReadOnly(True)


class ApiCaller(QThread):
    in_progress = pyqtSignal(str)
    error = pyqtSignal(tuple)
    finished = pyqtSignal(int)

    def __init__(self, text: str, audio_params: AudioParams, save_path: str) -> None:
        super().__init__()
        self.text = text
        self.audio_params = audio_params
        self.save_path = save_path

    def run(self):
        try:
            for _, message in tts(self.text, self.audio_params, self.save_path):
                self.in_progress.emit(f"{message}...\n")
        except Exception as e:
            self.error.emit((e, traceback.format_exc()))
            self.finished.emit(1)
        else:
            self.finished.emit(0)


if __name__ == "__main__":
    app = QApplication([])
    main_window = MainWindow()
    main_window.resize(800, 600)
    main_window.show()
    sys.exit(app.exec())
