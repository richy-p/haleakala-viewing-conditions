import prep_data as prep

import os
import glob


# function to check if status hours csv files already exist for all data on IfA site (exclueding 1993 and 2020-1 right now)
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


# function to grab and pre-process any year data not already prepped.
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

    # check for reasonable values
    prep.remove_unreasonable_measurements(df,range_limits,inplace=True)
    
    # split wind into sustaind and gusts
    df = prep.determine_wind_sust_and_gust(df)

    # add delta dew point
    df['dewpoint_delta'] = df['temperature'] - df['dewpoint']

    # convert thresholds to status
    df['status'] = prep.get_weather_status(df,thresholds)

    # make new df with daily hours
    df_status_hours = prep.generate_status_hours_df(df)

    print(f'{year} data prep complete\n')
    # save new df
    if save_results:
        prep.save_df_to_csv(df_status_hours,year)
    if return_df:
        return df_status_hours

    




if __name__ == "__main__":
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
    # get list of all data file urls
    csv_urls = prep.get_csv_file_links(base_url)

    # prep all data 
    for url in csv_urls:
        year = url.split('/')[-1].split('.')[0]
        # for now skip 2020-2021 becuase I know the formating is not correct. Skip 1993 because it is empty.
        if year in ['1993','2020','2021']:
            continue
        # if prepped data file already exist for that year skip it
        elif prepped_data_exists(year):
            print(f'{year} data already prepped.')
            continue
        else:
            get_and_prep_data(url,acceptable_ranges,thresholds)
        
    # combine the daily status hours for all years into one df
    df = prep.combine_status_hour_dfs(base_path='data')
    df = prep.normalize_daily_hours_to_24(df)
    prep.add_month_year_columns(df)
    print(df)