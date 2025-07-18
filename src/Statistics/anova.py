
import pandas as pd
from scipy.stats import shapiro,f_oneway
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def run_anova(cell_data):
    grouped = [group['autocorr'].values for name, group in cell_data.groupby('condition')]
    stat, p = f_oneway(*grouped)

    if p < 0.05:
        tukey = pairwise_tukeyhsd(endog=cell_data['autocorr'],
                        groups=cell_data['condition'],
                        alpha=0.05)
        
        data = pd.DataFrame(data=tukey._results_table.data[1:], columns=tukey._results_table.data[0])
    else:
        pval_df = pd.DataFrame({'p-value': [p],
                                'Significance': ['Not Significant']})
        data = pval_df
    
    return data


