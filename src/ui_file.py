import os
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog, QMessageBox, QWidget, QTableView, QTreeWidgetItem, QTabWidget, QVBoxLayout, QHeaderView
)
import pandas as pd
import string
import pandera.pandas as pa

from src.data_model import DataModel
from src.utils.input_data import input_schema

class UIFile(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.tabs_data_models = {}
        self._connect_signals()

    def _connect_signals(self):
        self.ui.actionNew_File.triggered.connect(self.new_file)
        self.ui.actionOpen_File.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_as_file)
        self.ui.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

    def open_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Excel File", "", "Excel files (*.xlsx *.xls *.xlsm)")
        if not file_paths:
            return
        
        self.ui.treeWidget.show()
        total_width = self.ui.splitter.width()
        self.ui.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])

        for file_path in file_paths:
            file_path = Path(file_path)
            try:
                excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
                for sheet_name, df in excel_data.items():
                    try:
                        df["Track n"] = df["Track n"].astype(float)
                        df["Slice n"] = df["Slice n"].astype(float)
                        df["X"] = df["X"].astype(float)
                        df["Y"] = df["Y"].astype(float)
                        df = df.dropna(how="all")
                        validated = input_schema.validate(df)
                        # do something with validated data if needed
                    except pa.errors.SchemaError as e:
                        QMessageBox.critical(self, "Error", f"Not correct data in the sheet '{sheet_name}': {e}")

            except Exception as e:
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
            
            # Add sheets
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
                # Связываем элемент дерева с таблицей (виджетом)
                sheet_item.table_widget = table

                # И наоборот — сохраняем в таблице ссылку на элемент дерева
                table.tree_item = sheet_item
                file_root.addChild(sheet_item)

            file_root.setExpanded(True)

            # Add page with tabs to the stackedWidget
            self.ui.stackedWidget.addWidget(page)

        # Go to the last added page
        if self.ui.stackedWidget.count() > 0:
            self.ui.stackedWidget.setCurrentWidget(page)

    def on_tree_item_clicked(self, item):
        parent = item.parent()
        if parent is None:
            # Кликнули по файлу — найдем индекс стэка с этим файлом
            file_name = item.text(0)
            index = self.find_stack_index_by_filename(file_name)
            if index is not None:
                self.ui.stackedWidget.setCurrentIndex(index)
        else:
            # Кликнули по листу — переключаем вкладку в табе текущего стэка
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
        # Пример функции — ты должен реализовать, как хранишь соответствие
        for i in range(self.ui.stackedWidget.count()):
            widget = self.ui.stackedWidget.widget(i)
            file_path = getattr(widget, 'filename', None)
            if file_path is not None:
                # file_path — объект Path, filename — строка из дерева (только имя файла)
                if file_path.name == filename:
                    return i
        return None

    def get_new_filename(self, base_dir, prefix="new_file_", extension=".xlsx"):
        existing = os.listdir(base_dir)
        used_numbers = set()

        for name in existing:
            if name.startswith(prefix) and name.endswith(extension):
                num_part = name[len(prefix):-len(extension)].strip()
                if num_part.isdigit():
                    used_numbers.add(int(num_part))

        # Найти минимальный свободный номер
        for i in range(1, len(used_numbers) + 2):
            if i not in used_numbers:
                return os.path.join(base_dir, f"{prefix}{i}{extension}")
    
    def new_file(self):
        try:
            temp_dir = os.path.join(os.getcwd(), "tmp")
            os.makedirs(temp_dir, exist_ok=True)
            new_file_path = self.get_new_filename(temp_dir)
            new_file_path = Path(new_file_path)
            # создаем пустой DataFrame
            columns = list(string.ascii_uppercase)
            empty_df = pd.DataFrame('', index=range(1000), columns=columns)

            # сохраняем в Excel
            with pd.ExcelWriter(new_file_path, engine='openpyxl') as writer:
                empty_df.to_excel(writer, sheet_name='Sheet1', index=False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot create new file:\n{e}")
            return

        # Показываем и настраиваем дерево
        self.ui.treeWidget.show()
        total_width = self.ui.splitter.width()
        self.ui.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])
        file_root = QTreeWidgetItem([new_file_path.name])
        self.ui.treeWidget.addTopLevelItem(file_root)

        # Создаем страницу и таб
        page = QWidget()
        page.filename = new_file_path
        layout = QVBoxLayout(page)
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Создаем TableView и модель
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

        # дерево: лист
        sheet_item = QTreeWidgetItem(["Sheet1"])
        sheet_item.setData(0, Qt.ItemDataRole.UserRole, {"unsaved_changes": False})
        file_root.addChild(sheet_item)
        file_root.setExpanded(True)

        # добавляем страницу
        self.ui.stackedWidget.addWidget(page)
        self.ui.stackedWidget.setCurrentWidget(page)

    def save_file(self):
        page = self.ui.stackedWidget.currentWidget()
        if not hasattr(page, "filename"):
            QMessageBox.warning(self, "Warning", "No file associated with this page.")
            return

        file_path = page.filename  # объект Path
        temp_dir = Path.cwd() / "tmp"

        if temp_dir in file_path.parents:
            # Если временный файл — вызываем Save As
            self.save_as_file()
            try:
                file_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Warning: could not delete temp file: {e}")
            return
        else:
            self._save_page_to_file(page, file_path)

        # После успешного сохранения меняем флаг у всех дочерних элементов дерева файла
        tree_item = getattr(page, "tree_item", None)
        if tree_item is not None:
            # Сам файл — корень, выставляем флаг тоже
            data = tree_item.data(0, Qt.ItemDataRole.UserRole) or {}
            data["unsaved_changes"] = False
            tree_item.setData(0, Qt.ItemDataRole.UserRole, data)

            # Пройдемся по всем листам (дочерним элементам)
            for i in range(tree_item.childCount()):
                child = tree_item.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole) or {}
                data["unsaved_changes"] = False
                child.setData(0, Qt.ItemDataRole.UserRole, data)

    def save_as_file(self):
        page = self.ui.stackedWidget.currentWidget()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", "Excel files (*.xlsx *.xls)"
        )
        if not file_path:
            return
        file_path = Path(file_path)

        # Обновляем путь файла
        page.filename = file_path
        self._save_page_to_file(page, file_path)

    def _save_page_to_file(self, page, file_path):
        try:
            tab_widget = page.findChild(QTabWidget)
            if not tab_widget:
                raise Exception("Tab widget not found.")

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for i in range(tab_widget.count()):
                    table_view = tab_widget.widget(i)
                    model = table_view.model()
                    if not hasattr(model, 'get_dataframe'):
                        raise Exception("Model does not implement get_dataframe().")
                    df = model.get_dataframe()
                    sheet_name = tab_widget.tabText(i)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
