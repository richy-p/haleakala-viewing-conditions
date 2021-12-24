
# TODAY
Think about the power and threshold to use  
Review hypothesis testing - Bonferonni correction  
Normalize the daily hours numbers to total 24 hours in a day.   
Wrangle the data a little more to build arrays for each month with all the daily green hours

# Conditions
## Define valid ranges for each column
I noticed some values are not possible (temperatures and dewpoints below -273 deg C). I will use the following for the acceptable ranges.


|               | Min  | Max    | Note                                                                          |
|---------------|------|--------|-------------------------------------------------------------------------------|
| Temperature   | -273 | 40     | below -273 &deg;C not possible, max temperature ever on Maui was less than 40 |
| Humidity      | 0    | 100    |                                                                               |
| Wind Speed    | 0    | 100    |                                                                               |
| Visibility    | 0    | 100000 |                                                                               |
| Precipitation | 0    | 100    |                                                                               |
|  Dew Point    | -273 | T      | Dew point can't be higher than the temperature                                |

## Thresolds to use
|      | Units | Green | Yellow | Red |
|:-----|------:|------:|-------:|-----|
|date | YYYY-MM-DD HH\:mm\:ss | N/A | N/A | N/A |
|temperature| &deg;C |  N/A | N/A | N/A  |
|humidity|% | <=75 | \[75-85) | >85 |
|wind_speed| m/s | sustained <= 10 | | > 12 |
|          |     | gusts <= 15 | | > 15 |
|visibility| meters | >=50000 | | <40000 |
|precipitation| inches | <=0 | | > 0 |
|delta dewpoint| &deg;C | > 6 | | < 3 |




# Steps

## (Opt) Create a thresholds file to read from

## Read data convert to weather status hours
1. Get urls 
2. Read single year file 
3. convert '\N' to NaN
4. drop uniteresting columns
4. convert date_time column from str to datetime
5. sep sust wind and gusts - if 10min = 0 wind_speed is sustained, otherwise it is gusts, need to get 2 min average
5. check values of columns to see if they are in expected ranges
    - (opt) write a report to view summar of year (any major 
concerns?)
    - record how many values are outside the range
6. (opt) add 'status' columns for each weather condition with threshold
    - this could be for further analysis of what causes the most red weather conditions
7. add 'status' column for overal weather condition
8. For every change in weather status get the start and stop times
9. for each day sum the hours of each weather condition
10. save the daily hours for future use

## Build arrays for each month and weather condition
1. Load all the saved daily hours for each condition
2. Normalize the daily hours and multipy each by 24 so the total hours for each day is 24.
3. add column for month to group and do comparisons


## Hypothesis test
1. Use the arrays of daily green hours for each month for a hypothesis test.
```
1. Scientific Question: Does one month have a higher average daily green weather hours than the others?

2. $H_0$: There is no significant difference between the average daily green weather hours each month

3. $H_a$: multiple combinations (12 choose 2) : mean hours of month A > mean hours of month B 

4. Create a Probabilistic Model of the Situation Assuming the Null Hypothesis is True

5. Decide how Surprised You Need to Be to Reject Your Skeptical Assumption - apply Bonferroni correction

6. Collect Your Data - done

7. Calculate the Probability of Finding a Result Equally or More Extreme than Actually Observed Assuming the Null Hypothesis is True

8. Compare the p-value to Your Stated Rejection Threshold
```

# Elevator Pitch
Ground based optical observatories require mostly clear skies and good weather conditions in order to make space observations.   
How good the weather conditions need to be is dependent on the site and equipment in use.   When weather conditions meet the required threshold, it is referred to as green weather, meaning "go for operations."   
I am investigating the daily green weather hours for the summit of Haleakalā, a dormant volcano in Maui; with the goal of determining if one month has more green weather on average than the others.

## Want to add now
1. Make config files for thresholds and range limits
1. Ability to run analysis with different thresholds and save all results in new direcotry. 
1. Look into what measurements are NaNs, how does it change over time

## Improvements for future
1. Handle NaNs using nearest neighbors - build model to predict and test
1. Other test better suited to cyclcical trends instead of discrete bins (such as months) - Chris was trying to think of what one was called. roh?

## Other Notes
- Power calculation for non parametric tests are messy and what I found still requires assumptions about the shape of the data that aren't true.