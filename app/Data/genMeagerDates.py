import os
import glob
import datetime
import pandas as pd
import numpy as np


os.chdir('/Users/drotheram/Projects/Volcano_InSAR/Meager/5M3/insar/cropped/')

wrapTifs=glob.glob('*wrp.geo.crop.tif')

dates = []

for file in wrapTifs:
    dates.append(int(file.split('_')[0]))
    dates.append(int(file.split('_')[2]))

dates = list(dict.fromkeys(dates))
dates.sort()

startDate = datetime.datetime.strptime(str(dates[0]), '%Y%m%d')

endDate   = datetime.datetime.strptime(str(dates[-1]), '%Y%m%d')

datelist = pd.date_range(start=startDate, end=endDate, freq='4D').tolist()
datelist2 = datelist

c = []

for x in datelist:
    for y in datelist2:
        if x==y:
            print('Same Date')
        else:
            c.append([x,y])

for x in datelist:
    for y in datelist2:
        c.append([x,y])

cDf = pd.DataFrame(c)


coh = []
for i in range(4900):
     coh.append(random.random())

cohDf = pd.DataFrame(coh)

cohDf2 = pd.concat([cDf, cohDf], axis=1)
cohDf2.columns = ['Reference Date', 'Pair Date', 'Coherence']

for index, row in cohDf2.iterrows():
    # print(row['Reference Date'])
    if row['Reference Date']>=row['Pair Date']:
        # row['coherence']=0
        # print(cohDf2.iloc[index])
        cohDf2.loc[index, 'Coherence']=np.nan
    fileName=row['Reference Date'].strftime('%Y%m%d')+'_HH_'+row['Pair Date'].strftime('%Y%m%d')+'_HH.adf.wrp.geo.crop.tif'
    if fileName not in wrapTifs:
        cohDf2.loc[index, 'Coherence']=np.nan


cohDf3= cohDf2[cohDf2['Reference Date']<cohDf2['Pair Date']]

cohDf2.to_csv('/Users/drotheram/GitHub/Volcanic-Interpretation-Workbench/app/Data/coherenceMatrixMeagerCompleteNan.csv', index=False)

cohDf3.to_csv('coherenceMatrixMeager.csv', index=False)
