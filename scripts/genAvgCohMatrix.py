import os
import glob
import datetime
import pandas as pd
import numpy as np
import argparse


def main():
    args = parse_args()
    os.chdir(args.ccDir)

    wrapTifs=glob.glob('*wrp.geo.tif')

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
            c.append([x,y])

    cDf = pd.DataFrame(c)
    cDf.columns = ['Reference Date', 'Pair Date']

    cohDf = pd.read_csv('avgCC.csv')

    cDf['Reference Date']= cDf['Reference Date'].dt.strftime('%Y-%m-%d').astype('object')
    cDf['Pair Date']= cDf['Pair Date'].dt.strftime('%Y-%m-%d').astype('object')
    cohDfOut = pd.merge(cDf, cohDf,  how='left', left_on=['Reference Date', 'Pair Date'], right_on = ['Master', 'Slave'])
    cohDfOut = cohDfOut.drop(columns=['Master', 'Slave'])
    cohDfOut.to_csv('CoherenceMatrix.csv', index=False)
    return 


def parse_args():
    parser = argparse.ArgumentParser(description="Average Coherence across cc image and output to list")
    parser.add_argument("--ccDir", type=str, help="Directory Containing Average Coherence csv", required=True)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()