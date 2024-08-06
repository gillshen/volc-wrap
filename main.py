from gui import QApplication, MainWindow
import sys

app = QApplication([])
main_window = MainWindow()
main_window.resize(800, 600)
main_window.show()
sys.exit(app.exec())
