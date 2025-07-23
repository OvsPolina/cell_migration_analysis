import matplotlib.pyplot as plt
import pandas as pd

def plot_trajectories(ax, data, values, filename):
    """
    Plot cell trajectories from tracking data, optionally limiting the number
    of tracks and time points displayed.

    Args:
        ax (matplotlib.axes.Axes): Axes object to draw the plot on.
        data (pd.DataFrame): DataFrame containing tracking data. Must contain columns:
                             ['Track n', 'Slice n', 'X', 'Y'].
        values (dict): Dictionary with two keys:
                       - 'n_tracks': maximum number of tracks to plot.
                       - 'n_time_points': number of time points (slices) per track to display.
        filename (str): Filename or label for the plot title.
    """
    df = data.copy()
    tracks = 0

    # Loop over each track in the dataset
    for track_id, group in df.groupby('Track n'):
        if tracks >= values['n_tracks']:
            break
        tracks+=1

        group_sorted = group.sort_values('Slice n')
        group_sorted = group_sorted.head(values['n_time_points'])  # take first n slides
        if group.empty:
            continue  # skip if track has no valid points

        # Get starting coordinates of the trajectory
        x0, y0 = group_sorted.iloc[0]['X'], group_sorted.iloc[0]['Y']

        # Shift the trajectory so it starts at (0, 0)
        xs = group_sorted['X'] - x0
        ys = group_sorted['Y'] - y0

        ax.plot(xs, ys, marker=None)

    # Adjust plot limits to be symmetric around origin
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    # Max possible radius
    R = max(abs(xlim[0]), abs(xlim[1]), abs(ylim[0]), abs(ylim[1]))

    # Symmetric borders
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_aspect('equal')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title(f"{filename} Trajectories")
    #ax.legend()
    ax.grid(True)