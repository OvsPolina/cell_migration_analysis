
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, mannwhitneyu

from logs.logger import app_logger as logger

def run_ttest(cell_data, parameter):
    """
    Performs pairwise statistical comparisons between all conditions in the dataset
    using the Mann–Whitney U test (non-parametric version of the t-test).

    Args:
        cell_data (pd.DataFrame): DataFrame that must include columns:
            - 'condition': categorical variable representing groups
            - parameter: the numeric column to compare between groups
        parameter (str): The name of the column containing numeric data to test.

    Returns:
        pd.DataFrame: Symmetric matrix of p-values for each pair of conditions.
                      Diagonal values are NaN.
    """
    # Get unique group names (conditions)
    conditions = cell_data['condition'].unique()

    # Create an empty symmetric DataFrame to store p-values
    pval_df = pd.DataFrame(index=conditions, columns=conditions, dtype=float)   

    # Iterate over all condition pairs
    for i, cond1 in enumerate(conditions):
        for j, cond2 in enumerate(conditions):
            if i == j:
                pval_df.loc[cond1, cond2] = None  # Skip diagonal (self-comparison)
            elif i < j:
                # Extract data for each condition
                data1 = cell_data[cell_data['condition'] == cond1][parameter]
                data2 = cell_data[cell_data['condition'] == cond2][parameter]
                
                # Perform Mann–Whitney U test (non-parametric, does not assume normality)
                stat, p = mannwhitneyu(data1, data2)
                
                # Store p-value symmetrically
                pval_df.loc[cond1, cond2] = p
                pval_df.loc[cond2, cond1] = p     

    # Round p-values to 4 decimal places
    pval_df = pval_df.round(4)
    pval_df = pval_df.fillna(np.nan)

    return pval_df



