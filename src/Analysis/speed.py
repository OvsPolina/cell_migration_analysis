from ui.configuration.configuration_autocorrelation_window import Ui_ConfigurationAutocorrelationWindow
from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow
from ui.plot.plot_window import Ui_Plot
from src.data_model import DataModel
from src.Plot.plot import PlotDialog
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QDialog, QMessageBox, QTreeWidgetItem, QTabWidget, QVBoxLayout
)

class UISpeed(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.speed_data_by_condition = []
        self.ui.actionSpeed.triggered.connect(self.open_dialog)

    def open_dialog(self):
        dialog = QDialog(self)
        ui = Ui_ConfigurationAutocorrelationWindow()
        ui.setupUi(dialog)
        ui.lineEdit_n_plot_points.setDisabled(True)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.open_choose_samples_dialog()
            self.values = self._read_values(ui)
            if self.values is not None:
                self.run_speed()
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

    def run_speed(self):
        if self.values['time_interval'] == 0:
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
            data_model = table.model()
            if not hasattr(data_model, "get_dataframe"):
                continue

            original_df = data_model.get_dataframe()
            data = self.treat_data(original_df)
            if data is None:
                continue

            # Speed data
            speed_data = self.speed(data)
            self.speed_data_by_condition.append((speed_data, f"{filename[1]}"))

            #Update table in tab:
            new_model = DataModel(speed_data)
            table.setModel(new_model)

        # create plot
        dialog = PlotDialog(self, title="MSD Plot")
        dialog.show_plot(self.plot_speed)
        #self.plot_speed()

    def treat_data(self, df):
        # Считать в pandas DataFrame
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
    
    def speed(self, data):
        calculate_dxdy = False
        calculate_time = False
        calculate_dbp = False
        calculate_speed = False

        if 'ΔX' not in data.columns or 'ΔY' not in data.columns:
            data['ΔX'] = np.nan
            data['ΔY'] = np.nan
            calculate_dxdy = True
        
        if 'time' not in data.columns:
            data['time'] = np.nan
            calculate_time = True

        if 'distance_bw_points' not in data.columns:
            data['distance_bw_points'] = np.nan
            calculate_dbp = True

        if 'instant_speed' not in data.columns:
            data["instant_speed"] = np.nan
            calculate_speed = True
            
        data["avg_speed_by_cell"] = np.nan
        data["avg_speed_of_condition"] = np.nan

        avg_speeds = []

        for track_id in sorted(data["Track n"].unique()):
            track_df = data[data["Track n"] == track_id].sort_values("Slice n")

            if calculate_dxdy:
                track_df['ΔX'] = track_df['X'].diff()
                track_df['ΔY'] = track_df['Y'].diff()
            
            if calculate_dbp:
                track_df['distance_bw_points'] = np.sqrt(track_df['ΔX']**2 + track_df['ΔY']**2)

            if calculate_time:
                track_df["time"] = track_df["Slice n"] * self.values['time_interval']

            if calculate_speed:
                dx = track_df['distance_bw_points'].to_numpy()
                dy = track_df['time'].to_numpy()
                
                track_df["instant_speed"] = dx / dy

            avg = track_df["instant_speed"].mean(skipna=True)
            avg_speeds.append(avg)
            
            # Вставляем обратно все рассчитанные колонки
            data.loc[track_df.index, ['ΔX', 'ΔY', 'distance_bw_points', 'time', 'instant_speed']] = \
                track_df[['ΔX', 'ΔY', 'distance_bw_points', 'time', 'instant_speed']]

            # Вставляем среднюю скорость в первую строку трека
            data.loc[track_df.index[0], "avg_speed_by_cell"] = avg

        if avg_speeds:
            avg = np.mean(avg_speeds)
            err = np.std(avg_speeds, ddof=1) / np.sqrt(len(avg_speeds))
            combined = f"{avg:.3f} ± {err:.3f}"

            # Запишем значение во все строки данного трека
            data.loc[0, "avg_speed_of_condition"] = combined

        return data
                    
    def plot_speed(self, ax):
        plt.figure(figsize=(10, 6))
        
        labels = []
        avg_values = []
        errors = []

        for df, label in self.speed_data_by_condition:
            value = df.get("avg_speed_of_condition", [None])[0]  # предполагается, что это строка вида "0.123 ± 0.045"

            if value:
                try:
                    avg_str, err_str = value.split("±")
                    avg = float(avg_str.strip())
                    err = float(err_str.strip())
                    labels.append(label)
                    avg_values.append(avg)
                    errors.append(err)
                except Exception as e:
                    print(f"Ошибка при обработке значения {value}: {e}")

        # Рисуем столбчатую диаграмму
        x = np.arange(len(labels))

        ax.bar(x, avg_values, yerr=errors, capsize=5, color='skyblue')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_ylabel("Average Speed")
        ax.set_title("Average Speed by Condition")
        ax.grid(True, axis='y')
