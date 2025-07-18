import matplotlib.pyplot as plt
import pandas as pd

def plot_trajectories(ax, data, values, filename):
    """
    Построить траектории с ограничением по трекам и слайдам внутри цикла.

    - track_ids: список треков для отображения (например, [1, 2, 5]).
                 Если None — показывать все.
    - slice_range: кортеж (min_slice, max_slice) для ограничения по слайдам.
                   Если None — показывать все.
    """
    df = data.copy()
    tracks = 0

    for track_id, group in df.groupby('Track n'):
        if tracks >= values['n_tracks']:
            break
        tracks+=1

        group_sorted = group.sort_values('Slice n')
        group_sorted = group_sorted.head(values['n_time_points'])  # берем первые n слайдов
        if group.empty:
            continue  # если после фильтрации группа пустая — пропускаем

        # координаты первой точки траектории
        x0, y0 = group_sorted.iloc[0]['X'], group_sorted.iloc[0]['Y']

        # сдвиг всей траектории так, чтобы началась в (0, 0)
        xs = group_sorted['X'] - x0
        ys = group_sorted['Y'] - y0

        ax.plot(xs, ys, marker=None)

    # После построения всех траекторий:
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Определим максимально возможный радиус
    R = max(abs(xlim[0]), abs(xlim[1]), abs(ylim[0]), abs(ylim[1]))

    # Установим симметричные границы
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect('equal')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f"{filename} Trajectories")
    #ax.legend()
    ax.grid(True)