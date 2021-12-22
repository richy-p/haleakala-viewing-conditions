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

def count_NaNs(df):
    '''
    Count the number of NaNs in each column of the date frame.
    Parameters
    ----------
    df : DataFrame
    '''
    len_df = len(df)
    max_digits = int(np.log10(len_df) + 1)
    print(f'Total rows          : {len_df}')
    print('-----------------------------')
    print('Number of NaNs per column:')
    for col in df:
        print(f'{col:20}: {sum(df[col].isna()):{max_digits}}')  

def remove_unreasonable_measurements(df,range_limits={
                    'temperature': (-273,40),
                    'humidity': (0,100),
                    'wind_speed': (0,100),
                    'visibility': (0,100000),
                    'precipitation': (0,100),
                    'dewpoint': (-273,40)
                    },inplace=False):
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

# MVP just consider any NaN measurements 
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
    # should break this up for readability
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

def check_if_red(df,thresholds):
    '''
    '''
    pass

# MVP just counts time based off the time step.
def generate_status_hours_df(df):
    '''
    Parameters
    ----------
    df : 
    Return
    ------
    new_df : 
    '''
    df['seconds'] = np.where(df['10min'],600,10)
    df['date'] = df.index.date
    new_df = pd.DataFrame(columns = ['Green','Yellow','Red'],index=df['date'].unique().tolist())
    new_df.index.name = 'date'
    for status in new_df.columns:
        new_df[status] = (df[df.status==status].groupby(['date']).seconds.sum()) / 3600
    return new_df

def save_df_to_csv(df,year,base_path='data/'):
    '''
    '''
    filename = os.path.join(base_path,f'status_hours_{year}.csv')
    df.to_csv(filename)

def combine_status_hour_dfs(base_path='data/'):
    '''
    Loads the data from all the individual year CVS files into a single Data Frame
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
        # print()
        # print(f'First day: {df_to_add.date.iloc[0]}')
        # print(f'Last day : {df_to_add.date.iloc[-1]}')
        # print(f'Length of df: {len(df_to_add)}')
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
    pass