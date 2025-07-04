import numpy as np

class MSD():
    def __init__(self, data, values):
        super().__init__()
        self.data = data
        self.values = values

        self.msd()
    
    def msd(self):
        calculate_time = False
        if 'time' not in self.data.columns:
            self.data['time'] = np.nan
            calculate_time = True
        
        self.data['avg_msd_by_time_cell'] = np.nan
        self.data["avg_msd_by_time_condition"] = np.nan
        self.data["sem_by_time_condition"] = np.nan

        avr_msd = []

        for track_id in sorted(self.data["Track n"].unique()):
            track_df = self.data[self.data["Track n"] == track_id].sort_values("Slice n")

            if calculate_time:
                track_df['time'] = track_df['Slice n'] * self.values['time_interval']
                self.data.loc[track_df.index, 'time'] = track_df["time"].values

            # Calculate MSD
            msd = np.zeros(self.values['n_time_points'])

            dx = track_df['X'].to_numpy()
            dy = track_df['Y'].to_numpy()

            for tau in range(1, self.values['n_time_points']):
                displacements = (dx[tau:] - dx[:-tau])**2 + (dy[tau:] - dy[:-tau])**2
                msd[tau] = np.mean(displacements)

            track_df['avg_msd_by_time_cell'] = msd
            self.data.loc[track_df.index, 'avg_msd_by_time_cell'] = track_df["avg_msd_by_time_cell"].values
            
            avr_msd.append(msd)

        if avr_msd:
            avr_msd = np.array(avr_msd)
            avg = np.mean(avr_msd, axis=0)
            err = np.std(avr_msd, axis=0, ddof=1) / np.sqrt(avr_msd.shape[0])
            self.data.loc[:self.values['n_time_points']-1, "avg_msd_by_time_condition"] = avg
            self.data.loc[:self.values['n_time_points']-1, "sem_by_time_condition"] = err

def plot_msd(ax, avg_msd_data, values):
    # Для каждого набора данных
    for df, label in avg_msd_data:
        if 'avg_msd_by_time_condition' not in df.columns or 'sem_by_time_condition' not in df.columns:
            continue  # Пропускаем, если нет нужных колонок

        # Предполагается, что есть n строк с msd_avg и msd_err
        y = df['avg_msd_by_time_condition'].dropna().values
        yerr = df['sem_by_time_condition'].dropna().values
        x = np.arange(len(y)) * values['time_interval']  # временная шкала

        ax.errorbar(x, y, yerr=yerr, fmt='o-', capsize=4, label=label)

    ax.set_xlabel("Time (step × interval)")
    ax.set_ylabel("Mean Squared Displacement (MSD)")
    ax.set_title("MSD with SEM")
    ax.grid(True)
    ax.legend()
