
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, mannwhitneyu

def run_ttest(cell_data, parameter):
    conditions = cell_data['condition'].unique()

    # Создаём пустой датафрейм для p-value
    pval_df = pd.DataFrame(index=conditions, columns=conditions, dtype=float)   

    # Перебираем все пары
    for i, cond1 in enumerate(conditions):
        for j, cond2 in enumerate(conditions):
            if i == j:
                pval_df.loc[cond1, cond2] = None  # или np.nan, т.к. сравниваем с самим собой
            elif i < j:
                data1 = cell_data[cell_data['condition'] == cond1][parameter]
                data2 = cell_data[cell_data['condition'] == cond2][parameter]
                
                stat, p = mannwhitneyu(data1, data2)
                
                pval_df.loc[cond1, cond2] = p
                pval_df.loc[cond2, cond1] = p  # заполняем симметрично    

    pval_df = pval_df.round(4)
    pval_df = pval_df.fillna(np.nan)

    return pval_df



