# app.py
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from ui.main_window.main_window import Ui_MainWindow  # импорт сгенерированного интерфейса
from src.ui_file import UIFile
from src.Analysis.autocorrelation import UIAutocorrelation

class CellMigration(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.file = UIFile(self.ui)
        self.config_autocorrelation = UIAutocorrelation(self.ui)




if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = CellMigration()
    window.show()
    sys.exit(app.exec())