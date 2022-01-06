import prep_data as prep
import hypothesis_test as ht
import myplots
import utilities as ut

import os
from itertools import combinations


if __name__ == "__main__":
    # set testing to True to just use smaller data sets from 1994-2005
    testing = False
    
    # skip years that don't have data (1993) or have formatting issues (2020-2021)
    skip_years = {1993,2020,2021}
    if testing:
        # use smaller data set to run for testing
        skip_years.update(set(range(2006,2020,1)))
        

    # Establish required info
    # link for data files
    base_url = "http://kopiko.ifa.hawaii.edu/weather/archivedata/"
    
    # Define reasonable ranges for each column
    acceptable_ranges = {
        'temperature': (-273,40),
        'humidity': (0,100),
        'wind_speed': (0,100),
        'visibility': (0,100000),
        'precipitation': (0,100),
        'dewpoint': (-273,40)
        }
    # Define the thresholds for ('Green', 'Red') weather - plan to use config file in future
    thresholds = {
            'humidity': (75,85),
            'wind_sust': (10,12),
            'wind_gust': (15,15),
            'visibility': (50000,40000),
            'precipitation': (0,0),
            'dewpoint_delta': (6,3)
            }

    # Run 
    # make results directory for current run - allows for running multiple tests 
    results_dir = ut.make_numbered_directory(parent_dir='results',base_name='results')
    data_dir = ut.make_numbered_directory(parent_dir='data',base_name='prepped_data')

    # get list of all data file urls
    csv_urls = prep.get_csv_file_links(base_url)


    # prep all data 
    for url in csv_urls:
        year = url.split('/')[-1].split('.')[0]
        if int(year) in skip_years:
            continue
        # if prepped data file already exist for that year skip it
        elif ut.prepped_data_exists(year,base_path=data_dir):
            print(f'{year} data already prepped.')
            continue
        else:
            prep.get_and_prep_data(url,acceptable_ranges,thresholds,save_path=data_dir)

    # record the set up info to a file
    years = ut.get_years(data_dir)
    with open(os.path.join(data_dir,'run_info.txt'),'a') as f:
        ut.record_setup(thresholds,acceptable_ranges,years,f)


    # combine the daily status hours for all years into one df
    df = prep.combine_status_hour_dfs(base_path=data_dir)
    df = prep.normalize_daily_hours_to_24(df)
    prep.add_month_year_columns(df)
    ut.save_df_to_csv(df,'combined_status_hours',data_dir)


    # Make plots
    image_dir = os.path.join(results_dir,'images')
    os.mkdir(image_dir)
    myplots.daily_green_weather_over_time(df,save_path=image_dir,marker='o',show_comb_avg=True)
    myplots.avg_daily_hours(df,save_path=image_dir)
    myplots.plot_monthly_distribution_green_wx(df,months='All',save_path=image_dir)
    myplots.plot_combined_distribution_wx_stacked(df,save_path=image_dir)

    ut.copy_txt_files(data_dir,results_dir)

    # sort the months by mean to make results easier to read
    months_sorted_by_mean = ht.sort_dict_keys_by_values(ht.get_monthly_means(df))
    combos = list(combinations(months_sorted_by_mean,2))
    num_combos = len(combos)
    alpha = 0.05 
    fwer = 1 - (1 - alpha)**num_combos
    alpha_adj = alpha / num_combos
    with open(os.path.join(results_dir,'run_info.txt'),'a') as f:
        print(f'\nThe family-wise error rate for alpha={alpha} and {num_combos} combinations is: {fwer}',file=f)
        print(f'Apply a Bonferroni correction and use an adjusted alpha of {alpha_adj:.5f}',file=f)
    results = ht.mwu_test_month_combos(df,combos,alpha=alpha_adj,is_alpha_adjusted=True)
    ut.save_df_to_csv(results,'hyp_test_results',results_dir)

    # view significant results
    print(results[results['is_significant']==True].drop('is_significant',axis=1))

