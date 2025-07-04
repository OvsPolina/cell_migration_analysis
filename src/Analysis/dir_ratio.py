import numpy as np

class DirRatio():
    def __init__(self, data, values):
        super().__init__()
        self.data = data
        self.values = values

        self.dir_ratio()

    def dir_ratio(self):
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

        self.data['Δ(xi-x0)'] = np.nan
        self.data['Δ(yi-y0)'] = np.nan
        self.data["distance_to_start"] = np.nan
        self.data["cumulative_distance"] = np.nan
        self.data["dir_ratio"] = np.nan
        self.data["average_dir_ratio"] = np.nan
        self.data["sem_average_dir_ratio"] = np.nan

        avr_dir = []

        for track_id in sorted(self.data["Track n"].unique()):
            track_df = self.data[self.data["Track n"] == track_id].sort_values("Slice n")

            if calculate_dxdy:
                track_df['ΔX'] = track_df['X'].diff()
                track_df['ΔY'] = track_df['Y'].diff()

            dx = track_df['X'].to_numpy()
            dy = track_df['Y'].to_numpy()
            track_df['Δ(xi-x0)'] = dx - dx[0]
            track_df['Δ(yi-y0)'] = dy - dy[0]
            
            if calculate_dbp:
                track_df['distance_bw_points'] = np.sqrt(track_df['ΔX']**2 + track_df['ΔY']**2)
            
            track_df['distance_to_start'] = np.sqrt(track_df['Δ(xi-x0)']**2 + track_df['Δ(yi-y0)']**2)
            track_df['cumulative_distance'] = track_df['distance_bw_points'].fillna(0).cumsum()

            if calculate_time:
                track_df["time"] = track_df["Slice n"] * self.values['time_interval']

            if calculate_speed:
                dx = track_df['distance_bw_points'].to_numpy()
                dy = track_df['time'].to_numpy()
                track_df["instant_speed"] = dx / dy

            track_df["dir_ratio"] = track_df["distance_to_start"] / track_df["cumulative_distance"]
            track_df["dir_ratio"] = track_df["dir_ratio"].replace([np.inf, -np.inf], np.nan)

            # Вставляем обратно все рассчитанные колонки
            self.data.loc[track_df.index, ['ΔX', 'ΔY', 'Δ(xi-x0)', 'Δ(yi-y0)', 'time', 'instant_speed', 'distance_bw_points', 'distance_to_start', 'cumulative_distance', "dir_ratio"]] = \
                track_df[['ΔX', 'ΔY', 'Δ(xi-x0)', 'Δ(yi-y0)', 'time', 'instant_speed', 'distance_bw_points', 'distance_to_start', 'cumulative_distance', "dir_ratio"]]

            # Вставляем среднюю скорость в первую строку трека
            avr_dir.append(track_df['dir_ratio'])

        if avr_dir:
            avr_dir = np.array(avr_dir)
            avg = np.mean(avr_dir, axis=0)
            err = np.std(avr_dir, axis=0, ddof=1) / np.sqrt(avr_dir.shape[0])
            self.data.loc[:self.values['n_time_points']-1, "average_dir_ratio"] = avg
            self.data.loc[:self.values['n_time_points']-1, "sem_average_dir_ratio"] = err



def plot_dir_ratio(ax, avg_dir_data, values):
    # Для каждого набора данных
    for df, label in avg_dir_data:
        if 'average_dir_ratio' not in df.columns or 'sem_average_dir_ratio' not in df.columns:
            continue  # Пропускаем, если нет нужных колонок

        # Предполагается, что есть n строк с msd_avg и msd_err
        y = df['average_dir_ratio'].dropna().values
        yerr = df['sem_average_dir_ratio'].dropna().values
        x = np.arange(len(y)) * values['time_interval']  # временная шкала

        ax.errorbar(x, y, yerr=yerr, fmt='o-', capsize=4, label=label)

    ax.set_xlabel("Time (step × interval)")
    ax.set_ylabel("Directionality Ratio")
    ax.set_title("Directionality Ratio with SEM")
    ax.grid(True)
    ax.legend()

