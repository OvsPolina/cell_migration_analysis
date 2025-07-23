# Single Cell Migration Analysis App

A PyQt-based desktop application for analyzing cell trajectories using various quantitative metrics such as:

* **Mean Squared Displacement (MSD)**
* **Speed**
* **Directionality Ratio**
* **Autocorrelation**

This tool helps researchers and analysts efficiently process and visualize tracked cell movement data.

Based on the study:  
**Quantitative and unbiased analysis of directional persistence in cell migration**  
_Roman Gorelik & Alexis Gautreau_

---

## Features

* Load data from Excel files.
* Support for multiple sheets (condition per sheet).
* Trajectory plotting.
* Exportable plots (PNG, PDF).
* Migration Analyses include:

  * **Speed** with average and SEM.
  * **MSD** by cell and condition.
  * **Directionality Ratio**.
  * **Autocorrelation**.
* Statistical Tests:
    * **Mann–Whitney U test** (non-parametric version of the t-test)
    * **ANOVA**

---

# Installation Instructions

---

## 1. Running from Source (Manual Setup with Python)

If you want to run the app directly from source code, follow these steps:

### Requirements

* Python 3.10+ installed ([download Python](https://www.python.org/downloads/))
* Dependencies listed in `requirements.txt`

### Installing dependencies

```bash
git clone https://github.com/OvsPolina/cell_migration_analysis.git
cd cell_migration_analysis
python -m venv venv                # create a virtual environment (recommended)
source venv/bin/activate           # macOS/Linux
venv\Scripts\activate.bat          # Windows
pip install -r requirements.txt    # install dependencies
```

### Running the application

```bash
python main.py
```

---

## 2. Running the Standalone Executable (.exe) — Windows

A ready-to-use `cell_migration_analysis.exe` file that does **not require Python or any dependencies installed** on your system.

### How to use

1. Download `cell_migration_analysis.exe` from the [Releases](https://github.com/OvsPolina/cell_migration_analysis) section
2. Run it by double-clicking the file
3. The app will open as a normal desktop program

> **Note:** The executable file size may be around 50-100 MB due to the embedded Python interpreter and libraries.

---

## 3. Installer Setup (Coming Soon)

In upcoming releases, an **installer for Windows** will be provided which will allow you to:

* Install the program into `Program Files`
* Create shortcuts on Desktop and Start Menu
* Easily uninstall via Control Panel ("Programs and Features")

> Stay tuned for updates in the [Releases](https://github.com/OvsPolina/cell_migration_analysis) section.

---

# Usage Instructions

Below you will find descriptions of the main interface elements along with screenshots for macOS and Windows, highlighting key buttons and their functions.

---

## Main Window Overview

The main window contains several important buttons and panels that help you load data, run analyses, and visualize results.

### Interface on macOS

![Mac Interface](path/to/mac_screenshot.png)  
*Figure 1: Main interface on macOS.*

- **Open File** (top-left) — Click this button to open a file dialog and load sample data files into the application.  
- **Analysis Type Dropdown** (next to Load Data) — Select the type of analysis you want to perform, such as Autocorrelation or MSD.  
- **Run Analysis** (right of dropdown) — Executes the selected analysis on the loaded data.  
- **Save Results** (bottom-right) — Saves the processed data and generated plots to your chosen location.  
- **Data Table** (center) — Displays the loaded dataset and updated results after analysis.  

---

### Interface on Windows

![Windows Interface](path/to/windows_screenshot.png)  
*Figure 2: Main interface on Windows.*

- **Load Data** button is located at the top toolbar. Clicking it allows you to import data files.  
- **Analysis Selector** dropdown is to the right of Load Data and lets you choose the analysis method.  
- **Run Analysis** button initiates the selected analysis process.  
- **Save Results** button is near the bottom of the window to export data and figures.  
- The **Data Table** updates dynamically with loaded data and analysis output.  

---

## How to Use the Application

1. **Load Your Data**  
   Click the **Load Data** button and select one or more data files. The data will be displayed in the table view.

2. **Choose Analysis Type**  
   Use the **Analysis Type** dropdown to select your desired analysis method.

3. **Configure Parameters**  
   Input parameters such as *time interval* and *number of plot points* in the settings panel (usually located on the right side or in a separate tab).

4. **Run the Analysis**  
   Click **Run Analysis** to process the data. Results will appear in the table and plots will open in a separate dialog.

5. **View and Save Results**  
   Inspect the plot dialogs for graphical summaries. Use the **Save Results** button to export both data and plots.

---

For additional help, refer to the FAQ section or contact the support team.



## Analysis Modules

### 1. **Speed Analysis**

Calculates instantaneous and average speed per track and condition.

**Preview:**
![Speed Screenshot](path/to/speed_screenshot.png)

---

### 2. **Mean Squared Displacement (MSD)**

Analyzes cell motility over time based on MSD calculations.

**Preview:**
![MSD Screenshot](path/to/msd_screenshot.png)

---

### 3. **Directionality Ratio**

Estimates how linear the movement of a cell is.

**Preview:**
![Directionality Screenshot](path/to/directionality_screenshot.png)

---

### 4. **Autocorrelation**

Assesses the memory of motion in cell paths.

**Preview:**
![Autocorrelation Screenshot](path/to/autocorrelation_screenshot.png)

---

### 5. **Trajectory Plots**

Interactive visualization of tracks per condition.

**Preview:**
![Trajectory Screenshot](path/to/trajectory_screenshot.png)

---

## File Structure

```
project/
├── ui/
│   └── plot/
│       └── plot_window.py
├── analysis/
│   ├── speed.py
│   ├── msd.py
│   ├── dir_ratio.py
│   ├── autocorrelation.py
│   └── trajectories.py
├── main.py
├── README.md
└── requirements.txt
```

---

### Prerequisites

* Python 3.8+
* Pip

Sure! Here’s the README installation and usage instruction template in English, covering the three scenarios you asked for:

---

## 🧩 Technologies Used

* Python 3
* PyQt6
* Matplotlib
* NumPy
* Pandas

---

## License

---

## Contributing

Feel free to open issues or submit pull requests for improvements or new features.

---

## Contact

For questions or support, contact [your.email@example.com](mailto:your.email@example.com)

---

## References

This work is based on the study:  
**Quantitative and unbiased analysis of directional persistence in cell migration**  
_Roman Gorelik & Alexis Gautreau_  
Published in **Nature Methods**, 2014.  
[https://doi.org/10.1038/nmeth.2808](https://doi.org/10.1038/nmeth.2808)


