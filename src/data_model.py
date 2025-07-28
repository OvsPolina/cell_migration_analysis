from PyQt6.QtCore import Qt, QAbstractTableModel
from PyQt6.QtGui import QUndoStack, QUndoCommand

from logs.logger import app_logger as logger


class DataModel(QAbstractTableModel):
    """
    A Qt data model for displaying and editing a pandas DataFrame in a QTableView.
    Includes support for undoable edits via QUndoStack.
    """
    def __init__(self, df):
        """
        Initialize the model with a pandas DataFrame.

        Args:
            df (pandas.DataFrame): The data to be shown in the table.
        """
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        """
        Returns the number of rows in the table.
        """
        return self._df.shape[0]

    def columnCount(self, parent=None):
        """
        Returns the number of columns in the table.
        """
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """
        Returns the data to be displayed or edited in a cell.

        Args:
            index (QModelIndex): Cell location.
            role (Qt.ItemDataRole): Display role or edit role.

        Returns:
            str | None: Cell value as string or None if not applicable.
        """
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(self._df.iat[index.row(), index.column()])
        return None
    
    def setDataWithUndo(self, index, value, undo_stack):
        """
        Set the data at the given index using an undoable command.

        Args:
            index (QModelIndex): Target cell.
            value (str): New value to set.
            undo_stack (QUndoStack): Undo stack to store the operation.

        Returns:
            bool: True if value changed and command pushed, False otherwise.
        """
        if index.isValid():
            old_value = self._df.iat[index.row(), index.column()]
            if old_value != value:
                command = EditCellCommand(self, index, old_value, value)
                undo_stack.push(command)
                return True
        return False

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """
        Directly set data at the specified index.

        Args:
            index (QModelIndex): Target cell.
            value (str): New value.
            role (Qt.ItemDataRole): Role (should be EditRole).

        Returns:
            bool: True if data was updated, False otherwise.
        """
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
        """
        Returns a copy of the underlying DataFrame.

        Returns:
            pandas.DataFrame: Copy of internal data.
        """
        return self._df.copy()
    

class EditCellCommand(QUndoCommand):
    """
    Command object representing an editable cell change,
    used with QUndoStack to support undo/redo functionality.
    """
    def __init__(self, model, index, old_value, new_value):
        """
        Create an undoable cell edit command.

        Args:
            model (DataModel): The data model where the change happens.
            index (QModelIndex): Target cell.
            old_value (str): Previous value.
            new_value (str): New value.
        """
        super().__init__()
        self.model = model
        self.index = index
        self.old_value = old_value
        self.new_value = new_value

    def undo(self):
        """
        Undo the cell edit by restoring the old value.
        """
        self.model.setData(self.index, self.old_value)

    def redo(self):
        """
        Redo the cell edit by setting the new value again.
        """
        self.model.setData(self.index, self.new_value)
