import os
from pathlib import Path
import string

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QWidget, QTableView, QTreeWidgetItem, QTabWidget, QVBoxLayout, QHeaderView
)

import pandas as pd
import pandera.pandas as pa

from logger import app_logger as logger

from src.data_model import DataModel
from src.utils.input_data import input_schema



class UIFile(QWidget):
    """
    File handling class for loading, creating, displaying, and saving Excel files.
    """
    def __init__(self, ui):
        """
        Initialize the UIFile handler.
        Args:
            ui (QMainWindow): The main UI window object.
        """
        super().__init__()
        self.ui = ui
        self.tabs_data_models = {} # Store DataModels for each sheet
        
        # Connect UI actions and tree widget signals to the appropriate handlers.
        self.ui.actionNew_File.triggered.connect(self.new_file)
        self.ui.actionOpen_File.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_as_file)
        self.ui.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

    def open_file(self):
        """
        Open and load Excel files selected by the user. Each sheet is added as a tab,
        and the file/sheet structure is displayed in a tree widget.
        """
        try:
            file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Excel File", "", "Excel files (*.xlsx *.xls *.xlsm)")
        except Exception as e:
            logger.exception(f"Could not receive file paths to open: {e}")

        if not file_paths:
            return
        
        # Display tree widget and adjust layout
        self.ui.treeWidget.show()
        total_width = self.ui.splitter.width()
        self.ui.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])

        logger.info(f"Files to open: {file_paths}")

        for file_path in file_paths:
            file_path = Path(file_path)
            try:
                # Load all sheets
                excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
                for sheet_name, df in excel_data.items():
                    try:
                        # Cast and validate required columns
                        df["Track n"] = df["Track n"].astype(float)
                        df["Slice n"] = df["Slice n"].astype(float)
                        df["X"] = df["X"].astype(float)
                        df["Y"] = df["Y"].astype(float)
                        df = df.dropna(how="all")
                        validated = input_schema.validate(df)
                        # do something with validated data if needed
                    except pa.errors.SchemaError as e:
                        logger.error(f"Not correct data in the sheet '{sheet_name}': {e}")
                        QMessageBox.critical(self, "Error", f"Not correct data in the sheet '{sheet_name}': {e}")
                logger.info(f"Opened file {file_path}")

            except Exception as e:
                logger.error(f"Cannot open the file:\n{e}")
                QMessageBox.critical(self, "Error", f"Cannot open the file:\n{e}")
                continue #skip file with error

            # Add root to the filetree
            file_root = QTreeWidgetItem([file_path.name])
            file_root.setData(0, Qt.ItemDataRole.UserRole, {"unsaved_changes": False})
            self.ui.treeWidget.addTopLevelItem(file_root)

            # Create new widget for the page and tab widget for sheets
            page = QWidget()
            page.filename = file_path
            layout = QVBoxLayout(page)
        
            tab_widget = QTabWidget()
            layout.addWidget(tab_widget)
            
            page.tree_item = file_root
            
            # Create a tab and tree item for each sheet
            for sheet_name, df in excel_data.items():
                table = QTableView()
                data_model = DataModel(df)
                table.setModel(data_model)
                table.setSortingEnabled(True)
                table.resizeColumnsToContents()

                self.tabs_data_models[sheet_name] = data_model

                tab_widget.addTab(table, sheet_name)

                # Add sheet to the tree
                sheet_item = QTreeWidgetItem([sheet_name])
                sheet_item.setData(0, Qt.ItemDataRole.UserRole, {"unsaved_changes": False})
                
                # Connect the element of the tree with the table widget and vice versa
                sheet_item.table_widget = table
                table.tree_item = sheet_item

                file_root.addChild(sheet_item)

            file_root.setExpanded(True)

            # Add page with tabs to the stackedWidget
            self.ui.stackedWidget.addWidget(page)

        # Automatically show the most recently opened file
        if self.ui.stackedWidget.count() > 0:
            self.ui.stackedWidget.setCurrentWidget(page)

    def on_tree_item_clicked(self, item):
        """
        Handle clicks on tree items to switch to the correct file tab or sheet tab.

        Args:
            item (QTreeWidgetItem): The clicked item in the tree widget.
        """
        parent = item.parent()
        if parent is None:
            # Root level: switch page
            file_name = item.text(0)
            index = self.find_stack_index_by_filename(file_name)
            if index is not None:
                self.ui.stackedWidget.setCurrentIndex(index)
        else:
            # Child level: switch to sheet tab
            index = self.find_stack_index_by_filename(parent.text(0))
            if index is not None:
                self.ui.stackedWidget.setCurrentIndex(index)
            sheet_name = item.text(0)
            tab_widget = self.ui.stackedWidget.currentWidget().findChild(QTabWidget)
            if tab_widget:
                for i in range(tab_widget.count()):
                    if tab_widget.tabText(i) == sheet_name:
                        tab_widget.setCurrentIndex(i)
                        break

    def find_stack_index_by_filename(self, filename):
        """
        Find the index in the stacked widget for a given file name.

        Args:
            filename (str): The name of the file.

        Returns:
            int | None: Index of the corresponding page in the stacked widget or None.
        """
        for i in range(self.ui.stackedWidget.count()):
            widget = self.ui.stackedWidget.widget(i)
            file_path = getattr(widget, 'filename', None)
            if file_path is not None:
                if file_path.name == filename:
                    return i
        return None

    def get_new_filename(self, base_dir, prefix="new_file_", extension=".xlsx"):
        """
        Generate a new unique filename in the given directory.

        Args:
            base_dir (str): Directory where the new file will be created.
            prefix (str): Prefix for the new file name.
            extension (str): File extension.

        Returns:
            str: Path to the new file.
        """
        existing = os.listdir(base_dir)
        used_numbers = set()

        for name in existing:
            if name.startswith(prefix) and name.endswith(extension):
                num_part = name[len(prefix):-len(extension)].strip()
                if num_part.isdigit():
                    used_numbers.add(int(num_part))

        # Find the minimal free number
        for i in range(1, len(used_numbers) + 2):
            if i not in used_numbers:
                logger.info(f"New temporary file was created: {os.path.join(base_dir, f"{prefix}{i}{extension}")}")
                return os.path.join(base_dir, f"{prefix}{i}{extension}")
    
    def new_file(self):
        """
        Create a new empty Excel file with a single blank sheet and load it into the UI.
        """
        try:
            temp_dir = os.path.join(os.getcwd(), "tmp")
            os.makedirs(temp_dir, exist_ok=True)
            new_file_path = Path(self.get_new_filename(temp_dir))

            # Create empty DataFrame
            columns = list(string.ascii_uppercase)
            empty_df = pd.DataFrame('', index=range(1000), columns=columns)

            # Save as Excel
            with pd.ExcelWriter(new_file_path, engine='openpyxl') as writer:
                empty_df.to_excel(writer, sheet_name='Sheet1', index=False)

        except Exception as e:
            logger.error(f"Cannot create new file:\n{e}")
            QMessageBox.critical(self, "Error", f"Cannot create new file:\n{e}")
            return

        # Show and adjust the tree
        self.ui.treeWidget.show()
        total_width = self.ui.splitter.width()
        self.ui.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])
        file_root = QTreeWidgetItem([new_file_path.name])
        self.ui.treeWidget.addTopLevelItem(file_root)

        # Create page and tab
        page = QWidget()
        page.filename = new_file_path
        layout = QVBoxLayout(page)
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Create TableView and model
        table_view = QTableView()
        data_model = DataModel(empty_df)
        table_view.setModel(data_model)
        table_view.setSortingEnabled(True)
        table_view.resizeColumnsToContents()
        table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table_view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        table_view.horizontalHeader().setStretchLastSection(True)

        tab_widget.addTab(table_view, "Sheet1")

        self.tabs_data_models["Sheet1"] = data_model

        # Add to the tree
        sheet_item = QTreeWidgetItem(["Sheet1"])
        sheet_item.setData(0, Qt.ItemDataRole.UserRole, {"unsaved_changes": False})
        file_root.addChild(sheet_item)
        file_root.setExpanded(True)

        # Add to the page
        self.ui.stackedWidget.addWidget(page)
        self.ui.stackedWidget.setCurrentWidget(page)

        logger.info(f"New file {new_file_path.name} was created and added to the widgets.")

    def save_file(self):
        """
        Save the currently active file. If it's a temporary file, prompt for a new file path.
        """
        page = self.ui.stackedWidget.currentWidget()
        if not hasattr(page, "filename"):
            logger.warning(f"No file associated with the page {page}")
            QMessageBox.warning(self, "Warning", "No file associated with this page.")
            return

        file_path = page.filename 
        temp_dir = Path.cwd() / "tmp"

        if temp_dir in file_path.parents:
            # If file is from temp directory, ask user to save as a new file
            self.save_as_file()
            try:
                file_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Warning: could not delete temp file: {e}")
            return
        else:
            self._save_page_to_file(page, file_path)

        # Reset unsaved change flags in the tree
        tree_item = getattr(page, "tree_item", None)
        if tree_item is not None:
            # Change flag for root
            data = tree_item.data(0, Qt.ItemDataRole.UserRole) or {}
            data["unsaved_changes"] = False
            tree_item.setData(0, Qt.ItemDataRole.UserRole, data)

            # Change flag for children of the root
            for i in range(tree_item.childCount()):
                child = tree_item.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole) or {}
                data["unsaved_changes"] = False
                child.setData(0, Qt.ItemDataRole.UserRole, data)

    def save_as_file(self):
        """
        Save the current page to a new file path chosen by the user.
        """
        page = self.ui.stackedWidget.currentWidget()
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save As", "", "Excel files (*.xlsx *.xls)"
            )
        except Exception as e:
            logger.warning(f"Could not create a file_path : {e}")
            QMessageBox.warning(self, "Warning", f"Could not create a file_path : {e}")
            return

        # Update file path
        file_path = Path(file_path)
        page.filename = file_path
        self._save_page_to_file(page, file_path)

    def _save_page_to_file(self, page, file_path):
        """
        Save the content of a page (with multiple sheet tabs) to an Excel file.

        Args:
            page (QWidget): The UI page representing the file.
            file_path (Path): Destination path to save the Excel file.
        """
        try:
            tab_widget = page.findChild(QTabWidget)
            if not tab_widget:
                logger.error("_save_page_to_file : Tab widget not found.")

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for i in range(tab_widget.count()):
                    table_view = tab_widget.widget(i)
                    model = table_view.model()
                    df = model.get_dataframe()
                    sheet_name = tab_widget.tabText(i)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        except Exception as e:
            logger.critical(f"Failed to save file:\n{e}")
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
