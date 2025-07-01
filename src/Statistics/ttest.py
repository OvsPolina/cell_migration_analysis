from ui.configuration.configuration_autocorrelation_window import Ui_ConfigurationAutocorrelationWindow
from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow
from ui.stats.result_window import Ui_StatsWindow
from src.data_model import DataModel
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.stats import shapiro
from scipy.stats import ttest_ind, mannwhitneyu

from PyQt6.QtWidgets import (
    QWidget, QDialog, QMessageBox, QTreeWidgetItem, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
)

class UITTest(QWidget):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.ui.actionTtest.triggered.connect(self.run)

    def run(self):
        self.open_choose_samples_dialog()
        self.pretreat_data()
        if self.check_norm_dist():
            self.run_ttest()

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

    def pretreat_data(self):
        cells = []

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
            data = data_model.get_dataframe()
            if data is None:
                continue

            for track_id in sorted(data["Track n"].unique()):
                track_df = data[data["Track n"] == track_id].sort_values("Slice n")

                track_df['time'] = track_df['Slice n'] * 10
                dx = track_df['X'].to_numpy()
                dy = track_df['Y'].to_numpy()

                track_df['ΔX'] = track_df['X'].diff()
                track_df['ΔY'] = track_df['Y'].diff()

                track_df['distance_bw_points'] = np.sqrt(track_df['ΔX']**2 + track_df['ΔY']**2)

                # Calculate MSD
                msd = np.zeros(3)
                for tau in range(1, 3):
                    displacements = (dx[tau:] - dx[:-tau])**2 + (dy[tau:] - dy[:-tau])**2
                    msd[tau] = np.mean(displacements)
                avg_msd_1 = np.mean(msd[1:])

                # Calculate Speed
                track_df["instant_speed"] = track_df['distance_bw_points'].to_numpy() / track_df['time'].to_numpy()
                avg_speed = track_df["instant_speed"].mean(skipna=True)

                # Calculate Directionality
                track_df['Δ(xi-x0)'] = dx - dx[0]
                track_df['Δ(yi-y0)'] = dy - dy[0]

                track_df['distance_to_start'] = np.sqrt(track_df['Δ(xi-x0)']**2 + track_df['Δ(yi-y0)']**2)
                track_df['cumulative_distance'] = track_df['distance_bw_points'].fillna(0).cumsum()

                track_df["dir_ratio"] = track_df["distance_to_start"] / track_df["cumulative_distance"]
                track_df["dir_ratio"] = track_df["dir_ratio"].replace([np.inf, -np.inf], np.nan)
                avg_dir = track_df['dir_ratio'].mean(skipna=True)

                # Calculate Autocorrelation
                track_df['magnitude'] = np.sqrt(track_df['ΔX']**2 + track_df['ΔY']**2)
                track_df['cos_theta'] = track_df['ΔX'] / track_df['magnitude']
                track_df['sin_theta'] = track_df['ΔY'] / track_df['magnitude']

                dx = track_df['cos_theta'].to_numpy()
                dy = track_df['sin_theta'].to_numpy()
                avg_scalars = []
                for step in range(1, 7):
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
                        avg_scalars.append(avg)

                cells.append({
                    'cell_id': track_id,
                    'condition': filename[1],
                    'mean_speed': avg_speed,
                    'msd': avg_msd_1,
                    'directionality': avg_dir,
                    'autocorr': np.mean(avg_scalars)
                })

        self.cell_data = pd.DataFrame(cells)

    def check_norm_dist(self):
        stat, p = shapiro(self.cell_data['autocorr'])
        if p > 0.05:
            return True
        return False

    def run_ttest(self):
        conditions = self.cell_data['condition'].unique()

        # Создаём пустой датафрейм для p-value
        pval_df = pd.DataFrame(index=conditions, columns=conditions, dtype=float)   

        # Перебираем все пары
        for i, cond1 in enumerate(conditions):
            for j, cond2 in enumerate(conditions):
                if i == j:
                    pval_df.loc[cond1, cond2] = None  # или np.nan, т.к. сравниваем с самим собой
                elif i < j:
                    data1 = self.cell_data[self.cell_data['condition'] == cond1]['mean_speed']
                    data2 = self.cell_data[self.cell_data['condition'] == cond2]['mean_speed']
                    
                    stat, p = mannwhitneyu(data1, data2)
                    
                    pval_df.loc[cond1, cond2] = p
                    pval_df.loc[cond2, cond1] = p  # заполняем симметрично    

        
        dialog = QDialog(self)
        ui = Ui_StatsWindow()
        ui.setupUi(dialog)

        pval_df = pval_df.round(4)
        pval_df = pval_df.fillna(np.nan)
        data = DataModel(pval_df)
        ui.tableView.setModel(data)

        dialog.exec()

        print(f"p-value: {p:.4f}")


