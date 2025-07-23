
import pandas as pd
from scipy.stats import shapiro,f_oneway
from statsmodels.stats.multicomp import pairwise_tukeyhsd



from logger import app_logger as logger

def run_anova(cell_data, parameter):
    """
    Performs one-way ANOVA on the given cell data and parameter.
    If the ANOVA test is significant (p < 0.05), it performs Tukey's HSD post-hoc test.

    Args:
        cell_data (pd.DataFrame): DataFrame containing at least 'condition' and the target parameter.
        parameter (str): Column name to analyze across different conditions.

    Returns:
        pd.DataFrame: 
            - If significant: Tukey HSD test results.
            - If not significant: A one-row DataFrame showing p-value and significance.
    """
    # Group data by condition and extract the parameter values
    grouped = [group[parameter].values for name, group in cell_data.groupby('condition')]
    try:
        # Perform one-way ANOVA test
        stat, p = f_oneway(*grouped)
    except Exception as e:
        logger.exception(f"Stats Module : ANOVA {e}")

    if p < 0.05:
        # If ANOVA is significant, perform Tukey's post-hoc test
        logger.info(f"ANOVA : p-value significant, Tukey HSD is performed")
        tukey = pairwise_tukeyhsd(endog=cell_data[parameter],
                        groups=cell_data['condition'],
                        alpha=0.05)
        
        # Convert Tukey results to a DataFrame
        data = pd.DataFrame(
            data=tukey._results_table.data[1:],  # Skip header row
            columns=tukey._results_table.data[0]  # Use header
        )
    else:
        # If ANOVA is not significant, return a single p-value row
        logger.info(f"ANOVA : p-value is not significant")
        pval_df = pd.DataFrame({'p-value': [p],
                                'Significance': ['Not Significant']})
        data = pval_df
    
    return data


