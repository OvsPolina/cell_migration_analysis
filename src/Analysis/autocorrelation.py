import numpy as np
import re


class Autocorrelation():
    def __init__(self, data, values):
        super().__init__()
        self.data = data
        self.values = values

        self.autocorrelation()

    def autocorrelation(self):
        # Normalised vector
        self.norm()
        # Average Scalars
        self.scalars()

    def norm(self):
        calculate_dxdy = False

        if 'ΔX' not in self.data.columns or 'ΔY' not in self.data.columns:
            self.data['ΔX'] = np.nan
            self.data['ΔY'] = np.nan
            calculate_dxdy = True

        self.data["magnitude"] = np.nan
        self.data["cos_theta"] = np.nan
        self.data["sin_theta"] = np.nan

        for track_id in sorted(self.data["Track n"].unique()):
            track_df = self.data[self.data["Track n"] == track_id].sort_values("Slice n")
            if calculate_dxdy:
                track_df['ΔX'] = track_df['X'].diff()
                track_df['ΔY'] = track_df['Y'].diff()
            self.data.loc[track_df.index, 'ΔX'] = track_df["ΔX"].values
            self.data.loc[track_df.index, 'ΔY'] = track_df["ΔY"].values
            
            track_df['magnitude'] = np.sqrt(track_df['ΔX']**2 + track_df['ΔY']**2)
            self.data.loc[track_df.index, 'magnitude'] = track_df['magnitude'].values

            # Косинус и синус угла относительно оси X
            track_df['cos_theta'] = track_df['ΔX'] / track_df['magnitude']
            track_df['sin_theta'] = track_df['ΔY'] / track_df['magnitude']
            self.data.loc[track_df.index, 'cos_theta'] = track_df['cos_theta'].values
            self.data.loc[track_df.index, 'sin_theta'] = track_df['sin_theta'].values
    
    def scalars(self):
        for step in range(1, self.values['n_plot_points'] + 1):
            time_label = f"time_{step * self.values['time_interval']}"
            col_name = f"scalar_{time_label}"
            
            # Инициализируем колонку
            self.data[col_name] = np.nan
            avg_scalars = []
            avg_sem = []
            for track_id in sorted(self.data["Track n"].unique()):
                track_df = self.data[self.data["Track n"] == track_id].sort_values("Slice n").reset_index()

                dx = track_df['cos_theta'].to_numpy()
                dy = track_df['sin_theta'].to_numpy()
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
                    err = np.std(scalars, ddof=1) / np.sqrt(len(scalars))

                    avg_scalars.append(avg)
                    avg_sem.append(err)


            if avg_scalars:
                avg = np.mean(avg_scalars)
                err = np.std(avg_scalars, ddof=1) / np.sqrt(len(avg_scalars))
                combined = f"{avg:.3f} ± {err:.3f}"

                self.data.loc[0, col_name] = avg
                self.data.loc[1, col_name] = err


def plot_scalar_averages(ax, all_scalar_data):
    ax.clear()
    for df, label in all_scalar_data:
        time_points = [0]
        scalar_values = [1]

        for col in df.columns:
            if col.startswith("scalar_time_"):
                match = re.search(r"scalar_time_(\d+)", col)
                if match:
                    time_point = int(match.group(1))
                    time_points.append(time_point)

                    vals = df[col].dropna().unique()
                    val = vals[0]
                    scalar_values.append(float(val))

        # Сортировка по времени
        sorted_pairs = sorted(zip(time_points, scalar_values))
        sorted_times, sorted_scalars = zip(*sorted_pairs)

        try:
            ax.plot(sorted_times, sorted_scalars, marker='o', label=label)
        except Exception as e:
            print(label, e)

    ax.set_xlabel("Time (step × interval)")
    ax.set_ylabel("Persistence")
    ax.set_title("Migration Persistence")
    ax.grid(True)
    ax.legend()
        
