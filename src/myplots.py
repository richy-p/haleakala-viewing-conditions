import matplotlib.pyplot as plt
import os

plt.style.use('ggplot')
plt.rcParams.update({'font.size':16,'axes.labelcolor': '#000000','ytick.color': '#000000','xtick.color': '#000000'})

green = '#63d297'
yellow = '#fff176'
red = '#ff5252'
colors = [green,yellow,red]
conditions = ['Green','Yellow','Red']


def avg_daily_hours(df,save_path=None):
    '''
    Creates a bar chart showing the average daily weather status for green, yellow and red weather for all months.
    Parameters
    ----------
    df : DataFrame
    save_path : str
        Location to save figure.
    '''
    fig,ax = plt.subplots(figsize=(6,5))
    df.drop('year',axis=1).groupby(['month']).mean().plot.bar(color=colors,ax=ax,stacked=True)
    ax.set_ylim(0,27)
    ax.set_xlabel(None)
    ax.set_ylabel('Hours')
    ax.set_title('Mean Daily Weather Status')
    ax.set_yticks(range(0,25,4))
    ax.legend(ncol=3,fontsize=14,loc='upper center', bbox_to_anchor=(.5,1.02))
    fig.tight_layout()
    if save_path:
        fig.savefig(os.path.join(save_path,'mean_monthly_hours.png'),dpi=300)

def daily_green_weather_over_time(df,months='All',show_comb_avg=False,save_path=None,**kwargs):
    '''
    Creates line plot for the average daily temperature for each month in 'months' over all years in 'df'
    Parameters
    ----------
    df : DataFrame
    months : list or str
        Month names must be three letter abreviations. Put multiple months in a list. A single month does not have to be in a list, but can be.
    show_comb_avg : bool
        If true plots the monthly averages with lower alpha and overlays the combined average for all months.
    save_path : str
        Location to save the figure to.
    '''
    if months == 'All':
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # if only one month is given put it in a list
    elif type(months) == str:
        months = months.split()

    fig,ax = plt.subplots(figsize=(12,6))
    ax.set_prop_cycle('color',plt.cm.Paired(range(12)))
    if show_comb_avg:
        alpha = 0.2
    else:
        alpha = 1

    for month in months:
        df[df['month']==month].groupby('year')['Green'].mean().plot(ax=ax,label=month,alpha=alpha)
    if show_comb_avg:
        df.groupby('year')['Green'].mean().plot(ax=ax,label='Mean',color='g',**kwargs)
    ax.set_xlabel('Year')
    ax.set_ylabel('Hours')
    ax.set_title('Daily Green Weather Averages')
    ax.legend(bbox_to_anchor=(1,1))
    fig.tight_layout()
    if save_path:
        fig.savefig(os.path.join(save_path,'average_daily_green_weather_over_time.png'),dpi=300)

def plot_monthly_distribution_green_wx(df,months='All',save_path=None):
    '''
    Create histogram plots of the green weather for each month in 'months' as subplots in a figure.
    Parameters
    ----------
    df : DataFrame
    months : list or str
        Month names must be three letter abreviations. Put multiple months in a list. A single month does not have to be in a list, but can be.
    save_path : str
        Location to save the figure to. 
    '''
    if months == 'All':
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # if only one month is given put it in a list
    elif type(months) == str:
        months = months.split()

    num_ax = len(months)
    num_cols = 3 if num_ax > 4 else 2 if num_ax == 4 else num_ax
    num_rows = -(num_ax // -num_cols) 

    fig,axs = plt.subplots(num_rows,num_cols,figsize=(num_cols*5,num_rows*4),sharex=True,sharey=True)
    for i,ax in enumerate(axs.flatten()):
        if i >= num_ax:
            ax.axes.remove()
            continue
        df[df['month']==months[i]].hist('Green',ax=ax,color='g',bins=24)
        ax.set_title(months[i])
    fig.suptitle('Distribution of Green Weather')
    fig.text(.5,0,'Hours')
    fig.text(0,0.5,'Frequency',rotation='vertical')
    fig.tight_layout()
    if save_path:
        fig.savefig(os.path.join(save_path,'green_weather_distribution.png'),dpi=300)

def plot_combined_distribution_wx(df,statuses='All',save_path=None):
    '''
    Plot the combined distribution all months.
    Parameters
    ----------
    df : DataFrame
    statuses : str or list
        Options {'All','Green','Yellow','Red'} - if multiple put in list.
    save_path : str
        Location to save the figure to. 
    '''
    if statuses == 'All':
        status_list = ['Green','Yellow','Red']
    elif type(statuses) == str:
        status_list = statuses.split()
    color_dict = {'Green': green, 'Yellow': yellow, 'Red': red}
    fig,ax = plt.subplots(figsize=(10,5))
    for status in status_list:
        df[status].hist(bins=24,ax=ax,alpha=0.3,color=color_dict[status],label=status)
    ax.set_xlim(0,24)
    ax.set_xlabel('Hours')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Weather Status')
    ax.legend()
    if save_path:
        fig.savefig(os.path.join(save_path,'combined_weather_distribution.png'),dpi=300)

def plot_combined_distribution_wx_stacked(df,save_path=None):
    '''
    Plot the combined distribution all months.
    Parameters
    ----------
    df : DataFrame
    save_path : str
        Location to save the figure to. 
    '''
    fig,axs = plt.subplots(3,1,figsize=(8,10),sharex=True)
    conditions = ['Green','Yellow','Red']
    colors = [green,yellow,red]
    for idx,ax in enumerate(axs.flatten()):
        df[conditions[idx]].hist(ax=ax,bins=24,color=colors[idx])
        ax.set_xlim(0,24)
        ax.set_ylim(0,3100)
        ax.set_title(conditions[idx],y=.85)

    axs[1].set_ylabel('Frequency (# days)')
    axs[2].set_xlabel('Hours')
    fig.suptitle('Distribution of Weather Conditions')
    fig.tight_layout()   
    if save_path:
        fig.savefig(os.path.join(save_path,'combined_weather_distribution_stacked.png'),dpi=300)   

if __name__ == "__main__":
    pass