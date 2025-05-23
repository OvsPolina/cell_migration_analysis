import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QTableWidget, QTableWidgetItem, QTreeWidgetItem, QTabWidget, QVBoxLayout, QHeaderView
)
import pandas as pd
import string

class UIFile(QWidget):
    def __init__(self, ui):
        super().__init__()  # нужно вызвать, чтобы QWidget инициализировался корректно
        self.ui = ui
        self._connect_signals()

    def _connect_signals(self):
        self.ui.actionNew_File.triggered.connect(self.new_file)
        self.ui.actionOpen_File.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_as.triggered.connect(self.save_as_file)
        self.ui.treeWidget.itemClicked.connect(self.on_tree_item_clicked)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel files (*.xlsx *.xls, *.xlsm)")
        if not file_path:
            return

        try:
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open the file:\n{e}")
            return

        # Добавляем новый корневой элемент в дерево для файла
        self.ui.treeWidget.show()
        total_width = self.ui.splitter.width()
        self.ui.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])
        file_root = QTreeWidgetItem([file_path])
        self.ui.treeWidget.addTopLevelItem(file_root)

        # Создаем новый виджет страницы и таб виджет для листов
        page = QWidget()
        page.filename = file_path
        layout = QVBoxLayout(page)  # Внутренний layout для страницы
    
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Добавляем вкладки с листами
        for sheet_name, df in excel_data.items():
            table = QTableWidget()
            table.setRowCount(df.shape[0])
            table.setColumnCount(df.shape[1])
            table.setHorizontalHeaderLabels(df.columns.astype(str).to_list())

            for row in range(df.shape[0]):
                for col in range(df.shape[1]):
                    item = QTableWidgetItem(str(df.iat[row, col]))
                    table.setItem(row, col, item)

            tab_widget.addTab(table, sheet_name)

            # Добавляем лист в дерево
            sheet_item = QTreeWidgetItem([sheet_name])
            file_root.addChild(sheet_item)

        file_root.setExpanded(True)

        # Добавляем страницу с табами в stackedWidget
        self.ui.stackedWidget.addWidget(page)

        # Переключаемся на только что добавленную страницу (индекс -1 - последний)
        self.ui.stackedWidget.setCurrentWidget(page)

    def on_tree_item_clicked(self, item, column):
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
            # допустим, у каждого виджета есть property с именем файла
            if getattr(widget, 'filename', None) == filename:
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
            temp_dir = os.path.join(os.getcwd(), "temp")
            new_file_path = self.get_new_filename(temp_dir)
            empty_df = pd.DataFrame()
            with pd.ExcelWriter(new_file_path, engine='openpyxl') as writer:
                empty_df.to_excel(writer, sheet_name='Sheet1', index=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot create new file:\n{e}")
            return

        # Добавляем новый корневой элемент в дерево для файла
        self.ui.treeWidget.show()
        total_width = self.ui.splitter.width()
        self.ui.splitter.setSizes([int(total_width * 0.3), int(total_width * 0.7)])
        file_root = QTreeWidgetItem([new_file_path])
        self.ui.treeWidget.addTopLevelItem(file_root)

        # Создаем новый виджет страницы и таб виджет для листов
        page = QWidget()
        page.filename = new_file_path
        layout = QVBoxLayout(page)  # Внутренний layout для страницы
    
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        table = QTableWidget()
        table.setRowCount(1000)
        columns = list(string.ascii_uppercase)
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        table.setShowGrid(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        table.horizontalHeader().setStretchLastSection(True)

        tab_widget.addTab(table, "Sheet1")

        # Добавляем лист в дерево
        sheet_item = QTreeWidgetItem(["Sheet1"])
        file_root.addChild(sheet_item)

        file_root.setExpanded(True)

        # Добавляем страницу с табами в stackedWidget
        self.ui.stackedWidget.addWidget(page)

        # Переключаемся на только что добавленную страницу (индекс -1 - последний)
        self.ui.stackedWidget.setCurrentWidget(page)

    def save_file(self):
        pass

    def save_as_file(self):
        pass
