from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
import os

from logger import app_logger as logger

# Interface import
from ui.main_window.main_window import Ui_MainWindow 

# Import application backend
from src.ui_file import UIFile
from src.ui_edit import UIEdit

# Import calculating module
from src.Analysis.analysis_class import UIAnalysis
from src.Statistics.stat_class import UIStat

class CellMigration(QMainWindow):
    def __init__(self):
        logger.info(f"Opened Application")
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.file = UIFile(self.ui)
        self.edit = UIEdit(self.ui)

        self.shortcuts()
        
        self.analysis = UIAnalysis(self.ui)
        
        self.stat = UIStat(self.ui)

    
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

        if self.ui.treeWidget:
            # Search in breadth
            stack = []
            for i in range(self.ui.treeWidget.topLevelItemCount()):
                stack.append(self.ui.treeWidget.topLevelItem(i))

            while stack:
                item = stack.pop(0)
                
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(data, dict) and "unsaved_changes" in data:
                    if data['unsaved_changes']:
                        self.file.on_tree_item_clicked(item)

                        reply = QMessageBox.question(
                            self,
                            "Save File",
                            f"Do you want to save the unsaved changes in {item.parent().text(0)} file? All the unsaved data will be deleted.",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )

                        if reply == QMessageBox.StandardButton.Yes:
                            self.file.save_file()
                            logger.info(f"Saved file {item.text(0)}.")
                            event.accept() 
                        else:
                            event.ignore()


                for j in range(item.childCount()):
                    stack.append(item.child(j))
            
        temp_path = os.path.join(os.getcwd(), "tmp")
        if os.path.exists(temp_path):
            for filename in os.listdir(temp_path):
                file_path = os.path.join(temp_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        logger.info(f"Closed Application")
        event.accept() 



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = CellMigration()
    window.show()
    sys.exit(app.exec())