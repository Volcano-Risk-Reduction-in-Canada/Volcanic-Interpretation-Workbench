#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""

import argparse
import glob
import os
import numpy as np
import pandas as pd

from osgeo import gdal


def main():
    '''Main function, generate average coherence
    matrix from average coherence list'''
    args = parse_args()
    os.chdir(args.ccDir)

    cc_list = glob.glob("*cc.geo.tif")

    cc_df = pd.DataFrame(columns=['Master',
                                  'Slave',
                                  'Average Coherence'])

    for file in cc_list:
        dataset = gdal.Open(file)
        array = np.array(dataset.GetRasterBand(1).ReadAsArray())
        array_filt = array.ravel()
        array_filt = array_filt[array_filt != 0.]
        avg_cc = np.average(array_filt)
        new_row = {'Master': file[0:4]+'-'+file[4:6]+'-'+file[6:8],
                   'Slave': file[12:16]+'-'+file[16:18]+'-'+file[18:20],
                   'Average Coherence': avg_cc}
        cc_df = cc_df.append(new_row, ignore_index=True)

        cc_df.to_csv("avgCC.csv", index=False)
    return cc_df


def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Average Coherence across cc image and output to list")
    parser.add_argument("--ccDir",
                        type=str,
                        help="Directory Containing Coherence Images",
                        required=True)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
