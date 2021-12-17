import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

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

# Note this does not work for Green status if there are NaNs
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
        (df['humidity'] <= min(thresholds['humidity'])) &
        (df['wind_sust'] <= min(thresholds['wind_sust'])) & 
        (df['wind_gust'] <= min(thresholds['wind_gust'])) & 
        (df['precipitation'] <= min(thresholds['precipitation'])) & 
        (df['dewpoint_delta'] >= max(thresholds['dewpoint_delta'])) &
        (df['visibility'] >= max(thresholds['visibility']))
        )]
    status_values = ['Red','Green']
    return np.select(status_conditions,status_values,default='Yellow')

def check_if_red(df,thresholds):
    '''
    '''
    pass




if __name__ == "__main__":
    pass