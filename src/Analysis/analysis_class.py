import pandas as pd
import os

from PyQt6.QtWidgets import (
    QWidget, QDialog, QMessageBox, QTreeWidgetItem, QTabWidget
)
from PyQt6.QtCore import Qt

from logger import app_logger as logger

from ui.configuration.configuration_autocorrelation_window import Ui_ConfigurationAutocorrelationWindow
from ui.configuration.choose_sample_window import Ui_ChooseSampleWindow

from src.Plot.plot import PlotDialog
from src.data_model import DataModel
from src.Analysis.autocorrelation import Autocorrelation, plot_scalar_averages
from src.Analysis.speed import Speed, plot_speed
from src.Analysis.msd import MSD, plot_msd
from src.Analysis.dir_ratio import DirRatio, plot_dir_ratio
from src.Plot.trajectories import plot_trajectories

class UIAnalysis(QWidget):
    """
    Main analysis controller class. Connects UI elements to various analysis routines
    such as Autocorrelation, MSD, Speed, Directionality Ratio, and Trajectories.
    """
    def __init__(self, ui):
        """
        Initializes UIAnalysis class.

        Args:
            ui (QMainWindow): The main UI instance (contains stacked widget, tree, and menu).
        """
        super().__init__()
        self.ui = ui

        # Connect analysis actions to handler
        self.ui.actionAutocorrelation.triggered.connect(lambda: self.open_dialog("Autocorrelation"))
        self.ui.actionMSD.triggered.connect(lambda: self.open_dialog("MSD"))
        self.ui.actionSpeed.triggered.connect(lambda: self.open_dialog("Speed"))
        self.ui.actionDirectionality_Ratio.triggered.connect(lambda: self.open_dialog("Directionality_Ratio"))
        self.ui.actionTrajectories.triggered.connect(lambda: self.open_dialog("Trajectories"))

    def open_dialog(self, analysis):
        """
        Open the configuration dialog for the selected analysis type.

        Args:
            analysis (str): Name of the selected analysis.
        """
        logger.info(f"Opening configuration dialog for: {analysis}")
        dialog = QDialog(self)
        ui = Ui_ConfigurationAutocorrelationWindow()
        ui.setupUi(dialog)
        if analysis == "Trajectories":
            ui.lineEdit_n_plot_points.setDisabled(True)
            ui.lineEdit_time_interval.setDisabled(True)
        elif analysis != "Autocorrelation":
            ui.lineEdit_n_plot_points.setDisabled(True)
        

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.values = self._read_values(ui)
            if self.values is not None:
                logger.info(f"Configuration accepted: {self.values}")
                chosen = self.open_choose_samples_dialog()
                if chosen:
                    self.run_analysis(analysis)
        else:
            return None

    def _read_values(self, ui):
        """
        Read and validate user inputs from the configuration dialog.

        Args:
            ui (Ui_ConfigurationAutocorrelationWindow): Config UI instance.

        Returns:
            dict or None: Parsed parameters or None if input is invalid.
        """
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
        except ValueError as e:
            logger.warning(f"Invalid input in configuration: {e}")
            QMessageBox.warning(self, "Error", "Please input correct parameters.")
            return None

    def open_choose_samples_dialog(self):
        """
        Open a dialog for the user to choose input samples from the loaded file tree.

        Returns:
            bool or None: True if samples selected, None otherwise.
        """
        dialog = QDialog(self)
        ui = Ui_ChooseSampleWindow()
        ui.setupUi(dialog)
        self.selected_samples = []

        if self.ui.treeWidget:
            ui.treeWidget.clear()
            stack = []

            # Сlone upper level of the file tree
            for i in range(self.ui.treeWidget.topLevelItemCount()):
                src_item = self.ui.treeWidget.topLevelItem(i)
                cloned_item = QTreeWidgetItem([src_item.text(0)])
                ui.treeWidget.addTopLevelItem(cloned_item)
                stack.append((src_item, cloned_item))

            # Search in breadth
            while stack:
                src_parent, cloned_parent = stack.pop(0)
                for j in range(src_parent.childCount()):
                    src_child = src_parent.child(j)
                    cloned_child = QTreeWidgetItem([src_child.text(0)])
                    cloned_parent.addChild(cloned_child)
                    stack.append((src_child, cloned_child))
            
            
            for i in range(ui.treeWidget.topLevelItemCount()):
                ui.treeWidget.topLevelItem(i).setExpanded(True)

            # Run dialog
            if dialog.exec() == QDialog.DialogCode.Accepted:
                for item in ui.treeWidget.selectedItems():
                    if item.parent() is not None: # check that it is a file in the list
                        file_path = item.parent().text(0)
                        sheet_name = item.text(0)
                        self.selected_samples.append([file_path, sheet_name])
                    else: #otherwise take every list in the file
                        for i in range(item.childCount()):
                            child = item.child(i)
                            file_path = item.text(0) 
                            sheet_name = child.text(0) 
                            self.selected_samples.append([file_path, sheet_name])
                logger.info(f"Selected samples: {self.selected_samples}")
                return True

            else:
                return None

    def pretreat_data(self, df, filename):
        """
        Clean and preprocess the input DataFrame.

        Args:
            df (pd.DataFrame): Raw input data.
            filename (tuple): (filename, sheetname)

        Returns:
            pd.DataFrame or None: Cleaned data or None if invalid.
        """
        try:
            df.dropna(subset=["Track n", "Slice n"], inplace=True)
            df["Track n"] = df["Track n"].astype(int)
            df["Slice n"] = df["Slice n"].astype(int)
            df["X"] = pd.to_numeric(df["X"], errors='coerce')
            df["Y"] = pd.to_numeric(df["Y"], errors='coerce')
        except Exception as e:
            logger.error(f"Error while treating data: {e}")
            QMessageBox.warning(self, "Error", f"Incorrect type of data in columns Track n or Slice n:\n{e}")
            return None
        
        # Treat track
        cleaned_rows = []
        missing_tracks = []
        for track_id in sorted(df["Track n"].unique()):
            track_df = df[df["Track n"] == track_id].sort_values("Slice n")
            if len(track_df) < self.values['n_time_points']:
                missing_tracks.append(track_id)
            else:
                cleaned_rows.append(track_df.iloc[:self.values['n_time_points']])

        result_df = pd.concat(cleaned_rows, ignore_index=True)

        # Check number of tracks
        if len(df["Track n"].unique()) < self.values['n_tracks']:
            logger.warning(f"Track count mismatch in {filename}: expected {self.values['n_tracks']}, found {len(df['Track n'].unique())}")
            QMessageBox.warning(self, "Warning", f"{filename[0]} {filename[1]} expected {self.values['n_tracks']} tracks, found {len(df['Track n'].unique())}.")

        if missing_tracks:
            logger.warning(f"Missing slices for tracks in {filename}: {missing_tracks}")
            QMessageBox.warning(self, "Warning", f"{filename[0]} {filename[1]} Folowing tracks have less than {self.values['n_time_points']} slices: {missing_tracks}")

        return result_df

    def run_analysis(self, analysis):
        """
        Run the selected analysis and update the interface with the results.

        Args:
            analysis (str): Type of analysis to perform.
        """
        logger.info(f"Running analysis: {analysis}")

        self.all_scalar_data = []
        self.speed_data_by_condition = []
        self.avg_msd_data = []
        self.avg_dir_data = []
        self.trajectories_dialogs = []
        self.plot_dialogs = []

        if self.values['time_interval'] == 0 or self.values['n_plot_points'] == 0:
            logger.warning("Invalid analysis parameters: time interval or n plot points is 0.")
            QMessageBox.warning(self, "Error", "Please, input correct parameters.")

        for filename in self.selected_samples:
            # Find sheet
            index = None
            for i in range(self.ui.stackedWidget.count()):
                widget = self.ui.stackedWidget.widget(i)
                file = os.path.basename(getattr(widget, 'filename', None))
                if file == filename[0]:
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
                logger.warning(f"No DataFrame found for: {filename}")
                continue

            original_df = data_model.get_dataframe()

            data = self.pretreat_data(original_df, filename)
            if data is None:
                continue
            
            try: 
                # Perform the selected analysis
                if analysis == "Autocorrelation":
                    autocorr_data = Autocorrelation(data, self.values)
                    self.all_scalar_data.append((autocorr_data.data, f"{filename[0]} {filename[1]}"))
                    data = autocorr_data.data
                
                if analysis == "MSD":
                    msd_data = MSD(data, self.values)
                    self.avg_msd_data.append((msd_data.data, f"{filename[1]}"))
                    data = msd_data.data
                
                if analysis == "Speed":
                    speed_data = Speed(data, self.values)
                    self.speed_data_by_condition.append((speed_data.data, f"{filename[1]}"))
                    data = speed_data.data
                    
                if analysis == "Directionality_Ratio":
                    dir_data = DirRatio(data, self.values)
                    self.avg_dir_data.append((dir_data.data, f"{filename[1]}"))
                    data = dir_data.data

                if analysis == "Trajectories":
                    dialog = PlotDialog(filename, analysis, title=f"{analysis} {filename[1]}")
                    dialog.show_plot(lambda ax: plot_trajectories(ax, data, self.values, filename[1]))
                    dialog.show()

                    # Save pointer so the dialog won't close automatically
                    self.trajectories_dialogs.append(dialog)
            except Exception as e:
                logger.exception(f"Analysis Module : problem with {analysis} : {e}")
                QMessageBox.warning(self, "Error", e)

            #Update table in tab:
            new_model = DataModel(data)
            table.setModel(new_model)

            # Reset unsaved change flags in the tree
            tree_item = getattr(table, "tree_item", None)
            data = tree_item.data(0, Qt.ItemDataRole.UserRole) or {}
            data["unsaved_changes"] = True
            tree_item.setData(0, Qt.ItemDataRole.UserRole, data)
            
        # create plot Dialog
        dialog = PlotDialog(filename, analysis, title=f"{analysis} Plot")

        if analysis == "Autocorrelation":
            dialog.show_plot(lambda ax: plot_scalar_averages(ax, self.all_scalar_data))

        if analysis == "Speed":
            dialog.show_plot(lambda ax: plot_speed(ax, self.speed_data_by_condition))

        if analysis == "MSD":
            dialog.show_plot(lambda ax: plot_msd(ax, self.avg_msd_data, self.values))

        if analysis == "Directionality_Ratio":
            dialog.show_plot(lambda ax: plot_dir_ratio(ax, self.avg_dir_data, self.values))
        
        if analysis != "Trajectories":
            dialog.show()
            self.plot_dialogs.append(dialog)

        logger.info(f"Analysis {analysis} completed.")

        
        
