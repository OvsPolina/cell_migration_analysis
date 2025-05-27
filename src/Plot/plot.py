from PyQt6.QtWidgets import QDialog, QVBoxLayout, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ui.plot.plot_window import Ui_Plot  # путь к сгенерированному UI-классу

class PlotDialog(QDialog):
    def __init__(self, parent=None, title="Plot"):
        super().__init__(parent)
        self.ui = Ui_Plot()
        self.ui.setupUi(self)
        self.setWindowTitle(title)

        # Создаем фигуру и канвас
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(self.ui.widget)
        layout.addWidget(self.canvas)

        # Подключаем кнопки
        self.ui.buttonBox.accepted.connect(self.save_figure)
        self.ui.buttonBox.rejected.connect(self.reject)

    def save_figure(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)")
        if path:
            self.figure.savefig(path)

    def show_plot(self, plot_func):
        """
        plot_func — функция, которая принимает Axes и рисует на нем график
        """
        ax = self.figure.add_subplot(111)
        plot_func(ax)
        self.canvas.draw()
        self.exec()
