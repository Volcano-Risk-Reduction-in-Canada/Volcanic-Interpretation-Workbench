#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench

SPDX-License-Identifier: MIT

Copyright (C) 2021-2023 Government of Canada

Authors:
  - Drew Rotheram <drew.rotheram-clarke@nrcan-rncan.gc.ca>
"""
import argparse
import datetime
import glob
import os
import pandas as pd


def main():
    '''Main function, generate average coherence
    matrix from average coherence list'''
    args = parse_args()
    os.chdir(args.ccDir)

    wrap_tifs = glob.glob('*wrp.geo.tif')

    dates = []

    for file in wrap_tifs:
        dates.append(int(file.split('_')[0]))
        dates.append(int(file.split('_')[2]))

    dates = list(dict.fromkeys(dates))
    dates.sort()

    start_date = datetime.datetime.strptime(str(dates[0]), '%Y%m%d')
    end_date = datetime.datetime.strptime(str(dates[-1]), '%Y%m%d')

    datelist = pd.date_range(start=start_date,
                             end=end_date,
                             freq='4D').tolist()
    datelist2 = datelist

    coherence_date_list = []
    for first_date in datelist:
        for second_date in datelist2:
            coherence_date_list.append([first_date, second_date])

    coherence_date_list_df = pd.DataFrame(coherence_date_list)
    coherence_date_list_df.columns = ['Reference Date', 'Pair Date']

    coherence_matrix_df = pd.read_csv('avgCC.csv')

    coherence_date_list_df['Reference Date'] = coherence_date_list_df[
        'Reference Date'].dt.strftime('%Y-%m-%d').astype('object')
    coherence_date_list_df['Pair Date'] = coherence_date_list_df[
        'Pair Date'].dt.strftime('%Y-%m-%d').astype('object')
    coh_df_out = pd.merge(coherence_date_list_df,
                          coherence_matrix_df,
                          how='left',
                          left_on=['Reference Date', 'Pair Date'],
                          right_on=['Master', 'Slave'])
    coh_df_out = coh_df_out.drop(columns=['Master', 'Slave'])
    coh_df_out.to_csv('CoherenceMatrix.csv', index=False)
    return


def parse_args():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser(
        description="Average Coherence across cc image and output to list")
    parser.add_argument("--ccDir",
                        type=str,
                        help="Directory Containing Average Coherence csv",
                        required=True)
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
