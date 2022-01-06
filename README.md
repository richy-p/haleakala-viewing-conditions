# Haleakalā Viewing Conditions for Space Observations
## Summary
Analyzing weather data for Haleakalā to determine the best month for space observations. See [Haleakalā_Viewing_Conditions_for_Space_Observations.pdf](Haleakalā_Viewing_Conditions_for_Space_Observations.pdf) for project description, analysis, and results.

## Repo Organization Notes
The analysis is set up to be able to run multiple times with various thresholds and acceptable ranges for the weather conditions. Each time the analysis is run the pre-processed data and the results will be stored in numbered directories. A ```run_info.txt``` is stored in each directory to identify parameters used for that run. 
1. ```src``` contains the analysis scripts.  
    a. ```prep_data.py``` converts the archived IfA weather data into a data set containing the daily hours of Green, Yellow, and Red weather.  The generated data set will be stored in ```data/prepped_data_XXXX```.   
    b. ```hypothesis_test.py``` runs the Mann-Whitney U test to compare each month against each other. Reads the specified ```prepped_data_XXXX``` directory and returns the results in ```results/results_XXXX```. Note that the numbered directories may not be the same as multiple hypothesis tests could be ran on the same prepped data. The results includes a text file with run information and a csv files with the hypothesis test results.  
    c. ```utilities.py``` and ```myplots.py``` contain functions used in the analysis and generating plots.  
    d. ```main.py``` will run the the entire analysis (preparing data, generating plots and performing hypothesis test).
1. ```notebooks``` contains Jupyter notebooks used in the developement of the python scripts. Because they were just for development they are "messy", and are not necessary to just run the analysis. Some do contain more details on the raw data and exploring the preppared data before the hypothesis test.
1. ```data``` contains the pre-processed data from each run in numbered ```prepped_data``` directories as well as a sample of the IfA data in ```sample_data```.  
1. ```results``` contains numbered directories for the results of subsequent tests.  Each numbered directory contains the hypothesis test results, text files with information about the run, and an images directory with the plots for that run.
1. ```images``` contains variations of figures with formating for the presentation charts.



