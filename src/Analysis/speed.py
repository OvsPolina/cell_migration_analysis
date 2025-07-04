import numpy as np


class Speed():
    def __init__(self, data, values):
        super().__init__()
        self.data = data
        self.values = values

        self.speed()

    def speed(self):
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

            avg = track_df["instant_speed"].mean(skipna=True)
            avg_speeds.append(avg)
            
            # Вставляем обратно все рассчитанные колонки
            self.data.loc[track_df.index, ['ΔX', 'ΔY', 'distance_bw_points', 'time', 'instant_speed']] = \
                track_df[['ΔX', 'ΔY', 'distance_bw_points', 'time', 'instant_speed']]

            # Вставляем среднюю скорость в первую строку трека
            self.data.loc[track_df.index[0], "avg_speed_by_cell"] = avg

        if avg_speeds:
            avg = np.mean(avg_speeds)
            err = np.std(avg_speeds, ddof=1) / np.sqrt(len(avg_speeds))
            combined = f"{avg:.3f} ± {err:.3f}"

            # Запишем значение во все строки данного трека
            self.data.loc[0, "avg_speed_of_condition"] = avg
            self.data.loc[1, "avg_speed_of_condition"] = err
                    
def plot_speed(ax, speed_data_by_condition):

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
            print(f"Ошибка при обработке значения {vals}: {e}")

    # Рисуем столбчатую диаграмму
    x = np.arange(len(labels))

    ax.bar(x, avg_values, yerr=errors, capsize=5, color='skyblue')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel("Average Speed")
    ax.set_title("Average Speed by Condition")
    ax.grid(True, axis='y')
