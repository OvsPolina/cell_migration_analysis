from ui.configuration.configuration_autocorrelation_window import Ui_ConfigurationAutocorrelationWindow
from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow
from ui.plot.plot_window import Ui_Plot
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QDialog, QMessageBox, QTreeWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
)

class UIAutocorrelation(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.ui.actionAutocorrelation.triggered.connect(self.open_dialog)

    def open_dialog(self):
        dialog = QDialog(self)
        ui = Ui_ConfigurationAutocorrelationWindow()
        ui.setupUi(dialog)
        self.all_scalar_data = []
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.open_choose_samples_dialog()
            self.values = self._read_values(ui)
            if self.values is not None:
                self.run_autocorrelation()
        else:
            return None

    def _read_values(self, ui):
        try:
            time_interval = float(ui.lineEdit_time_interval.text())
            n_time_points = int(ui.lineEdit_n_time_points.text())
            n_tracks = int(ui.lineEdit_n_tracks.text())
            n_plot_points = int(ui.lineEdit_n_plot_points.text())
            return {
                "time_interval": time_interval,
                "n_time_points": n_time_points,
                "n_tracks": n_tracks,
                "n_plot_points": n_plot_points
            }
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректные числовые значения.")
            return None

    def open_choose_samples_dialog(self):
        dialog = QDialog(self)
        ui = Ui_ChooseSampleWindow()
        ui.setupUi(dialog)
        self.selected_samples = []

        if self.ui.treeWidget:
            ui.treeWidget.clear()
            stack = []

            # Клонируем верхний уровень
            for i in range(self.ui.treeWidget.topLevelItemCount()):
                src_item = self.ui.treeWidget.topLevelItem(i)
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
                        self.selected_samples.append([file_path, sheet_name])
            else:
                return None

    def run_autocorrelation(self):
        if self.values['time_interval'] == 0 or self.values['n_plot_points'] == 0:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректные числовые значения.")


        for filename in self.selected_samples:

            # Find sheet
            index = None
            for i in range(self.ui.stackedWidget.count()):
                widget = self.ui.stackedWidget.widget(i)
                if getattr(widget, 'filename', None) == filename[0]:
                    index = i
            
            if index is not None:
                    self.ui.stackedWidget.setCurrentIndex(index)
            tab_widget = self.ui.stackedWidget.currentWidget().findChild(QTabWidget)
            if tab_widget:
                for i in range(tab_widget.count()):
                    if tab_widget.tabText(i) == filename[1]:
                        tab_widget.setCurrentIndex(i)
                        break
            
            table = tab_widget.widget(i)

            data = self.treat_data(table)

            # Normalised vector
            norm_data = self.norm(data)

            # Average Scalars
            scalar_data = self.scalars(norm_data)
            self.all_scalar_data.append((scalar_data, f"{filename[1]}"))

            #Update table in tab:
            table.clear()
            table.setRowCount(scalar_data.shape[0])
            table.setColumnCount(scalar_data.shape[1])
            table.setHorizontalHeaderLabels([str(col) for col in scalar_data.columns])

            for i in range(scalar_data.shape[0]):
                for j in range(scalar_data.shape[1]):
                    value = str(scalar_data.iat[i, j]) if pd.notna(scalar_data.iat[i, j]) else ""
                    table.setItem(i, j, QTableWidgetItem(value))

        # Create Statistics

        # create plot
        self.plot_scalar_averages()

    def treat_data(self, table):
        # Считать в pandas DataFrame
        data = []
        headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
            if any(cell.strip() != "" for cell in row_data):  # Игнорировать пустые строки
                data.append(row_data)

        df = pd.DataFrame(data, columns=headers)

        try:
            df["Track n"] = df["Track n"].astype(int)
            df["Slice n"] = df["Slice n"].astype(int)
            df["X"] = pd.to_numeric(df["X"], errors='coerce')
            df["Y"] = pd.to_numeric(df["Y"], errors='coerce')
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось преобразовать столбцы Track n или Slice n в числа:\n{e}")
            return None

        # Обработка треков
        cleaned_rows = []
        missing_tracks = []
        for track_id in sorted(df["Track n"].unique()):
            track_df = df[df["Track n"] == track_id].sort_values("Slice n")
            if len(track_df) < self.values['n_time_points']:
                missing_tracks.append(track_id)
            else:
                cleaned_rows.append(track_df.iloc[:self.values['n_time_points']])
                #cleaned_rows.append(pd.DataFrame([[""] * len(df.columns)], columns=df.columns))  # Пустая строка

        result_df = pd.concat(cleaned_rows, ignore_index=True)

        # Проверка количества треков
        if len(df["Track n"].unique()) != self.values['n_tracks']:
            QMessageBox.warning(self, "Предупреждение", f"Ожидалось {self.values['n_tracks']} треков, но найдено {len(df['Track n'].unique())}.")

        if missing_tracks:
            QMessageBox.warning(self, "Недостаточно слайсов", f"У следующих треков меньше {self.values['n_time_points']} слайсов: {missing_tracks}")

        return result_df
    
    def norm(self, data):
        data['ΔX'] = data['X'].diff()
        data['ΔY'] = data['Y'].diff()

        # Вычисляем длину вектора
        data['magnitude'] = np.sqrt(data['ΔX']**2 + data['ΔY']**2)
        data['magnitude'] = data['magnitude'].replace(0, np.nan)

        # Косинус и синус угла относительно оси X
        data['cos_theta'] = data['ΔX'] / data['magnitude']
        data['sin_theta'] = data['ΔY'] / data['magnitude']

        return data
    
    def scalars(self, data):
        for step in range(1, self.values['n_plot_points'] + 1):
            time_label = f"time_{step * self.values['time_interval']}"
            col_name = f"scalar_{time_label}"
            
            # Инициализируем колонку
            data[col_name] = np.nan

            for track_id in sorted(data["Track n"].unique()):
                track_df = data[data["Track n"] == track_id].sort_values("Slice n").reset_index()

                dx = track_df['cos_theta'].to_numpy()
                dy = track_df['sin_theta'].to_numpy()
                scalars = []

                for i in range(len(track_df) - step):
                    v1 = np.array([dx[i], dy[i]])
                    v2 = np.array([dx[i + step], dy[i + step]])

                    if np.any(np.isnan(v1)) or np.any(np.isnan(v2)):
                        continue

                    scalar = np.dot(v1, v2)
                    scalars.append(scalar)

            if scalars:
                avg = np.mean(scalars)
                err = np.std(scalars, ddof=1) / np.sqrt(len(scalars))
                combined = f"{avg:.3f} ± {err:.3f}"

                # Запишем значение во все строки данного трека
                data.loc[0, col_name] = combined

        return data
                    
    def plot_scalar_averages(self):
        dialog = QDialog(self)
        ui = Ui_Plot()
        ui.setupUi(dialog)

        # Создаем Figure и Canvas
        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)

        plt.figure(figsize=(10, 6))
        
        for df, label in self.all_scalar_data:
            time_points = []
            scalar_values = []

            for col in df.columns:
                if col.startswith("scalar_time_"):
                    match = re.search(r"scalar_time_(\d+)", col)
                    if match:
                        time_point = int(match.group(1))
                        time_points.append(time_point)

                        vals = df[col].dropna().unique()

                        scalars = []
                        for val in vals:
                            try:
                                avg_str = val.split("±")[0].strip()
                                scalars.append(float(avg_str))
                            except:
                                continue

                        scalar_values.append(np.mean(scalars) if scalars else np.nan)

            # Сортировка по времени
            sorted_pairs = sorted(zip(time_points, scalar_values))
            sorted_times, sorted_scalars = zip(*sorted_pairs)

            ax.plot(sorted_times, sorted_scalars, marker='o', label=label)

        ax.set_xlabel("Time (step × interval)")
        ax.set_ylabel("Average Scalar Product")
        ax.set_title("Autocorrelation Scalar Averages")
        ax.grid(True)
        ax.legend()

        # Вставляем канвас в UI
        layout = QVBoxLayout(ui.widget)
        layout.addWidget(canvas)

        dialog.exec()
