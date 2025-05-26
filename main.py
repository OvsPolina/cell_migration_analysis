# app.py
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtGui import QShortcut, QKeySequence

from ui.main_window.main_window import Ui_MainWindow  # импорт сгенерированного интерфейса
from src.ui_file import UIFile
from src.ui_edit import UIEdit
from src.Analysis.autocorrelation import UIAutocorrelation

class CellMigration(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.file = UIFile(self.ui)
        self.edit = UIEdit(self.ui)

        self.shortcuts()
        
        self.config_autocorrelation = UIAutocorrelation(self.ui)
    
    def shortcuts(self):
        copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        copy_shortcut.activated.connect(self.edit.copy_selection)

        paste_shortcut = QShortcut(QKeySequence.StandardKey.Paste, self)
        paste_shortcut.activated.connect(self.edit.paste_selection)

        cut_shortcut = QShortcut(QKeySequence.StandardKey.Cut, self)
        cut_shortcut.activated.connect(self.edit.cut_selection)

        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self.edit.undo_action)

        redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        redo_shortcut.activated.connect(self.edit.redo_action)



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = CellMigration()
    window.show()
    sys.exit(app.exec())