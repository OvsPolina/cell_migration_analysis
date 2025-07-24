# Single Cell Migration Analysis App

A PyQt-based desktop application for analyzing cell trajectories using various quantitative metrics such as:

* **Mean Squared Displacement (MSD)**
* **Speed**
* **Directionality Ratio**
* **Autocorrelation**

This tool helps researchers and analysts efficiently process and visualize tracked cell 2D movement data.

Based on the study:  
**Quantitative and unbiased analysis of directional persistence in cell migration**  
_Roman Gorelik & Alexis Gautreau_

---

## Features

* Load data from Excel files.
* Support for multiple sheets (condition per sheet).
* Trajectory plotting.
* Exportable plots (PNG).
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

## 2. Running the Standalone Executable (.exe) — Windows (Coming soon)

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

### Interface

![Mac Interface](path/to/mac_screenshot.png)  
*Figure 1: Main interface on macOS.*

![Windows Interface](path/to/windows_screenshot.png)  
*Figure 2: Main interface on Windows.*


### File Menu

* **New File**: Create a new blank project.
* **Open File**: Load a file into the application.
* **Save**: Save current work.
* **Save as**: Save under a new filename.


### Edit Menu

* **Undo / Redo**: Standard undo/redo actions.
* **Cut / Copy / Paste**: Modify data.
* **Delete**: Remove selected item.
* **Select All**: Select all items in current view.


### Analyse Menu

* **Autocorrelation**: Compute the persistence of direction over time.
* **Speed**: Calculate the average speed of tracked cells.
* **MSD** (Mean Squared Displacement): Measure average distance moved over time intervals.
* **Directionality Ratio**: Measure directedness of motion.

Each analyse presents a plot at the end that can be saved as PNG file.


### Statistics Menu

* **T test**: Perform a two-sample pairwise T-test across conditions.
* **ANOVA**: Perform analysis of variance across multiple conditions. If the p-value is significant, will present Pairwise Tukey HSD test results. Otherwise will show p-value.


### Plot Menu

* **Trajectories**: Visualize cell movement tracks over time centered at (0,0).

---

## Workflow

1. **Open a File**
   Use `File > Open File` or the toolbar icon to import tracking data.

   ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

    File and condition names appear in the table and tree widgets.

2. **Select a Condition/Track**
   Navigate the tree view to choose a file and condition. Data will be shown in the central panel - table.

   ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

    ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

3. **Run Analyses**
   Use the **Analyse** menu or toolbar to compute movement metrics like:

   * Speed
   * MSD
   * Autocorrelation
   * Directionality Ratio

   ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

    ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

    ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

4. **Visualize Tracks**
   Select **Plot > Trajectories** to see the paths of migrating cells.

   ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

5. **Perform Statistical Tests**
   After analysis, use the **Statistics** menu to:

   * Compare conditions using **T test** or **ANOVA**.
   * View **p-values** in a comparison matrix.

   ![Mac Interface](path/to/mac_screenshot.png)  
    *Figure 1: Main interface on macOS.*

    You can select which parameter to analyze statistically (e.g., Speed, MSD, Directionality).

---

## Supported Input

The app expects tabular data with columns like:

* `Track n` (track ID)
* `Slice n` (frame number)
* `X`, `Y` (coordinates)

Example of the input excel file you can find in `example.xlsx` file.

---

For additional help contact the support team.



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
cell_migration_analysis/
├── logs/
│   └── app.log
├── src/
│   ├── Analysis/
│       ├── analysis_class.py
│       ├── autocorrelation.py
│       ├── dir_ratio.py
│       ├── msd.py
│       └── speed.py
│   ├── Plot/
│       ├── plot.py
│       └── trajectories.py
│   ├── Statistics/
│       ├── anova.py
│       ├── stat_class.py
│       └── ttest.py
│   ├── utils/
│       └── input_data.py
│   ├── ui_edit.py
│   ├── ui_file.py
│   └── data_model.py
├── ui/
│   └── configuration/
│       ├── choose_sample_window.py
│       ├── choose_sample_window.ui
│       ├── configuration_autocorrelation_window.ui
│       └── configuration_autocorrelation_window.py
│   ├── main_window/
│       ├── main_window.py
│       └── main_window.ui
│   ├── plot/
│       ├── plot_window.py
│       └── plot.ui
│   └── stats/
│       ├── parameters_window.py
│       ├── parameters_window.ui
│       └── result_window.py
├── __init__.py
├── example.xlsx
├── main.py
├── logger.py
├── README.md
└── requirements.txt
```

---

### Prerequisites

* Python 3.8+
* Pip

---

## 🧩 Technologies Used

* Python 3
* PyQt6
* Matplotlib
* NumPy
* Pandas

---

## Contact

For questions or support, contact [polina.ovsiannikova0403@gmail.com](mailto:polina.ovsiannikova0403@gmail.com)

---

## References

This work is based on the study:  
**Quantitative and unbiased analysis of directional persistence in cell migration**  
_Roman Gorelik & Alexis Gautreau_  
Published in **Nature Methods**, 2014.  
[https://doi.org/10.1038/nmeth.2808](https://doi.org/10.1038/nmeth.2808)


