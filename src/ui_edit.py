
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget
)
from PyQt6.QtGui import QUndoStack

from logger import app_logger as logger

class UIEdit(QWidget):
    """
    Class handling editing Excel files in tab Widget.
    """
    def __init__(self, ui):
        """
        Initialize the UIEdit handler.
        Args:
            ui (QMainWindow): The main UI window object.
        """
        super().__init__()  
        self.ui = ui
        self.undo_stack = QUndoStack(self)  # Stack Undo/Redo

        # Connect UI actions and tree widget signals to the appropriate handlers.
        self.ui.actionCopy.triggered.connect(self.copy_selection)
        self.ui.actionPaste.triggered.connect(self.paste_selection)
        self.ui.actionCut.triggered.connect(self.cut_selection)
        self.ui.actionUndo.triggered.connect(self.undo_action)
        self.ui.actionRedo.triggered.connect(self.redo_action)
        self.ui.actionSelect_All.triggered.connect(self.select_all)

    def get_current_table_view(self):
        """
        Retrieve the currently active QTableView from the visible page.

        Returns:
            QTableView | None: The currently active table view widget in the selected
            sheet tab, or None if no tab widget is found.
        """
        page = self.ui.stackedWidget.currentWidget()
        tab_widget = page.findChild(QTabWidget)
        if not tab_widget:
            logger.error("get_current_table_view : No tab_widget was found")
            return None
        return tab_widget.currentWidget()

    def copy_selection(self):
        """
        Imitates the copy function from Excel in QTabWidget.
        """
        table = self.get_current_table_view()
        if not table or not table.hasFocus():
            logger.error("copy_selection : no table or not has focus")
            return

        selection = table.selectionModel().selectedIndexes()
        if not selection:
            logger.error("copy_selection : no selection")
            return

        # Sort by rows, then by columns to make sure correct order of cells during copying
        selection = sorted(selection, key=lambda index: (index.row(), index.column()))

        # Group by rows
        current_row = -1
        row_data = []
        all_rows = []

        for index in selection:
            if index.row() != current_row:
                if row_data:
                    all_rows.append('\t'.join(row_data))
                row_data = []
                current_row = index.row()
            row_data.append(str(index.data()) if index.isValid() else '')

        if row_data:
            all_rows.append('\t'.join(row_data))

        text = '\n'.join(all_rows)

        # Dump into buffer (clipboard)
        QApplication.clipboard().setText(text)

    def paste_selection(self):
        """
        Imitates the paste function from Excel in QTabWidget.
        """
        table = self.get_current_table_view()
        if table is None or not table.hasFocus():
            logger.error("paste_selection : no table or not has focus")
            return

        model = table.model()
        if not model or not hasattr(model, "setDataWithUndo"):
            return

        selected = table.selectedIndexes()
        if not selected:
            logger.error("paste_selection : no selection")
            return

        # Choose the top left cell as a start for pasting
        top_left = selected[0].row(), selected[0].column()

        # Reading from buffer (clipboard)
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        rows = text.strip().split('\n')
        data = [r.split('\t') for r in rows]

        # Writing into the model in QTabWidget
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                r = top_left[0] + i
                c = top_left[1] + j
                index = model.index(r, c)
                model.setDataWithUndo(index, value, self.undo_stack)

    def cut_selection(self):
        """
        Imitates the cut function from Excel in QTabWidget.
        """
        self.copy_selection()  # copy selected cells
        self.delete_selection()  # delete selected cells

    def delete_selection(self):
        """
        Imitates the delete function from Excel in QTabWidget.
        """
        table = self.get_current_table_view()
        if table is None or not table.hasFocus():
            logger.error("delete_selection : no table or not has focus")
            return
        
        selection = table.selectionModel().selectedIndexes()

        model = table.model()

        for index in selection:
            if index.isValid():
                # Change the content of the cell to "" and store in Undo Stack
                model.setDataWithUndo(index, "", self.undo_stack)

    def undo_action(self):
        """
        Imitates the undo function from Excel in QTabWidget.
        """
        if self.undo_stack.canUndo():
            self.undo_stack.undo()

    def redo_action(self):
        """
        Imitates the redo function from Excel in QTabWidget.
        """
        if self.undo_stack.canRedo():
            self.undo_stack.redo()

    def select_all(self):
        """
        Imitates the select all function from Excel in QTabWidget.
        """
        table = self.get_current_table_view()
        if table is not None:
            table.selectAll()


    