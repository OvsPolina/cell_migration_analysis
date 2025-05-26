
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QTableView, QTableWidgetItem, QTreeWidgetItem, QTabWidget, QVBoxLayout, QHeaderView
)
from PyQt6.QtGui import QUndoStack, QUndoCommand


class UIEdit(QWidget):
    def __init__(self, ui):
        super().__init__()  # нужно вызвать, чтобы QWidget инициализировался корректно
        self.ui = ui
        self.undo_stack = QUndoStack(self)  # стек Undo/Redo
        self._connect_signals()

    def _connect_signals(self):
        self.ui.actionCopy.triggered.connect(self.copy_selection)
        self.ui.actionPaste.triggered.connect(self.paste_selection)
        self.ui.actionCut.triggered.connect(self.cut_selection)
        self.ui.actionUndo.triggered.connect(self.undo_action)
        self.ui.actionRedo.triggered.connect(self.redo_action)
        self.ui.actionSelect_All.triggered.connect(self.select_all)

    def get_current_table_view(self):
        page = self.ui.stackedWidget.currentWidget()
        tab_widget = page.findChild(QTabWidget)
        if not tab_widget:
            return None
        return tab_widget.currentWidget()

    def copy_selection(self):
        table = self.get_current_table_view()
        if not table or not table.hasFocus():
            return

        selection = table.selectionModel().selectedIndexes()
        if not selection:
            return

        # Сортируем сначала по строкам, потом по столбцам
        selection = sorted(selection, key=lambda index: (index.row(), index.column()))

        # Группируем по строкам
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

        # Финальный текст
        text = '\n'.join(all_rows)

        # В буфер обмена
        QApplication.clipboard().setText(text)

    def paste_selection(self):
        table = self.get_current_table_view()
        if table is None or not table.hasFocus():
            return

        model = table.model()
        if not model or not hasattr(model, "setDataWithUndo"):
            return

        selected = table.selectedIndexes()
        if not selected:
            return

        top_left = selected[0].row(), selected[0].column()
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        rows = text.strip().split('\n')
        data = [r.split('\t') for r in rows]

        for i, row in enumerate(data):
            for j, value in enumerate(row):
                r = top_left[0] + i
                c = top_left[1] + j
                index = model.index(r, c)
                model.setDataWithUndo(index, value, self.undo_stack)

    def cut_selection(self):
        self.copy_selection()  # сначала копируем
        self.delete_selection()  # потом удаляем выделенное

    def delete_selection(self):
        table = self.get_current_table_view()
        if table is None or not table.hasFocus():
            return
        selection = table.selectionModel().selectedIndexes()
        model = table.model()
        for index in selection:
            if index.isValid():
                model.setDataWithUndo(index, "", self.undo_stack)

    def undo_action(self):
        if self.undo_stack.canUndo():
            self.undo_stack.undo()

    def redo_action(self):
        if self.undo_stack.canRedo():
            self.undo_stack.redo()

    def select_all(self):
        pass


    