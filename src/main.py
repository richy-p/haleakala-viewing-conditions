import prep_data as prep
import hypothesis_test as ht
import myplots

import os
import glob
from itertools import combinations


def prepped_data_exists(year,base_path='data/'):
    '''
    Check if prepped data file 'status_hours_XXXX.csv' exists
    Parameters
    ----------
    year : int or str
    Return
    ------
    does_exist : bool
        True if prepped data file already exists
    '''
    does_exist = os.path.exists(os.path.join(base_path,f'status_hours_{year}.csv'))
    return does_exist

def get_and_prep_data(url,range_limits,thresholds,save_results=True,save_path='data/',return_df=False):
    '''
    Pipeline to load raw csv file from the IfA archive, clean it, and prepare it by calculating the hours of green, yellow, and red weather.
    Parameters
    ----------
    url : str
        URL of the CSV file to read
    range_limits : dict
        lower and upper limits for each columns except the date_time
    thresholds : dict
        Must contain the columns above as keys with the values being a tuple with the green and red weather threshold values.
    save_results : bool
        if true, results saved in location given by save_path
    save_path : str
        location to store the df with the status hours
    return_df : bool
        if true, returns the df with the calculated status hours
    '''
    # data column names
    column_names = ['date_time','temperature','pressure','humidity','wind_speed','wind_direction','visibility','co2','insolation','vertical_wind_speed','precipitation','10min','dewpoint']
    columns_of_interest = ['date_time','temperature','humidity','wind_speed','visibility','precipitation','dewpoint','10min']

    year = url.split('/')[-1].split('.')[0]
    try:
        # read data
        df = prep.read_data_of_interest(url,column_names,columns_of_interest)
        print(f'{year} data read, processing now.')
    except:
        print(f'Failed to read data for {year} at: {url} ')

    # record the number of NaNs for awareness, later anaylsis
    with open(os.path.join(results_run_dir,'run_info.txt'),'a') as f:
       print('',file=f) # print an empty line to break up the years
       prep.count_NaNs(df,f)

    # check for reasonable values
    prep.remove_unreasonable_measurements(df,range_limits,inplace=True)
    
    # split wind into sustaind and gusts
    df = prep.determine_wind_sust_and_gust(df)

    # add delta dew point
    df['dewpoint_delta'] = df['temperature'] - df['dewpoint']

    # convert thresholds to status
    df['status'] = prep.get_weather_status(df,thresholds)

    # record NaNs after prepping data (will now include values removed outside limit range)
    with open(os.path.join(results_run_dir,'run_info.txt'),'a') as f:
       print('After prep',file=f)
       prep.count_NaNs(df,f)

    # make new df with daily hours
    df_status_hours = prep.generate_status_hours_df(df)

    print(f'{year} data prep complete\n')
    # save new df
    if save_results:
        save_df_to_csv(df_status_hours,f'status_hours_{year}',save_path=save_path)
    if return_df:
        return df_status_hours

def save_df_to_csv(df,name,save_path):
    '''
    Save the DateFrame to a csv file
    Parameters
    ----------
    df : DataFrame
    name : str
        The name of the file without file extension
    save_path : str
        Path to save the data frame to
    '''
    filename_path = os.path.join(save_path,f'{name}.csv')
    df.to_csv(filename_path)

def make_numbered_directory(parent_dir,padding=4):
    '''
    Parameters
    ----------
    parent_dir : str
        Directory to look in
    padding : int
        Number of digits to use for numbered string. Only used if no numbered directories already exist.
    Returns
    -------
    run_dir :str
        path of the directory created
    '''
    last_run_number_string = get_last_run_number_string(parent_dir)
    if last_run_number_string:
        padding = len(last_run_number_string)
    else: 
        # if the string is empty this is the first run 
        last_run_number_string = '0'
    current_run_number = int(last_run_number_string) + 1      
    run_dir = os.path.join(parent_dir,f'run_{current_run_number:0{padding}}')
    os.mkdir(run_dir)
    return run_dir


def get_last_run_number_string(parent_dir):
    '''
    Returns what the last run number is, in string format with any padded zeros, by checking the directory for subdirectories named 'run_XXX'
    Parameters
    ----------
    parent_dir : str
        Directory to look for 'run_XX' directories in
    Returns
    -------
    run_number_string : str
        String of the highest run number, including any padded zeros
    '''
    run_number_strings = [directory.split('/')[-1].split('_')[-1] for directory in glob.glob(os.path.join(parent_dir,'*'))]

    if run_number_strings:
        run_number_string = sorted(run_number_strings)[-1]
    else:
        run_number_string = ''
    return run_number_string

def record_setup(thresholds,range_limits,file=None):
    '''
    Prints the thresholds and range limits to either sys.stdout or file
    Parameters
    ----------
    thresholds : dict
        dict containing the columns as keys and the green and red weather thresholds as values
    range_limits : dict
        dict containing the columns as keys and tuples with the lower and upper ranges as values
    file : file object
        open file object to write to
    '''
    print(f'Thresholds:\n{thresholds}\n',file=file)
    print(f'Valid Range Limits:\n{range_limits}\n',file=file)


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
    # make results directory for current run
    results_run_dir = make_numbered_directory(parent_dir='results')
    data_run_dir = make_numbered_directory(parent_dir='data/status_hours')

    # record the set up info
    with open(os.path.join(results_run_dir,'run_info.txt'),'a') as f:
        record_setup(thresholds,acceptable_ranges,f)

    # get list of all data file urls
    csv_urls = prep.get_csv_file_links(base_url)

    # prep all data 
    for url in csv_urls:
        year = url.split('/')[-1].split('.')[0]
        if int(year) in skip_years:
            continue
        # if prepped data file already exist for that year skip it
        elif prepped_data_exists(year,base_path=data_run_dir):
            print(f'{year} data already prepped.')
            continue
        else:
            get_and_prep_data(url,acceptable_ranges,thresholds,save_path=data_run_dir)
        
    # combine the daily status hours for all years into one df
    df = prep.combine_status_hour_dfs(base_path=data_run_dir)
    df = prep.normalize_daily_hours_to_24(df)
    prep.add_month_year_columns(df)
    save_df_to_csv(df,'combined_status_hours',data_run_dir)
    
    # Make plots
    run_image_dir = os.path.join(results_run_dir,'images')
    os.mkdir(run_image_dir)
    myplots.daily_green_weather_over_time(df,save_path=run_image_dir,marker='o',show_comb_avg=True)
    myplots.avg_daily_hours(df,save_path=run_image_dir)
    myplots.plot_monthly_distribution_green_wx(df,months='All',save_path=run_image_dir)
    myplots.plot_combined_distribution_wx(df,statuses='All',save_path=run_image_dir)

    # sort the months by mean to make results easier to read
    months_sorted_by_mean = ht.sort_dict_keys_by_values(ht.get_monthly_means(df))
    combos = list(combinations(months_sorted_by_mean,2))
    num_combos = len(combos)
    alpha = 0.5 
    FWER = 1 - (1 - alpha)**num_combos
    print(f'The family-wise error rate for alpha={alpha} and {num_combos} combinations is: {FWER}')
    alpha_adj = alpha / num_combos
    print(f'Apply a Bonferroni correction and use an adjusted alpha of {alpha_adj:.5f}')
    results = ht.mwu_test_month_combos(df,combos,alpha=alpha_adj,is_alpha_adjusted=True)
    print(results)
    save_df_to_csv(results,'hyp_test_results',results_run_dir)


    print(results[results['is_significant']==True].drop('is_significant',axis=1))

