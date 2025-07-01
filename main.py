# app.py
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtGui import QShortcut, QKeySequence
import os

from ui.main_window.main_window import Ui_MainWindow  # импорт сгенерированного интерфейса
from src.ui_file import UIFile
from src.ui_edit import UIEdit
from src.Analysis.autocorrelation import UIAutocorrelation
from src.Analysis.speed import UISpeed
from src.Analysis.msd import UIMSD
from src.Analysis.dir_ratio import UIDirRatio

from src.Statistics.ttest import UITTest
from src.Statistics.anova import UIANOVA

class CellMigration(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.file = UIFile(self.ui)
        self.edit = UIEdit(self.ui)

        self.shortcuts()
        
        self.analysis_autocorrelation = UIAutocorrelation(self.ui)
        self.analysis_speed = UISpeed(self.ui)
        self.analysis_MSD = UIMSD(self.ui)
        self.analysis_dirratio = UIDirRatio(self.ui)

        self.stat_ttest = UITTest(self.ui)
        self.stat_anova = UIANOVA(self.ui)

    
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

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Exit",
            "Do you want to exit the application? All the unsaved data will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            temp_path = os.path.join(os.getcwd(), "tmp")
            if os.path.exists(temp_path):
                for filename in os.listdir(temp_path):
                    file_path = os.path.join(temp_path, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            event.accept()  # Закрыть окно
        else:
            event.ignore()  # Остановить закрытие



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = CellMigration()
    window.show()
    sys.exit(app.exec())