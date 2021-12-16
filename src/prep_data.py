import requests
from bs4 import BeautifulSoup
import pandas as pd


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



if __name__ == "__main__":
    base_url = "http://kopiko.ifa.hawaii.edu/weather/archivedata/"
    print(get_csv_file_links(base_url))