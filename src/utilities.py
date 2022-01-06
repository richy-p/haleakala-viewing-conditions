import os
import glob
from shutil import copy2

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

def make_numbered_directory(parent_dir,base_name,padding=4):
    '''
    Parameters
    ----------
    parent_dir : str
        Directory to look in
    base_name : str
        name of the directory to look for/create (excluding any numbers)
    padding : int
        Number of digits to use for numbered string. Only used if no numbered directories already exist.
    Returns
    -------
    numbered_dir :str
        path of the directory created
    '''
    last_number_string = get_last_number_string(parent_dir,base_name)
    if last_number_string:
        padding = len(last_number_string)
    else: 
        # if the string is empty this is the first run 
        last_number_string = '0'
    current_number = int(last_number_string) + 1      
    numbered_dir = os.path.join(parent_dir,f'{base_name}_{current_number:0{padding}}')
    os.mkdir(numbered_dir)
    return numbered_dir


def get_last_number_string(parent_dir,base_name):
    '''
    Returns what the last run number is, in string format with any padded zeros, by checking the directory for subdirectories named 'run_XXX'
    Parameters
    ----------
    parent_dir : str
        Directory to look for numbered directories in
    base_name : str
        name of the directory to look for/create (excluding any numbers)
    Returns
    -------
    last_number_string : str
        String of the highest run number, including any padded zeros
    '''
    dir_number_strings = [directory.split('/')[-1].split('_')[-1] for directory in glob.glob(os.path.join(parent_dir,f'{base_name  }*'))]

    if dir_number_strings:
        last_number_string = sorted(dir_number_strings)[-1]
    else:
        last_number_string = ''
    return last_number_string

def get_years(data_dir):
    '''
    Get the years that have data pre-processed
    Parameters
    ----------
    data_dir : str
        Directory to look for the pre-processed data files
    Return
    ------
    list_of_years : list
        List containing the years 
    '''
    list_of_years = [file.split('/')[-1].split('_')[-1].split('.')[0] for file in glob.glob(os.path.join(data_dir,'status_hours_*.csv'))]
    list_of_years = sorted(list_of_years)
    return list_of_years

def record_setup(thresholds,range_limits,years,file=None):
    '''
    Prints the thresholds and range limits to either sys.stdout or file
    Parameters
    ----------
    thresholds : dict
        dict containing the columns as keys and the green and red weather thresholds as values
    range_limits : dict
        dict containing the columns as keys and tuples with the lower and upper ranges as values
    years : list
        list containing all the years
    file : file object
        open file object to write to
    '''
    print(f'Thresholds:\n{thresholds}\n',file=file)
    print(f'Valid Range Limits:\n{range_limits}\n',file=file)
    print(f'Years included: \n{years}\n', file=file)

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

def copy_txt_files(source,destination):
    '''
    Copies the text files from one directory to another
    Parameters
    ----------
    source : str
        Source directory of the text files
    destination : str
        Destination to copy text files
    '''
    files = glob.glob(os.path.join(source,'*.txt'))
    for file in files:
        copy2(file,destination)

if __name__ == "__main__":
    pass