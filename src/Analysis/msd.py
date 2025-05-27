from ui.configuration.configuration_autocorrelation_window import Ui_ConfigurationAutocorrelationWindow
from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow
from ui.plot.plot_window import Ui_Plot
from src.Plot.plot import PlotDialog
from src.data_model import DataModel
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QWidget, QDialog, QMessageBox, QTreeWidgetItem, QTabWidget, QVBoxLayout
)

class UIMSD(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.avg_msd_data = []
        self.ui.actionMSD.triggered.connect(self.open_dialog)

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
                self.run_msd()
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

    def run_msd(self):
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

            # MSD
            msd_data = self.msd(data)
            self.avg_msd_data.append((msd_data, f"{filename[1]}"))

            #Update table in tab:
            # Обновляем модель
            new_model = DataModel(msd_data)
            table.setModel(new_model)

        # create plot
        dialog = PlotDialog(self, title="MSD Plot")
        dialog.show_plot(self.plot_msd)
        #self.plot_msd()

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
    
    def msd(self, data):
        data['time'] = np.nan
        data['avg_msd_by_time_cell'] = np.nan
        data["avg_msd_by_time_condition"] = np.nan
        data["sem_by_time_condition"] = np.nan

        avr_msd = []

        for track_id in sorted(data["Track n"].unique()):
            track_df = data[data["Track n"] == track_id].sort_values("Slice n")

            track_df['time'] = track_df['Slice n'] * self.values['time_interval']
            data.loc[track_df.index, 'time'] = track_df["time"].values

            # Calculate MSD
            msd = np.zeros(self.values['n_time_points'])

            dx = track_df['X'].to_numpy()
            dy = track_df['Y'].to_numpy()

            for tau in range(1, self.values['n_time_points']):
                displacements = (dx[tau:] - dx[:-tau])**2 + (dy[tau:] - dy[:-tau])**2
                msd[tau] = np.mean(displacements)

            track_df['avg_msd_by_time_cell'] = msd
            data.loc[track_df.index, 'avg_msd_by_time_cell'] = track_df["avg_msd_by_time_cell"].values
            
            avr_msd.append(msd)

        if avr_msd:
            avr_msd = np.array(avr_msd)
            avg = np.mean(avr_msd, axis=0)
            err = np.std(avr_msd, axis=0, ddof=1) / np.sqrt(avr_msd.shape[0])
            data.loc[:self.values['n_time_points']-1, "avg_msd_by_time_condition"] = avg
            data.loc[:self.values['n_time_points']-1, "sem_by_time_condition"] = err

        return data
                    
    def plot_msd(self, ax):
        # Для каждого набора данных
        for df, label in self.avg_msd_data:
            if 'avg_msd_by_time_condition' not in df.columns or 'sem_by_time_condition' not in df.columns:
                continue  # Пропускаем, если нет нужных колонок

            # Предполагается, что есть n строк с msd_avg и msd_err
            y = df['avg_msd_by_time_condition'].dropna().values
            yerr = df['sem_by_time_condition'].dropna().values
            x = np.arange(len(y)) * self.values['time_interval']  # временная шкала

            ax.errorbar(x, y, yerr=yerr, fmt='o-', capsize=4, label=label)

        ax.set_xlabel("Time (step × interval)")
        ax.set_ylabel("Mean Squared Displacement (MSD)")
        ax.set_title("MSD with SEM")
        ax.grid(True)
        ax.legend()
