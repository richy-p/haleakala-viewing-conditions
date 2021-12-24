import pandas as pd
import prep_data as prep

class NaNTracker():
    def __init__(self,df):
        self.columns = df.columns
        self.num_rows = len(df)



if __name__ == "__main__":
    base_url = "http://kopiko.ifa.hawaii.edu/weather/archivedata/"
    csv_urls = prep.get_csv_file_links(base_url)
    column_names = ['date_time','temperature','pressure','humidity','wind_speed','wind_direction','visibility','co2','insolation','vertical_wind_speed','precipitation','10min','dewpoint']
    
    year = 2001
    link = prep.get_specific_year(year,csv_urls)
    df_2001 = pd.read_csv(link,na_values='\\N',names=column_names)


    