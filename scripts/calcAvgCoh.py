# calculate average coherence of cc image

from osgeo import gdal

import numpy as np
import pandas as pd

import glob
import os
import argparse

def main():
    args = parse_args()
    os.chdir(args.ccDir)

    ccList = glob.glob("*cc.geo.tif")

    ccDf = pd.DataFrame(columns = ['Master', 'Slave', 'Average Coherence'])

    for file in ccList:
        ds = gdal.Open(file)
        array = np.array(ds.GetRasterBand(1).ReadAsArray())
        arrayFilt = array.ravel()
        arrayFilt = arrayFilt[arrayFilt != 0.]
        avgCC = np.average(arrayFilt)
        new_row = {'Master':file[0:4]+'-'+file[4:6]+'-'+file[6:8], 'Slave':file[12:16]+'-'+file[16:18]+'-'+file[18:20], 'Average Coherence':avgCC}
        ccDf = ccDf.append(new_row, ignore_index=True)

        ccDf.to_csv("avgCC.csv", index=False)


    return 


def parse_args():
    parser = argparse.ArgumentParser(description="Average Coherence across cc image and output to list")
    parser.add_argument("--ccDir", type=str, help="Directory Containing Coherence Images", required=True)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
