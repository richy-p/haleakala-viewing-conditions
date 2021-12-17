import prep_data as prep

import numpy as np


if __name__ == "__main__":
    # link for data files
    base_url = "http://kopiko.ifa.hawaii.edu/weather/archivedata/"
    # get list of all data file urls
    csv_urls = prep.get_csv_file_links(base_url)

    # data column names
    column_names = ['date_time','temperature','pressure','humidity','wind_speed','wind_direction','visibility','co2','insolation','vertical_wind_speed','precipitation','10min','dewpoint']
    columns_of_interest = ['date_time','temperature','humidity','wind_speed','visibility','precipitation','dewpoint','10min']
    
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

    #----TEMP----#
    # for initial testing just grab one year - will  use a loop for this later
    year = 1994
    link = prep.get_specific_year(year,csv_urls)
    df = prep.read_data_of_interest(link, column_names,columns_of_interest)
    
     # create a small subset of data to check reasonable data against
    df = df.iloc[:20].copy()
    # change NaNs to numbers for now
    df.humidity.mask([True]*len(df),np.random.uniform(50,100,size=len(df)),inplace=True)
    df.visibility.mask([True]*len(df),np.random.uniform(30000,50000,size=len(df)),inplace=True)
    df.dewpoint.mask([True]*len(df),np.random.uniform(0,40,size=len(df)),inplace=True)
    acceptable_ranges_test = {
                        'temperature': (13,15.02),
                        'humidity': (62.3,84.2),
                        'wind_speed': (7.3,8.5),
                        'visibility': (33000,43000),
                        'precipitation': (0,0),
                        'dewpoint': (9.8,32.2)
                        }
    
    

    print(df)
    # check for reasonable values
    prep.remove_unreasonable_measurements(df,acceptable_ranges,inplace=True)
    print(df)

    # split wind into sustaind and gusts
    df = prep.determine_wind_sust_and_gust(df)
    print(df)

    # add delta dew point
    df['dewpoint_delta'] = df['temperature'] - df['dewpoint']

    # convert thresholds
