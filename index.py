import sys
import os
from main_window import MainApp
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    my_app = MainApp()
    sys.exit(app.exec_())