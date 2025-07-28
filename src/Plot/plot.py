from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ui.plot.plot_window import Ui_Plot

from logs.logger import app_logger as logger

import os

class PlotDialog(QDialog):
    """
    A custom dialog window for displaying and saving matplotlib plots
    inside a PyQt application.

    Attributes:
        filename (list): A list with the file path(s) used to suggest a default name.
        analysis (str): Description or type of the analysis (e.g., "Speed", "MSD").
        figure (Figure): Matplotlib Figure object used for plotting.
        canvas (FigureCanvas): Canvas to embed the matplotlib figure into Qt widget.
    """
    def __init__(self, filename, analysis, title="Plot", parent=None):
        """
        Initialize the PlotDialog.

        Args:
            filename (list): A list with at least one file path.
            analysis (str): A string indicating the analysis type for labeling.
            title (str, optional): The window title. Defaults to "Plot".
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.filename = filename
        self.analysis = analysis
        self.ui = Ui_Plot()
        self.ui.setupUi(self)
        self.setWindowTitle(title)

        # Create matplotlib Figure and Canvas
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        # Embed the canvas into the UI layout
        layout = QVBoxLayout(self.ui.widget)
        layout.addWidget(self.canvas)

        # Connect buttons (OK = save, Cancel = close)
        self.ui.buttonBox.accepted.connect(self.save_figure)
        self.ui.buttonBox.rejected.connect(self.reject)

    def save_figure(self):
        """
        Opens a file dialog to save the current figure as PNG or PDF.
        """
        # Use base name of the input file for default name
        file = os.path.basename(self.filename[0])
        path, _ = QFileDialog.getSaveFileName(self, "Save Plot", f"{file} {self.analysis}", "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)")
        if path:
            self.figure.savefig(path)
            logger.info(f"Plot Module : Figure saved at {path}")

    def show_plot(self, plot_func):
        """
        Displays the plot using a provided plotting function.

        Args:
            plot_func (function): A function that takes a matplotlib Axes object
                                  and draws the desired plot on it.
        """
        self.figure.clear()  # Clear any previous plots
        ax = self.figure.add_subplot(111)
        plot_func(ax)        # Let the user draw on the axes
        self.canvas.draw()   # Update the canvas with the new drawing
        self.show()          # Display the dialog
