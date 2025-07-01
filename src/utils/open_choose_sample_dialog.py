from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow

from PyQt6.QtWidgets import (
    QDialog, QTreeWidgetItem, QWidget
)

def open_choose_samples_dialog(widget: QWidget):
        dialog = QDialog(widget)
        ui = Ui_ChooseSampleWindow()
        ui.setupUi(dialog)
        widget.selected_samples = []

        if widget.ui.treeWidget:
            ui.treeWidget.clear()
            stack = []

            # Клонируем верхний уровень
            for i in range(widget.ui.treeWidget.topLevelItemCount()):
                src_item = widget.ui.treeWidget.topLevelItem(i)
                cloned_item = QTreeWidgetItem([src_item.text(0)])
                ui.treeWidget.addTopLevelItem(cloned_item)
                stack.append((src_item, cloned_item))

            # Обход в ширину
            while stack:
                src_parent, cloned_parent = stack.pop(0)
                for j in range(src_parent.childCount()):
                    src_child = src_parent.child(j)
                    cloned_child = QTreeWidgetItem([src_child.text(0)])
                    cloned_parent.addChild(cloned_child)
                    stack.append((src_child, cloned_child))
            
            
            for i in range(ui.treeWidget.topLevelItemCount()):
                ui.treeWidget.topLevelItem(i).setExpanded(True)

            # Запускаем диалог и ждем результата
            if dialog.exec() == QDialog.DialogCode.Accepted:
                for item in ui.treeWidget.selectedItems():
                    if item.parent() is not None:  # это лист (имеет родителя)
                        file_path = item.parent().text(0)
                        sheet_name = item.text(0)
                        widget.selected_samples.append([file_path, sheet_name])
            else:
                return None