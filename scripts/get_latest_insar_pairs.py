#!/usr/bin/python3
"""
Volcano InSAR Interpretation Workbench
SPDX-License-Identifier: MIT
Copyright (C) 2021-2024 Government of Canada
Authors:
  - Mandip Sond <mandip.sond@nrcan-rncan.gc.ca>
"""

import os
import botocore.exceptions
import boto3
import yaml

from data_utils import get_config_params


def main():
    '''Main function, retrieve latest potential
    insar pairs files for all site/beam combos'''
    config = get_config_params()
    s_3 = boto3.client('s3')

    with open('app/Data/beamList.yml', encoding="utf-8") as beam_list_yml:
        beam_list = yaml.safe_load(beam_list_yml)
        print(beam_list)
    for site in beam_list:
        for beam in beam_list[site]:
            print(f'Site: {site}, Beam: {beam}')
            if not os.path.exists(f'app/Data/{site}/{beam}'):
                os.makedirs(f'app/Data/{site}/{beam}')
            try:
                filename = f'app/Data/{site}/{beam}/InSAR_Pair_All.csv'
                s_3.download_file(Bucket=config['AWS_BUCKET_NAME'],
                                  Key=f'{site}/{beam}/InSAR_Pair_All.csv',
                                  Filename=filename
                                  )
            except botocore.exceptions.ClientError:
                print('InSAR_Pair_All.csv File not found')


if __name__ == '__main__':
    main()
