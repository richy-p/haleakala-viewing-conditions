import utilities as ut

import os
import scipy.stats as stats
import pandas as pd
from itertools import combinations
import shutil

def get_monthly_means(df,column='Green'):
    '''
    Parameters
    ----------
    df : DataFrame
        df must have 'months' as a column, with three letter abreviations as the values (Jan, Feb, ...)
    column : string
        Column name to calculate the mean for
    Returns
    -------
    monthly_means : dict
        Dictionary with month abbreviations as the keys and the corresponding mean of column as the values.
    '''
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_means = {}
    for month in months:
        monthly_means[month] = df[df['month']==month][column].mean()
    return monthly_means

def sort_dict_keys_by_values(d,descending=True):
    '''
    Parameters
    ----------
    d : dict
    descending : bool
        True returns keys in order from the value that is greatest to least.
    Returns
    -------
    sorted_keys : list
        keys of the given dictionary sorted by their values
    '''
    sorted_keys = sorted(d,key=d.get,reverse=descending)
    return sorted_keys

def mwu_test_month_combos(df, combos, column='Green', alpha=0.05, is_alpha_adjusted=False):
    '''
    Performs a Mann-Whitney U test on each combination of months.
    Parameters
    ----------
    df : DataFrame
        Contains the daily hours for each status
    combos : list
        List of tuples containing the month combinations
    column : str ('Green','Yellow','Red')
        Column name to grab values from 
    alpha : float
        Significance threshold. If specified value is what individual p values should be compared to ('alpha' already adjusted to account for family-wise error) then set 'is_alpha_adjusted' to True
    is_alpha_adjusted : bool
        If True uses 'alpha' as significance threshold for each test. If False, applies Bonferroni correction ('alpha'/len('combos')) for individual tests.
    Returns
    -------
    results : DataFrame
        Data Frame with columns: ['month_1', 'month_2', 'month_1_mean', 'month_2_mean', 'mean_diff', 'p_value', 'is_significant'], and rows are each combination of months.
    '''
    if not is_alpha_adjusted:
        alpha = alpha/len(combos)

    results = pd.DataFrame()
    for month1,month2 in combos:
        month1_values = df[df['month']==month1][column]
        month2_values = df[df['month']==month2][column]
        
        t,p = stats.mannwhitneyu(month1_values,month2_values)
        is_significant = p < alpha
        
        month1_mean = month1_values.mean()
        month2_mean = month2_values.mean()
        diff_means = month1_mean - month2_mean
        
        results = results.append({
                'month_1':month1, 'month_2': month2, 'month_1_mean': month1_mean, 'month_2_mean': month2_mean, 
                'mean_diff': diff_means, 'p_value': p, 'is_significant': is_significant
                }, ignore_index=True)
    return results 



if __name__ == "__main__":
    # load df
    # get data directory
    data_dir = input('Enter data directory: ')
    df = pd.read_csv(os.path.join(data_dir,'combined_status_hours.csv'))
    df.set_index('date',inplace=True)

    # make results directory for current run - allows for running multiple tests 
    results_dir = ut.make_numbered_directory(parent_dir='results',base_name='results')

    ut.copy_txt_files(data_dir,results_dir)

    # sort the months by mean to make results easier to read
    months_sorted_by_mean = sort_dict_keys_by_values(get_monthly_means(df))
    combos = list(combinations(months_sorted_by_mean,2))
    num_combos = len(combos)
    alpha = 0.05 
    fwer = 1 - (1 - alpha)**num_combos
    alpha_adj = alpha / num_combos
    with open(os.path.join(results_dir,'run_info.txt'),'a') as f:
        print(f'\nThe family-wise error rate for alpha={alpha} and {num_combos} combinations is: {fwer}',file=f)
        print(f'Apply a Bonferroni correction and use an adjusted alpha of {alpha_adj:.5f}',file=f)
    results = mwu_test_month_combos(df,combos,alpha=alpha_adj,is_alpha_adjusted=True)
    ut.save_df_to_csv(results,'hyp_test_results',results_dir)

    # view significant results
    print(results[results['is_significant']==True].drop('is_significant',axis=1))
