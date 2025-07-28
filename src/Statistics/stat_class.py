from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow
from ui.stats.result_window import Ui_StatsWindow
from ui.stats.parameters_window import Ui_Stat_parameters_window

from src.data_model import DataModel
from src.Statistics.ttest import run_ttest
from src.Statistics.anova import run_anova

from logs.logger import app_logger as logger

import pandas as pd
import numpy as np
from scipy.stats import shapiro
from scipy.optimize import curve_fit

from PyQt6.QtWidgets import QMessageBox

from PyQt6.QtWidgets import (
    QWidget, QDialog, QTreeWidgetItem, QTabWidget
)

class UIStat(QWidget):
    """
    Main widget for running statistical analysis (T-test or ANOVA) on cell tracking data.
    Provides a GUI for selecting samples, configuring parameters, and viewing results.
    """
    def __init__(self, ui):
        """
        Initialize the UIStat widget and connect menu actions to corresponding methods.
        Args:
            ui (QMainWindow): The main UI window object.
        """
        super().__init__()
        self.ui = ui
        self.parameter = None
        self.ui.actionANOVA.triggered.connect(lambda: self.run("ANOVA"))
        self.ui.actionTtest.triggered.connect(lambda: self.run("TTest")) 

    def run(self, method):
        """
        Entry point for running the selected statistical method (TTest or ANOVA).

        Args:
            method (str): The analysis method, either "TTest" or "ANOVA".
        """
        logger.info(f"Stats Module : run {method}")
        # Choose samples to compare
        result = self.open_choose_samples_dialog()
        logger.info(f"Stats Module : Samples selected {self.selected_samples}")
        if result:
            # Choose parameter by which to compare
            result = self.open_parameter_windows()
            logger.info(f"Stats Module : Parameter chosen {self.parameter}")
            if self.parameter:
                self.pretreat_data() # Pre treating the data
                data = None
                # Run chosen method
                try:
                    if method == "ANOVA":
                        data = run_anova(self.cell_data, self.parameter)
                    elif method == "TTest":
                        data = run_ttest(self.cell_data, self.parameter)
                except Exception as e:
                    logger.warning(f"Stats Module : problem with {method} : {e}")
                    QMessageBox.warning(self, "Error", f"{e}")
                # Show calculated data
                if data is not None:
                    self.show_data(data)
                else:
                    QMessageBox.warning(self, "Error", f"Empty data. Verify that you have chosen more than 1 condition (Conditions with the same name are considered the same conditions.)")
            else:
                return None

    def open_parameter_windows(self):
        """
        Opens the parameter selection dialog, where the user chooses the time interval
        and the measurement parameter for analysis.

        Returns:
            None if cancelled, otherwise sets `self.parameter` and `self.time_interval`.
        """
        dialog = QDialog(self)
        ui = Ui_Stat_parameters_window()
        ui.setupUi(dialog)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.time_interval = float(ui.lineEdit_2.text())
                self.parameter = str(ui.comboBox.currentText())
            except Exception as e:
                logger.warning(f"Error Stats module open_parameter_windows: {e}")
                QMessageBox.warning(self, "Error", f"{e}")
                return None
        else:
            return None

    def open_choose_samples_dialog(self):
        """
        Opens a dialog to allow the user to choose file/sheet pairs (samples)
        from a cloned version of the application's main tree widget.

        Returns:
            str: "ok" if the user accepted the dialog, None otherwise.
        """
        dialog = QDialog(self)
        ui = Ui_ChooseSampleWindow()
        ui.setupUi(dialog)
        self.selected_samples = []

        if self.ui.treeWidget:
            ui.treeWidget.clear()
            stack = []

            # Clone treeWidget items into dialog
            for i in range(self.ui.treeWidget.topLevelItemCount()):
                src_item = self.ui.treeWidget.topLevelItem(i)
                cloned_item = QTreeWidgetItem([src_item.text(0)])
                ui.treeWidget.addTopLevelItem(cloned_item)
                stack.append((src_item, cloned_item))

            # Breadth first search
            while stack:
                src_parent, cloned_parent = stack.pop(0)
                for j in range(src_parent.childCount()):
                    src_child = src_parent.child(j)
                    cloned_child = QTreeWidgetItem([src_child.text(0)])
                    cloned_parent.addChild(cloned_child)
                    stack.append((src_child, cloned_child))
            
            
            for i in range(ui.treeWidget.topLevelItemCount()):
                ui.treeWidget.topLevelItem(i).setExpanded(True)

            # Process user selection
            if dialog.exec() == QDialog.DialogCode.Accepted:
                for item in ui.treeWidget.selectedItems():
                    if item.parent() is not None:  # Only selects leaf nodes
                        file_path = item.parent().text(0)
                        sheet_name = item.text(0)
                        self.selected_samples.append([file_path, sheet_name])
                    else: #otherwise take every list in the file
                        for i in range(item.childCount()):
                            child = item.child(i)
                            file_path = item.text(0) 
                            sheet_name = child.text(0) 
                            self.selected_samples.append([file_path, sheet_name])
                return "ok"
            else:
                return None

    def pretreat_data(self):
        """
        Preprocesses selected samples and computes derived metrics:
        - Mean Squared Displacement (MSD)
        - Instantaneous Speed
        - Directionality Ratio
        - Autocorrelation (Migration Persistence)

        The results are stored in `self.cell_data` as a DataFrame.
        """
        cells = []

        for filename in self.selected_samples:
            # Set stacked widget to correct file
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
                logger.error("Stats Module : pretreat_data None data")
                continue

            for track_id in sorted(data["Track n"].unique()):
                try:
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
                    steps = []
                    for step in range(1, 10):
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
                            steps.append(step * self.time_interval)
                except Exception as e:
                    logger.error(f"Stats Module : calculation error {e}")

                # Exponential fit: A(t) = exp(-alpha * t)
                def exp_model(t, alpha):
                    return np.exp(-alpha * t)

                try:
                    popt, _ = curve_fit(exp_model, steps, avg_scalars, p0=[0.01])
                    alpha = popt[0]
                except Exception as e:
                    logger.error(f"Stats Module : exponential fit error {e}")
                    alpha = np.nan  # Fitting failed

                cells.append({
                    'cell_id': track_id,
                    'condition': filename[1],
                    'Speed': avg_speed,
                    'MSD': avg_msd_1,
                    'Directionality Ratio': avg_dir,
                    'Migration Persistence (Autocorrelation)': alpha
                })

        self.cell_data = pd.DataFrame(cells)

    def check_norm_dist(self):
        """
        Checks whether the selected parameter column in `self.cell_data`
        follows a normal distribution using the Shapiro-Wilk test.

        Returns:
            bool: True if normal (p > 0.05), False otherwise.
        """
        stat, p = shapiro(self.cell_data[self.parameter])
        if p > 0.05:
            return True
        return False

    def show_data(self, data):
        """
        Displays the resulting statistical data in a dialog window using a table view.

        Args:
            data (pd.DataFrame): The analysis results to show in the table.
        """
        dialog = QDialog(self)
        ui = Ui_StatsWindow()
        ui.setupUi(dialog)

        data = DataModel(data)
        ui.tableView.setModel(data)

        dialog.exec()
