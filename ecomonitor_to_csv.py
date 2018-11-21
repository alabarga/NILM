## EcoMonitor data converter ##
# 
# This program has been written to convert the available consumption data from the NURI smart meter to the preferred structure for NILM-Eval (https://github.com/beckel/nilm-eval). 
# The data is received from the EcoMonitor smart meter data collector made by Hark Tech by downloading a CSV-file from the customer website. 
# 
# Input: 1 CSV-file from EcoMonitor from the path data/rawdata/smartmeter/ecomonitor.csv.
# 
# Output: 7 separated consumption CSV-files in folders based on the date of data collection in the path: /data/powermundsen_data/smartmeter/YYYY-MM-DD




import csv
import pandas as pd
from pylab import *
import datetime
import time
import os


# Setting some variables
mpl.rcParams['agg.path.chunksize'] = 10000
plt.rcParams["figure.dpi"] = 600
plt.rcParams.update({'font.size': 22})
current_directory = os.getcwd()
household = '01'
plotvalues = {'Pi':'Active power in [W]', 
              'Pe':'Active power out [W]', 
              'Qi':'Reactive power in [VAr]', 
              'Qe':'Reactive power out [VAr]', 
              'I1':'Current phase 1 [A]', 
              'I2':'Current phase 2 [A]', 
              'I3':'Current phase 3 [A]', 
              'U1':'Voltage phase 1 [V]', 
              'U2':'Voltage phase 2 [V]', 
              'U3':'Voltage phase 3 [V]', 
              'Ai':'Accumulated active power in [KW]', 
              'Ae':'Accumulated active power out [KW]', 
              'Ri':'Accumulated reactive power in [VArh]', 
              'Re':'Accumulated reactive power out [VArh]'}
units = {'Pi':'W',
 'Pe':'kW',
 'Qi':'VAr',
 'Qe':'VAr',
 'I1':'Amper',
 'I2':'Amper',
 'I3':'Amper',
 'U1':'Volt',
 'U2':'Volt',
 'U3':'Volt',
 'Ai':'KW',
 'Ae':'KW',
 'Ri':'VArh',
 'Re':'VArh'}
filenames = {'Pi':'powerallphases',
 'I1':'currentl1',
 'I2':'currentl2',
 'I3':'currentl3',
 'U1':'voltagel1',
 'U2':'voltagel2',
 'U3':'voltagel3'}


# Import the CSV
df = pd.read_csv('data/rawdata/smartmeter/ecomonitor.csv')

# Renaming columns
df.rename(columns={'DTM':'time'}, inplace=True)

# Converting from kW to W
df.loc[:,'Pi'] *= 1000
df.loc[:,'Pe'] *= 1000
df.loc[:,'Qi'] *= 1000
df.loc[:,'Qe'] *= 1000
df.loc[:,'Ri'] *= 1000
df.loc[:,'Re'] *= 1000

# Making new columns for date and time
df['year'] = df['time'].str.slice(0,4)
df['month'] = df['time'].str.slice(5,7)
df['day'] = df['time'].str.slice(8,10)
df['time_of_day'] = df['time'].str.slice(11,16) 

# Adding seconds count
for index, row in df.iterrows():
    timestamp = row['time']
    time_reduced = timestamp[-8:]
    x = time.strptime(time_reduced.split(',')[0],'%H:%M:%S')
    second = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
    df.set_value(index,'second',second)
    
#print(df)

# Finding unique days
unique_years = df.year.unique()
unique_months = df.month.unique()
unique_days = df.day.unique()
print('Unique years: %s, Unique months: %s, Unique days: %s' %(unique_years, unique_months, unique_days))

print('\t\t Staring day iteration')
for year in unique_years:
    for month in unique_months:
        for day in unique_days:
            print('\t\t\t Working on day %s-%s-%s' %(year, month, day))

            df_temp = df.loc[(df['day'] == day)] # Locks the rows with this value (This only looks at the day, not the month)
            #print(df_temp)


            # Setting second to be index
            df_temp.set_index("second")
            new_index = pd.Index(arange(1,86401), name="second")
            df_temp = df_temp.set_index("second").reindex(new_index)
            #print(df_temp)



            # Plot graphs and save to 
            print('\t\t\t Making daily plots') 
            for value in plotvalues:
                df_print = df_temp.dropna(subset=[value])
                #df_print = df_print[df.time_of_day != '-1']
                plot = df_print.plot(x = 'time_of_day', y = value, label= plotvalues[value], figsize=[20,10]);
                #plot = df_temp.dropna(subset=[value]).plot(x = 'time_of_day', y = value, label= plotvalues[value], figsize=[20,10]);
                plot.set_xlabel('Smart meter measurements %s-%s-%s' %(year, month, day))
                plot.set_ylabel(units[value])
                fig = plot.get_figure();


                plotpath = current_directory + '/data/plots/smartmeter/'
                if not os.path.exists(plotpath):
                    os.makedirs(plotpath)
                filename = year+'-'+month+'-'+day+':'+ value +'-'+plotvalues[value]
                fig.savefig(plotpath + filename +'.png')
                plt.clf()
                plt.close('all')

                # Adding value -1 in power to rows with NaN to please matlab program
                df_temp[value].fillna('-1', inplace=True)
                print('Check value change on NaN in value %s' %value)
                #print(df_temp)

                # Save to file with a filename that includes: date, value, household.
                print('\t\t\t Saving to file')

                path = current_directory + '/data/powermundsen_data/smartmeter/' + household + '/' + year + '-' + month + '-' + day
                if not os.path.exists(path):
                    os.makedirs(path)

                if value in filenames:
                    df_temp.to_csv(os.path.join(path, r'%s' %(filenames[value]) + '.csv'), columns=[value], index=True, header=False)



            # Adding the remaining files the add on uses (These have no value since we dont have the data)
            print('Making the empty files...')
            path = current_directory + '/data/powermundsen_data/smartmeter/' + household + '/' + year + '-' + month + '-' + day
            others = ['currentneutral','powerl1', 'powerl2', 'powerl3', 'phaseanglevoltagel2l1', 'phaseanglevoltagel3l1', 'phaseanglecurrentvoltagel1', 'phaseanglecurrentvoltagel2', 'phaseanglecurrentvoltagel3']
            for element in others:
                df_temp[element] = -1
                df_temp.to_csv(os.path.join(path, r'%s' %element +'.csv'), columns=[element], index=True, header=False)

            print('\t\t\t Finished processing day %s ' %day)


print('Finished processing all smart meter data')
