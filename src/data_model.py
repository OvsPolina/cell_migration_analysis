from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QUndoStack, QUndoCommand


class DataModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(self._df.iat[index.row(), index.column()])
        return None
    
    def setDataWithUndo(self, index, value, undo_stack):
        if index.isValid():
            old_value = self._df.iat[index.row(), index.column()]
            if old_value != value:
                command = EditCellCommand(self, index, old_value, value)
                undo_stack.push(command)
                return True
        return False

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            self._df.iat[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            elif orientation == Qt.Orientation.Vertical:
                return str(self._df.index[section])
        return None

    def get_dataframe(self):
        return self._df.copy()
    

class EditCellCommand(QUndoCommand):
    def __init__(self, model, index, old_value, new_value):
        super().__init__()
        self.model = model
        self.index = index
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        self.model.setData(self.index, self.old_value)

    def redo(self):
        self.model.setData(self.index, self.new_value)
