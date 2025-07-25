import numpy as np
from logger import app_logger as logger

class Speed():
    """
    Computes average instantaneous speed per track and per condition.

    Args:
        data (pd.DataFrame): Trajectory data containing at least 'X', 'Y', 'Track n', 'Slice n'.
        values (dict): Parameters, must contain:
            - 'time_interval': interval between slices
    """
    def __init__(self, data, values):
        super().__init__()
        self.data = data
        self.values = values

        self.speed()

    def speed(self):
        """
        Main method to compute speed metrics:
        - ΔX, ΔY
        - Distance between points
        - Instantaneous speed (distance / time)
        - Average speed per cell
        - Average and SEM speed per condition
        """
        # Flags to control which columns need to be computed
        calculate_dxdy = False
        calculate_time = False
        calculate_dbp = False
        calculate_speed = False

        if 'ΔX' not in self.data.columns or 'ΔY' not in self.data.columns:
            self.data['ΔX'] = np.nan
            self.data['ΔY'] = np.nan
            calculate_dxdy = True
        
        if 'time' not in self.data.columns:
            self.data['time'] = np.nan
            calculate_time = True

        if 'distance_bw_points' not in self.data.columns:
            self.data['distance_bw_points'] = np.nan
            calculate_dbp = True

        if 'instant_speed' not in self.data.columns:
            self.data["instant_speed"] = np.nan
            calculate_speed = True
            
        self.data["avg_speed_by_cell"] = np.nan
        self.data["avg_speed_of_condition"] = np.nan

        avg_speeds = []

        for track_id in sorted(self.data["Track n"].unique()):
            track_df = self.data[self.data["Track n"] == track_id].sort_values("Slice n")

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

            # Average speed per track (ignoring NaNs)
            avg = track_df["instant_speed"].mean(skipna=True)
            avg_speeds.append(avg)
            
            # Save computed columns back to the main DataFrame
            self.data.loc[track_df.index, ['ΔX', 'ΔY', 'distance_bw_points', 'time', 'instant_speed']] = \
                track_df[['ΔX', 'ΔY', 'distance_bw_points', 'time', 'instant_speed']]

            # Store average speed in the first row of the track
            self.data.loc[track_df.index[0], "avg_speed_by_cell"] = avg

        if avg_speeds:
            avg = np.mean(avg_speeds)
            err = np.std(avg_speeds, ddof=1) / np.sqrt(len(avg_speeds))
            combined = f"{avg:.3f} ± {err:.3f}"

            self.data.loc[0, "avg_speed_of_condition"] = avg
            self.data.loc[1, "avg_speed_of_condition"] = err
                    
def plot_speed(ax, speed_data_by_condition):
    """
    Plots average speed per condition as a bar chart.

    Args:
        ax (matplotlib.axes.Axes): Axis to draw on.
        speed_data_by_condition (list): List of tuples (DataFrame, label).
    """

    labels = []
    avg_values = []
    errors = []

    for df, label in speed_data_by_condition:
        try:
            vals = df["avg_speed_of_condition"].dropna().unique()

            avg_str = float(vals[0])
            err = float(vals[1])
            labels.append(label)
            avg_values.append(avg_str)
            errors.append(err)
        except Exception as e:
            logger.exception(f"Error processing condition '{label}': {e}")

    x = np.arange(len(labels))

    ax.bar(x, avg_values, yerr=errors, capsize=5, color='skyblue')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel("Average Speed")
    ax.set_title("Average Speed by Condition")
    ax.grid(True, axis='y')
