import utilities as ut

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
import glob

def get_csv_file_links(base_url):
    '''
    Get links for all csv files on site
    Parameters
    ----------
    base_url : str
        website to look for csv files
    Returns
    -------
    csv_urls : list
        list of strings that are complete urls for csv files
    '''
    # make sure there is a file sep in order to append to base_url
    if base_url[-1] != '/':
        base_url += '/'
    
    reqs = requests.get(base_url)
    soup = BeautifulSoup(reqs.text, 'html.parser')

    links = []
    for link in soup.find_all('a'):
        links.append(link.get('href'))
    # combine the base_url to each csv file on the site
    csv_urls = [base_url+link for link in links if '.csv' in link]
    if not csv_urls:
        print(f'No csv files found at {base_url}')
    return csv_urls

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
        df = read_data_of_interest(url,column_names,columns_of_interest)
        print(f'{year} data read, processing now.')
    except:
        print(f'Failed to read data for {year} at: {url} ')

    # record the number of NaNs for awareness (possible later anaylsis)
    with open(os.path.join(save_path,'NaN_info.txt'),'a') as f:
       print('',file=f) # print an empty line to break up the years
       count_NaNs(df,f)

    # check for reasonable values
    remove_unreasonable_measurements(df,range_limits,inplace=True)
    
    # split wind into sustaind and gusts
    df = determine_wind_sust_and_gust(df)

    # add delta dew point
    df['dewpoint_delta'] = df['temperature'] - df['dewpoint']

    # convert thresholds to status
    df['status'] = get_weather_status(df,thresholds)

    # record NaNs after prepping data (will now include values removed outside limit range)
    with open(os.path.join(save_path,'NaN_info.txt'),'a') as f:
       print('After prep',file=f)
       count_NaNs(df,f)

    # make new df with daily hours
    df_status_hours = generate_status_hours_df(df)

    print(f'{year} data prep complete\n')
    # save new df
    if save_results:
        ut.save_df_to_csv(df_status_hours,f'status_hours_{year}',save_path=save_path)
    if return_df:
        return df_status_hours

def get_specific_year(year,url_list):
    '''
    Get the url link for a given year
    Parameters
    ----------
    year : str or int
    url_list : list
        list of all urls to seach through
    Return
    ------
    link : str
        url to the csv file for that year
    '''
    if type(year) == int:
        year = str(year)
    elif type(year) != str:
        return 'Year must be a string or integer'
    link = [url for url in url_list if year in url][0]
    return link

def read_data_of_interest(link,column_names,columns_of_interest):
    '''
    Read the csv file as a DataFrame, assigns column names, and only keeps those of interest. Also converts teh datetime string to datetime format.
    Parameters
    ----------
    link : str
        URL of the CSV file to read
    colum_names : list of strings
        Column names for the CSV files
    columns_of_interest : list of strings
        List of columns to keep in the returned DataFrame
    Return
    ------
    df : DataFrame
    '''
    df = pd.read_csv(link,na_values='\\N',names=column_names)
    # drop columns not interested in.
    df = df[columns_of_interest] 
    # change date string to date time
    df['date_time'] = pd.to_datetime(df['date_time'])
    df.set_index('date_time',inplace=True)
    return df

def count_NaNs(df,file=None):
    '''
    Count the number of NaNs in each column of the date frame.
    Parameters
    ----------
    df : DataFrame
    f : file to write to, must be open and writable. If None, prints to terminal
    '''
    len_df = len(df)
    max_digits = int(np.log10(len_df) + 1)
    year = df.index[0].year
    print(f'{year}',file=file)
    print(f'Total rows          : {len_df}',file=file)
    print('-----------------------------',file=file)
    print(f'Column                 NaNs',file=file)
    print('-----------------------------',file=file)
    for col in df:
        print(f'{col:20}: {sum(df[col].isna()):{max_digits}}',file=file)  
    print('-----------------------------',file=file)
    pass

def remove_unreasonable_measurements(df,range_limits,inplace=False):
    '''
    Check all values are reasonable and if not change to NaN
    Parameters
    ----------
    df : DataFrame
        DataFrame must have columns: 'date_time','temperature','humidity','wind_speed','visibility','precipitation','dewpoint'
    range_limits : dict
        lower and upper limits for each columns except the date_time
    Return 
    ------
    df_new: DataFrame with NaNs replacing out of range values. - only returned if inplace=False
    '''
    df_new = pd.DataFrame()
    for col in df.drop(['10min'],axis=1).columns:
        df_new[col] = df[col].mask((df[col]<range_limits[col][0]) | (df[col]>range_limits[col][1]),inplace=inplace)
    if not inplace:
        return df_new

def determine_wind_sust_and_gust(df):
    '''
    Determines if the 'wind_speed' is gusts or sustained. Will add additional columns to df for both. If 'wind_speed' is raw measurements the calculated sustained wind will be the rolling 2 min average. 
    Parameters
    ----------
    df : DataFrame
        df must contain datetimes as the index and the columns 'wind_speed' and '10min'. '10min' is a indicator that the measurement is a 10 min average.
    Return
    ------
    df : DataFrame 
        Additional colums 'wind_sust' and 'wind_gust' included. Note 'wind_gust' will be all NaN if the 'wind_speed' measurment was already a 10 min average
    '''
    df['wind_sust'] = np.where(df['10min']==1,df['wind_speed'],df.wind_speed.rolling('120s').mean())
    df['wind_gust'] = np.where(df['10min']==0,df['wind_speed'],np.nan)
    return df

def get_weather_status(df,thresholds):
    '''
    Determine the weather status (Green,Yellow, or Red) based on the given thresholds
    Parameters
    ----------
    df : DataFrame
        Must contain columns 'humidity','wind_sust','wind_gust','precipitation','visibility', and 'dewpoint_delta'
    thresholds : dict
        Must contain the columns above as keys with the values being a tuple with the green and red weather threshold values.
    status : Series
        Series of same length as df with corresponding status values as strings ('Green', 'Yellow', or 'Red')
    '''
    status_conditions = [(
        (df['humidity'] > max(thresholds['humidity'])) | 
        (df['wind_sust'] > max(thresholds['wind_sust'])) | 
        (df['wind_gust'] > max(thresholds['wind_gust'])) | 
        (df['precipitation'] > max(thresholds['precipitation'])) | 
        (df['dewpoint_delta'] < min(thresholds['dewpoint_delta'])) | 
        (df['visibility'] < min(thresholds['visibility']))
        ),(
        ((df['humidity'].isna()) | (df['humidity'] <= min(thresholds['humidity']))) &
        ((df['wind_sust'].isna()) | (df['wind_sust'] <= min(thresholds['wind_sust']))) & 
        ((df['wind_gust'].isna()) | (df['wind_gust'] <= min(thresholds['wind_gust']))) & 
        ((df['precipitation'].isna()) | (df['precipitation'] <= min(thresholds['precipitation']))) & 
        ((df['dewpoint_delta'].isna()) | (df['dewpoint_delta'] >= max(thresholds['dewpoint_delta']))) &
        ((df['visibility'].isna()) | (df['visibility'] >= max(thresholds['visibility'])))
        )]
    status_values = ['Red','Green']
    return np.select(status_conditions,status_values,default='Yellow')

def generate_status_hours_df(df):
    '''

    Parameters
    ----------
    df : DataFrame
        Must contain datetime as index and columns: ['10min','status']. '10min' is bool and 'status' is either 'Green', 'Yellow', or 'Red'.
    Return
    ------
    new_df : DataFrame
        DataFrame with 'date' as index and columns: ['Green','Yellow','Red']. Values are the hours of each condition for each day.
    '''
    df['seconds'] = np.where(df['10min'],600,10)
    df['date'] = df.index.date
    new_df = pd.DataFrame(columns = ['Green','Yellow','Red'],index=df['date'].unique().tolist())
    new_df.index.name = 'date'
    for status in new_df.columns:
        new_df[status] = (df[df.status==status].groupby(['date']).seconds.sum()) / 3600
    return new_df

def combine_status_hour_dfs(base_path):
    '''
    Loads the data from all the individual year 'status_hours' CSV files into a single Data Frame
    Parameters
    ----------
    base_path : str
        Directory path to location of the status hours CSV files.
    Returns
    -------
    df : DataFrame
    '''
    status_csv_files = sorted(glob.glob(os.path.join(base_path,'status_hours*.csv')))
    df = pd.DataFrame()
    for file in status_csv_files:
        df_to_add = pd.read_csv(file)
        df = pd.concat([df,df_to_add],ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date',inplace=True)
    return df

def normalize_daily_hours_to_24(df):
    '''
    Normalizes the hours of each status to 24 and replaces NaN with 0.
    Parameters
    ----------
    df : DataFrame
    Returns  
    -------
    normalized_df : DataFrame
    '''
    normalized_df = df.div(df.sum(axis=1),axis=0) * 24
    normalized_df.fillna({'Green': 0,'Yellow': 0,'Red':0},inplace=True)
    return normalized_df

def add_month_year_columns(df):
    '''
    Add columns indicating the month and the year to the data frame.
    Parameters
    ----------
    df : DataFrame
        df should have index of date-times named 'date' 
    '''
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    df.reset_index(inplace=True)
    df['month'] = pd.Categorical(df['date'].dt.strftime('%b'),categories=months,ordered=True)
    df['year'] = df['date'].dt.year
    df.set_index('date',inplace=True)
    pass

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
    # make directory for current run - allows for running multiple tests 
    data_dir = ut.make_numbered_directory(parent_dir='data',base_name='prepped_data')



    # get list of all data file urls
    csv_urls = get_csv_file_links(base_url)

    # prep all data
    # prep_all_available_data(csv_urls,acceptable_ranges,thresholds,save_results=True,save_path=data_dir) 
    for url in csv_urls:
        year = url.split('/')[-1].split('.')[0]
        if int(year) in skip_years:
            continue
        # if prepped data file already exist for that year skip it
        elif ut.prepped_data_exists(year,base_path=data_dir):
            print(f'{year} data already prepped.')
            continue
        else:
            get_and_prep_data(url,acceptable_ranges,thresholds,save_results=True,save_path=data_dir)
            
    # record the set up info to a file
    years = ut.get_years(data_dir)
    with open(os.path.join(data_dir,'run_info.txt'),'a') as f:
        ut.record_setup(thresholds,acceptable_ranges,years,f)


    # combine the daily status hours for all years into one df
    df = combine_status_hour_dfs(base_path=data_dir)
    df = normalize_daily_hours_to_24(df)
    add_month_year_columns(df)
    ut.save_df_to_csv(df,'combined_status_hours',data_dir)

